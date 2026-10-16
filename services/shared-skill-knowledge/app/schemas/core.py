from typing import Annotated, Literal

from pydantic import BaseModel, StringConstraints
from datetime import datetime

SkillType = Literal[
    "PROGRAMMING_LANGUAGE",
    "PROGRAMMING_SKILL",
    "PROGRAMMING_PARADIGM",
    "SOFTWARE_OR_TOOL",
    "KNOWLEDGE",
    "OTHER_SKILL",
]
SkillNature = Literal["TECHNICAL", "BEHAVIOURAL", "OTHER"]

# Trimmed, non-empty strings sized to the database columns
Id50 = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=50)]
Name255 = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=255)]
Status50 = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=50)]

class DomainBase(BaseModel):
    name: Name255
    code: Id50
    description: str | None = None
    status: Status50 = "ACTIVE"

class DomainCreate(DomainBase):
    domain_id: Id50

class DomainOut(DomainBase):
    domain_id: str
    
    class Config:
        from_attributes = True

class SkillBase(BaseModel):
    preferred_name: Name255
    description: str | None = None
    skill_type: SkillType
    skill_nature: SkillNature | None = None
    status: Status50 = "ACTIVE"

class SkillCreate(SkillBase):
    skill_id: Id50

class SkillOut(SkillBase):
    skill_id: str
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

class RoleBase(BaseModel):
    preferred_name: Name255
    description: str | None = None
    status: Status50 = "ACTIVE"

class RoleCreate(RoleBase):
    role_id: Id50

class RoleOut(RoleBase):
    role_id: str
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True
