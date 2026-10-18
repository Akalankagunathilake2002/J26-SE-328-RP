import logging
import uuid
from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_db_session
from app.schemas.analysis import (
    AnalysisCreateRequest,
    AnalysisDetailResponse,
    C04AnalysisResponse,
    PrioritySkillOut,
    SkillResultDetailOut,
)
from app.services.analysis_service import AnalysisService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/analyses", tags=["analyses"])
analysis_service = AnalysisService()

DbSession = Annotated[AsyncSession, Depends(get_db_session)]


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

    # Format priority skills
    priority_skills_out = [
        PrioritySkillOut(
            skillId=ps.skill_id,
            skillName=ps.skill_name,
            priorityRank=ps.priority_rank,
            learningPriority=ps.learning_priority_score,
            gap=ps.gap,
        )
        for ps in analysis.priority_skills
    ]

    c04_payload = analysis.reports[0].report_payload if analysis.reports else None

    return AnalysisDetailResponse(
        analysis_id=analysis.analysis_id,
        user_id=analysis.user_id,
        user_skill_profile_id=analysis.user_skill_profile_id,
        industry_profile_id=analysis.industry_profile_id,
        snapshot_id=analysis.snapshot_id,
        matching_method=analysis.matching_method,
        scoring_config_version=analysis.scoring_config_version,
        readiness_score=analysis.readiness_score,
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

    if analysis.reports:
        return analysis.reports[0].report_payload

    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="No C04 report payload found for this completed analysis",
    )
