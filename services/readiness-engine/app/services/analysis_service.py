import uuid
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import func, or_, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.algorithms import (
    MatchingMethod,
    MatchingPolicy,
    RequirementInput,
    StudentSkillInput,
    calculate_learning_priorities,
    calculate_skill_gaps,
    format_c04_payload,
    match_skills,
    score_readiness,
)
from app.models.analysis import (
    Analysis,
    AnalysisPrioritySkill,
    AnalysisReport,
    AnalysisSkillResult,
    AnalysisStatus,
)
from app.models.profiles import IndustryProfile
from app.schemas.analysis import AnalysisCreateRequest
from app.schemas.profile_validation import (
    validate_industry_profile,
    validate_user_skill_profile,
)
from app.schemas.report import AnalysisReportResponse
from app.services.explanation_service import build_analysis_explanation_report
from app.services.profile_loader import (
    load_snapshot_knowledge,
    resolve_industry_profile,
    resolve_snapshot,
    resolve_user_profile,
)


class AnalysisService:
    # Orchestrate the complete C03 Career Readiness Analysis Pipeline
    async def run_analysis(
        self,
        session: AsyncSession,
        request: AnalysisCreateRequest,
    ) -> tuple[Analysis, dict[str, Any]]:
        # 1. Resolve student and industry profiles directly from PostgreSQL database
        user_profile = await resolve_user_profile(
            session=session,
            profile_id=request.user_skill_profile_id,
            user_id=request.user_id,
            allow_fixture_fallback=False,
        )
        industry_profile = await resolve_industry_profile(
            session=session,
            profile_id=request.industry_profile_id,
            role_id=request.role_id,
            allow_fixture_fallback=False,
        )

        # 2. Resolve knowledge snapshot and matching knowledge directly from PostgreSQL
        snapshot = await resolve_snapshot(
            session=session,
            snapshot_id=request.snapshot_id,
            allow_fixture_fallback=False,
        )
        aliases, relationships = await load_snapshot_knowledge(
            session=session,
            snapshot_id=snapshot.snapshot_id,
        )

        # 3. Create persistent analysis record in PENDING status
        analysis_id = uuid.uuid4()
        start_time = datetime.now(UTC)
        analysis = Analysis(
            analysis_id=analysis_id,
            user_id=user_profile.user_id,
            user_skill_profile_id=user_profile.id,
            industry_profile_id=industry_profile.id,
            snapshot_id=snapshot.snapshot_id,
            matching_method=request.matching_method,
            scoring_config_version=request.scoring_config_version,
            status=AnalysisStatus.PENDING.value,
            started_at=start_time,
        )
        session.add(analysis)
        await session.commit()

        try:
            # Transition status to RUNNING as pipeline execution begins
            await session.execute(
                update(Analysis)
                .where(Analysis.analysis_id == analysis_id)
                .values(status=AnalysisStatus.RUNNING.value)
            )
            await session.commit()
            analysis.status = AnalysisStatus.RUNNING.value

            # 4. Validate industry and student skill profiles before algorithm execution
            validate_industry_profile(industry_profile)
            validate_user_skill_profile(user_profile)

            # 5. Prepare algorithm inputs
            method_key = request.matching_method.upper()
            if method_key not in MatchingMethod.__members__:
                raise ValueError(
                    f"Unsupported matching method: '{request.matching_method}'"
                )
            policy = MatchingPolicy(
                method=MatchingMethod[method_key],
                version=request.scoring_config_version,
            )

            req_inputs = [
                RequirementInput(
                    requirement_id=r.id,
                    skill_id=r.skill_id,
                    standard_name=r.standard_name,
                    mapping_status=r.mapping_status,
                    required_proficiency=r.required_proficiency_level,
                    demand_weight=r.demand_weight,
                )
                for r in industry_profile.requirements
            ]

            stu_inputs = [
                StudentSkillInput(
                    skill_record_id=s.id,
                    skill_id=s.skill_id,
                    standard_name=s.standard_name,
                    primary_observed_term=s.primary_observed_term,
                    observed_terms=list(s.observed_terms or []),
                    mapping_status=s.mapping_status,
                    proficiency_level=s.proficiency_level,
                )
                for s in user_profile.skills
            ]

            # Step 1: Matching
            matching_results = match_skills(
                req_inputs,
                stu_inputs,
                aliases=aliases,
                relationships=relationships,
                policy=policy,
            )
            matching_by_req_id = {
                str(m.industry_requirement_id): m for m in matching_results
            }
            student_skill_by_id = {str(s.id): s for s in user_profile.skills}

            # Step 2: Readiness Scoring
            req_scoring_data = [
                {
                    "id": r.id,
                    "demand_weight": r.demand_weight,
                    "required_proficiency": r.required_proficiency_score,
                    "skill_id": r.skill_id,
                    "standard_name": r.standard_name,
                    "mapping_status": r.mapping_status,
                }
                for r in industry_profile.requirements
            ]
            stu_scoring_data = [
                {
                    "id": s.id,
                    "student_proficiency": s.proficiency_score,
                    "evidence_confidence": s.evidence_confidence,
                }
                for s in user_profile.skills
            ]

            overall_readiness = score_readiness(
                requirements=req_scoring_data,
                matching_results=matching_results,
                student_skills=stu_scoring_data,
                matching_method=request.matching_method,
                scoring_version=request.scoring_config_version,
            )

            # Step 3: Skill Gaps
            skill_gaps = calculate_skill_gaps(overall_readiness.requirement_results)
            gaps_by_req_id = {str(g.industry_requirement_id): g for g in skill_gaps}
            readiness_by_req_id = {
                str(r.industry_requirement_id): r
                for r in overall_readiness.requirement_results
            }

            # Step 4: Learning Priorities
            priorities = calculate_learning_priorities(
                skill_gaps, include_covered=False
            )

            # Step 5: C04 Payload Assembly
            role_title = (
                industry_profile.primary_observed_title
                or industry_profile.role_name
                or "Target Industry Role"
            )
            resolved_role_id = (
                industry_profile.role_id
                or industry_profile.candidate_role_id
                or str(industry_profile.id)
            )
            c04_payload = format_c04_payload(
                priority_skills=priorities,
                role_name=role_title,
                readiness_score=overall_readiness.overall_readiness,
                analysis_id=analysis.analysis_id,
                user_id=user_profile.user_id,
                role_id=resolved_role_id,
            )

            # Step 6: Atomic Persistence of Detailed Results
            for req in industry_profile.requirements:
                req_str_id = str(req.id)
                match_res = matching_by_req_id.get(req_str_id)
                gap_res = gaps_by_req_id.get(req_str_id)
                readiness_item = readiness_by_req_id.get(req_str_id)

                matched_stu_id = None
                matched_stu_name = None
                matched_stu_prof = None

                if match_res and match_res.selected_student_skill_id:
                    matched_stu = student_skill_by_id.get(
                        str(match_res.selected_student_skill_id)
                    )
                    if matched_stu:
                        matched_stu_id = matched_stu.id
                        matched_stu_name = matched_stu.standard_name
                        matched_stu_prof = matched_stu.proficiency_level

                skill_result = AnalysisSkillResult(
                    id=uuid.uuid4(),
                    analysis_id=analysis.analysis_id,
                    industry_requirement_id=req.id,
                    user_skill_profile_skill_id=matched_stu_id,
                    required_skill_name=req.standard_name,
                    matched_skill_name=matched_stu_name,
                    match_type=match_res.match_type if match_res else "MISSING",
                    relationship_id=(
                        match_res.selected_relationship_id if match_res else None
                    ),
                    coverage_credit=match_res.coverage_credit if match_res else 0.0,
                    required_proficiency=req.required_proficiency_level,
                    user_proficiency=matched_stu_prof,
                    evidence_confidence=(
                        readiness_item.evidence_confidence if readiness_item else None
                    ),
                    industry_weight=req.demand_weight,
                    satisfaction=(
                        readiness_item.readiness_satisfaction if readiness_item else 0.0
                    ),
                    gap=gap_res.capability_gap if gap_res else None,
                    result_status=gap_res.gap_classification if gap_res else "MISSING",
                )
                session.add(skill_result)

            for p in priorities:
                priority_entry = AnalysisPrioritySkill(
                    id=uuid.uuid4(),
                    analysis_id=analysis.analysis_id,
                    skill_id=p.required_canonical_skill_id,
                    skill_name=p.required_skill_name,
                    priority_rank=p.priority_rank,
                    learning_priority_score=p.learning_priority,
                    gap=p.capability_gap,
                    required_proficiency=str(p.required_proficiency),
                    user_proficiency=(
                        str(p.student_proficiency)
                        if p.student_proficiency is not None
                        else None
                    ),
                )
                session.add(priority_entry)

            report = AnalysisReport(
                id=uuid.uuid4(),
                analysis_id=analysis.analysis_id,
                report_version="1.0",
                report_payload=c04_payload,
                generation_method=request.matching_method,
                status="READY",
            )
            session.add(report)

            # Complete analysis record atomically with child results and report
            complete_time = datetime.now(UTC)
            await session.execute(
                update(Analysis)
                .where(Analysis.analysis_id == analysis_id)
                .values(
                    readiness_score=overall_readiness.overall_readiness,
                    status=AnalysisStatus.COMPLETED.value,
                    completed_at=complete_time,
                )
            )
            await session.commit()

            analysis.readiness_score = overall_readiness.overall_readiness
            analysis.status = AnalysisStatus.COMPLETED.value
            analysis.completed_at = complete_time
            return analysis, c04_payload

        except Exception as exc:
            # Atomic rollback of all uncommitted child rows and operations
            await session.rollback()
            failed_time = datetime.now(UTC)
            clean_error = str(exc)
            await session.execute(
                update(Analysis)
                .where(Analysis.analysis_id == analysis_id)
                .values(
                    status=AnalysisStatus.FAILED.value,
                    error_message=clean_error,
                    completed_at=failed_time,
                )
            )
            await session.commit()
            analysis.status = AnalysisStatus.FAILED.value
            analysis.error_message = clean_error
            analysis.completed_at = failed_time
            raise

    # Retrieve analysis record along with its child results and reports
    async def get_analysis_by_id(
        self,
        session: AsyncSession,
        analysis_id: uuid.UUID,
    ) -> Analysis | None:
        stmt = (
            select(Analysis)
            .options(
                selectinload(Analysis.skill_results),
                selectinload(Analysis.priority_skills),
                selectinload(Analysis.reports),
                selectinload(Analysis.industry_profile),
            )
            .where(Analysis.analysis_id == analysis_id)
        )
        res = await session.execute(stmt)
        return res.scalars().first()

    # Retrieve paginated history of analyses with deterministic sorting and optional filters
    async def list_analyses(
        self,
        session: AsyncSession,
        user_id: uuid.UUID | None = None,
        status: str | None = None,
        role_id: str | None = None,
        limit: int = 20,
        offset: int = 0,
    ) -> tuple[list[Analysis], int]:
        filter_conditions = []
        if user_id is not None:
            filter_conditions.append(Analysis.user_id == user_id)
        if status is not None:
            filter_conditions.append(Analysis.status == status.strip().upper())

        # Count total matching records
        count_stmt = select(func.count(Analysis.analysis_id))
        if role_id is not None:
            count_stmt = count_stmt.join(Analysis.industry_profile).where(
                or_(
                    IndustryProfile.role_id == role_id,
                    IndustryProfile.candidate_role_id == role_id,
                )
            )
        if filter_conditions:
            count_stmt = count_stmt.where(*filter_conditions)

        total_res = await session.execute(count_stmt)
        total = total_res.scalar_one()

        # Query paginated analysis records with joined industry profile metadata
        items_stmt = select(Analysis).options(selectinload(Analysis.industry_profile))
        if role_id is not None:
            items_stmt = items_stmt.join(Analysis.industry_profile).where(
                or_(
                    IndustryProfile.role_id == role_id,
                    IndustryProfile.candidate_role_id == role_id,
                )
            )
        if filter_conditions:
            items_stmt = items_stmt.where(*filter_conditions)

        items_stmt = (
            items_stmt.order_by(Analysis.started_at.desc(), Analysis.analysis_id.desc())
            .offset(offset)
            .limit(limit)
        )
        records_res = await session.execute(items_stmt)
        records = list(records_res.scalars().all())

        return records, total

    # Retrieve or generate deterministic explanation report for completed analysis
    async def get_or_generate_explanation_report(
        self,
        session: AsyncSession,
        analysis_id: uuid.UUID,
    ) -> tuple[Analysis | None, AnalysisReportResponse | None]:
        analysis = await self.get_analysis_by_id(session, analysis_id)
        if analysis is None:
            return None, None

        if analysis.status != AnalysisStatus.COMPLETED.value:
            return analysis, None

        # Check if explanation report was already persisted
        for rep in analysis.reports:
            if rep.report_version == "explanation_v1.0":
                return analysis, AnalysisReportResponse.model_validate(
                    rep.report_payload
                )

        # Generate deterministic report from persisted results
        report_response = build_analysis_explanation_report(analysis)

        # Persist report to avoid duplicate generation on repeated requests
        new_report = AnalysisReport(
            id=uuid.uuid4(),
            analysis_id=analysis.analysis_id,
            report_version="explanation_v1.0",
            report_payload=report_response.model_dump(mode="json"),
            generation_method="DETERMINISTIC_TEMPLATES",
            status="READY",
        )
        session.add(new_report)
        await session.commit()
        analysis.reports.append(new_report)

        return analysis, report_response
