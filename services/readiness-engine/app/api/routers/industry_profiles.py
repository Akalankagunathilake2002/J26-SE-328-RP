import logging
import uuid
from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_db_session
from app.models.profiles import IndustryProfile
from app.schemas.profiles import IndustryProfileListItem
from app.services.profile_loader import (
    get_industry_profile_by_id,
    list_industry_profiles,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/industry-profiles", tags=["industry-profiles"])

DbSession = Annotated[AsyncSession, Depends(get_db_session)]


# Convert an IndustryProfile ORM instance to the API response schema
def _to_list_item(profile: IndustryProfile) -> IndustryProfileListItem:
    return IndustryProfileListItem(
        industry_profile_id=profile.id,
        id=profile.id,
        role_id=profile.role_id or profile.candidate_role_id,
        role_name=profile.role_name or profile.primary_observed_title,
        career_level=profile.career_level,
        domain_id=profile.domain_id,
        domain_name=profile.domain_name,
        domain=profile.domain_name or profile.domain_id,
        primary_observed_title=profile.primary_observed_title,
        profile_version=profile.profile_version,
        profile_status=profile.profile_status,
    )


# List available industry profiles for role selection and analysis targeting
@router.get(
    "",
    response_model=list[IndustryProfileListItem],
    summary="List available industry profiles",
    description="Retrieve available industry profiles with role IDs, names, career levels, and domains",
)
async def get_industry_profiles(
    session: DbSession,
    domain_id: Annotated[
        str | None,
        Query(description="Filter profiles by domain ID (e.g., DOM-IT)"),
    ] = None,
    career_level: Annotated[
        str | None,
        Query(description="Filter profiles by career level (e.g., INTERNSHIP, JUNIOR)"),
    ] = None,
    status_filter: Annotated[
        str | None,
        Query(alias="status", description="Filter profiles by status (e.g., active)"),
    ] = "active",
    latest_only: Annotated[
        bool,
        Query(description="Return only the latest version per role and career level"),
    ] = True,
) -> Any:
    profiles = await list_industry_profiles(
        session=session,
        domain_id=domain_id,
        career_level=career_level,
        status=status_filter,
        latest_only=latest_only,
    )
    return [_to_list_item(p) for p in profiles]


# Retrieve a single industry profile by unique UUID
@router.get(
    "/{industry_profile_id}",
    response_model=IndustryProfileListItem,
    summary="Get industry profile by ID",
    description="Retrieve a single industry profile by its unique UUID",
)
async def get_industry_profile(
    industry_profile_id: uuid.UUID,
    session: DbSession,
) -> Any:
    profile = await get_industry_profile_by_id(session, industry_profile_id)
    if profile is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Industry profile with ID '{industry_profile_id}' not found",
        )
    return _to_list_item(profile)
