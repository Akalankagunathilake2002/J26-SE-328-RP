from pydantic import BaseModel, Field
from datetime import datetime

class DomainBase(BaseModel):
    name: str
    code: str
    description: str | None = None
    status: str = "ACTIVE"

class DomainCreate(DomainBase):
    domain_id: str

class DomainOut(DomainBase):
    domain_id: str
    
    class Config:
        from_attributes = True

class SkillBase(BaseModel):
    preferred_name: str
    description: str | None = None
    skill_type: str
    status: str = "ACTIVE"

class SkillCreate(SkillBase):
    skill_id: str

class SkillOut(SkillBase):
    skill_id: str
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

class RoleBase(BaseModel):
    preferred_name: str
    description: str | None = None
    status: str = "ACTIVE"

class RoleCreate(RoleBase):
    role_id: str

class RoleOut(RoleBase):
    role_id: str
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True
