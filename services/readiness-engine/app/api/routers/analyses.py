import logging
import uuid
from typing import Annotated, Any

from fastapi import APIRouter, Depends, Header, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_db_session
from app.schemas.analysis import (
    AnalysisCreateRequest,
    AnalysisDetailResponse,
    AnalysisHistoryItem,
    AnalysisHistoryResponse,
    C04AnalysisResponse,
    PrioritySkillOut,
    SkillResultDetailOut,
)
from app.schemas.report import AnalysisReportResponse
from app.services.analysis_service import AnalysisService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/analyses", tags=["analyses"])
analysis_service = AnalysisService()

DbSession = Annotated[AsyncSession, Depends(get_db_session)]


# List analysis history with pagination, deterministic ordering, and optional filters
@router.get(
    "",
    response_model=AnalysisHistoryResponse,
    summary="List analysis history",
)
async def list_analyses(
    session: DbSession,
    user_id: Annotated[
        uuid.UUID | None,
        Query(description="Filter analyses by student user UUID"),
    ] = None,
    x_user_id: Annotated[
        uuid.UUID | None,
        Header(alias="X-User-Id", description="Authenticated student user UUID"),
    ] = None,
    status: Annotated[
        str | None,
        Query(description="Filter by status: PENDING, RUNNING, COMPLETED, or FAILED"),
    ] = None,
    role_id: Annotated[
        str | None,
        Query(description="Filter by canonical or candidate role identifier"),
    ] = None,
    limit: Annotated[
        int,
        Query(ge=1, le=100, description="Maximum number of records to return (1-100)"),
    ] = 20,
    offset: Annotated[
        int,
        Query(ge=0, description="Number of initial records to skip (>= 0)"),
    ] = 0,
) -> Any:
    effective_user_id = user_id or x_user_id
    records, total = await analysis_service.list_analyses(
        session=session,
        user_id=effective_user_id,
        status=status,
        role_id=role_id,
        limit=limit,
        offset=offset,
    )

    items = []
    for a in records:
        ind_prof = a.industry_profile
        role_id_val = (
            (ind_prof.role_id or ind_prof.candidate_role_id or str(ind_prof.id))
            if ind_prof
            else str(a.industry_profile_id)
        )
        role_name_val = (
            (ind_prof.primary_observed_title or ind_prof.role_name)
            if ind_prof
            else None
        )
        items.append(
            AnalysisHistoryItem(
                analysisId=str(a.analysis_id),
                user_id=str(a.user_id),
                roleId=role_id_val,
                roleName=role_name_val,
                readinessScore=a.readiness_score,
                status=a.status,
                createdAt=a.started_at,
                completedAt=a.completed_at,
            )
        )

    return AnalysisHistoryResponse(
        items=items,
        total=total,
        limit=limit,
        offset=offset,
    )


# Execute complete analysis pipeline and return C04 target payload
@router.post(
    "",
    response_model=C04AnalysisResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Initiate career readiness analysis",
)
async def create_analysis(
    request: AnalysisCreateRequest,
    session: DbSession,
) -> Any:
    try:
        _analysis, c04_payload = await analysis_service.run_analysis(
            session=session,
            request=request,
        )
        return c04_payload
    except ValueError as val_err:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(val_err),
        ) from val_err
    except Exception as exc:
        logger.exception("Unexpected error in analysis execution")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Analysis execution failed due to an unexpected internal error.",
        ) from exc


# Retrieve full analysis details and per-requirement scoring results
@router.get(
    "/{analysis_id}",
    response_model=AnalysisDetailResponse,
    summary="Get analysis execution details",
)
async def get_analysis(
    analysis_id: uuid.UUID,
    session: DbSession,
) -> Any:
    analysis = await analysis_service.get_analysis_by_id(session, analysis_id)
    if analysis is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Analysis with ID '{analysis_id}' not found",
        )

    # Format per-skill results
    skill_results_out = [
        SkillResultDetailOut(
            id=sr.id,
            industry_requirement_id=sr.industry_requirement_id,
            required_skill_name=sr.required_skill_name,
            matched_skill_name=sr.matched_skill_name,
            match_type=sr.match_type,
            relationship_id=sr.relationship_id,
            coverage_credit=sr.coverage_credit,
            required_proficiency=sr.required_proficiency,
            user_proficiency=sr.user_proficiency,
            evidence_confidence=sr.evidence_confidence,
            industry_weight=sr.industry_weight,
            satisfaction=sr.satisfaction,
            gap=sr.gap,
            result_status=sr.result_status,
        )
        for sr in analysis.skill_results
    ]

    # Format priority skills ordered by sequential rank
    priority_skills_out = [
        PrioritySkillOut(
            skillId=ps.skill_id,
            skillName=ps.skill_name,
            priorityRank=ps.priority_rank,
            learningPriority=ps.learning_priority_score,
            gap=ps.gap,
        )
        for ps in sorted(analysis.priority_skills, key=lambda p: p.priority_rank)
    ]

    c04_payload = next(
        (r.report_payload for r in analysis.reports if r.report_version == "1.0"),
        analysis.reports[0].report_payload if analysis.reports else None,
    )

    baseline_payload = next(
        (
            r.report_payload
            for r in analysis.reports
            if r.report_version == "exact_baseline_v1.0"
        ),
        None,
    )
    baseline_score = (
        baseline_payload.get("readinessScore")
        if baseline_payload
        else (c04_payload.get("baselineReadinessScore") if c04_payload else None)
    )

    return AnalysisDetailResponse(
        analysis_id=analysis.analysis_id,
        user_id=analysis.user_id,
        user_skill_profile_id=analysis.user_skill_profile_id,
        industry_profile_id=analysis.industry_profile_id,
        snapshot_id=analysis.snapshot_id,
        matching_method=analysis.matching_method,
        scoring_config_version=analysis.scoring_config_version,
        readiness_score=analysis.readiness_score,
        baseline_readiness_score=baseline_score,
        status=analysis.status,
        started_at=analysis.started_at,
        completed_at=analysis.completed_at,
        error_message=analysis.error_message,
        skill_results=skill_results_out,
        priority_skills=priority_skills_out,
        c04_payload=c04_payload,
    )


# Retrieve external C04 payload for downstream consumption
@router.get(
    "/{analysis_id}/c04",
    response_model=C04AnalysisResponse,
    summary="Get downstream C04 payload",
)
async def get_analysis_c04(
    analysis_id: uuid.UUID,
    session: DbSession,
) -> Any:
    analysis = await analysis_service.get_analysis_by_id(session, analysis_id)
    if analysis is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Analysis with ID '{analysis_id}' not found",
        )

    if analysis.status != "COMPLETED":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Analysis has not completed successfully (current status: {analysis.status})",
        )

    c04_report = next(
        (r for r in analysis.reports if r.report_version == "1.0"),
        analysis.reports[0] if analysis.reports else None,
    )
    if c04_report:
        return c04_report.report_payload

    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="No C04 report payload found for this completed analysis",
    )


# Retrieve deterministic explanation report for completed analysis
@router.get(
    "/{analysis_id}/report",
    response_model=AnalysisReportResponse,
    summary="Get analysis explanation report",
)
async def get_analysis_report(
    analysis_id: uuid.UUID,
    session: DbSession,
) -> Any:
    analysis = await analysis_service.get_analysis_by_id(session, analysis_id)
    if analysis is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Analysis with ID '{analysis_id}' not found",
        )

    if analysis.status != "COMPLETED":
        err_suffix = (
            f". Error: {analysis.error_message}" if analysis.error_message else ""
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Analysis has not completed successfully (current status: {analysis.status}){err_suffix}",
        )

    (
        _analysis,
        report_response,
    ) = await analysis_service.get_or_generate_explanation_report(session, analysis_id)
    if report_response is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate explanation report for completed analysis",
        )

    return report_response
