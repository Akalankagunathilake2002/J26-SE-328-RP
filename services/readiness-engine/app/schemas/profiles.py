import uuid

from pydantic import BaseModel, ConfigDict, Field


# Read-only schema representing an industry role profile for selection and evaluation
class IndustryProfileListItem(BaseModel):
    industry_profile_id: uuid.UUID = Field(
        ..., description="Unique ID of the saved industry profile"
    )
    id: uuid.UUID | None = Field(
        None, description="Alias matching industry_profile_id"
    )
    role_id: str | None = Field(
        None, description="Canonical or candidate role identifier from SSKS/C01"
    )
    role_name: str = Field(
        ..., description="The current role name stored in the industry profile"
    )
    career_level: str | None = Field(
        None, description="Career-level classification (e.g., INTERNSHIP, JUNIOR)"
    )
    domain_id: str | None = Field(
        None, description="Domain identifier (e.g., DOM-IT)"
    )
    domain_name: str | None = Field(
        None, description="Domain name (e.g., Information Technology)"
    )
    domain: str | None = Field(
        None, description="Domain category summary"
    )
    primary_observed_title: str | None = Field(
        None, description="Original observed job title from industry postings"
    )
    profile_version: str | None = Field(
        None, description="Profile version timestamp"
    )
    profile_status: str | None = Field(
        None, description="Status of the industry profile (e.g., active)"
    )

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)
