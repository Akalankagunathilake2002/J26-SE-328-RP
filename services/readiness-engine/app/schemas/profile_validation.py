import math
import re
import uuid
from typing import Any

from pydantic import (
    AliasChoices,
    BaseModel,
    ConfigDict,
    Field,
    ValidationError,
    model_validator,
)

CANONICAL_SKILL_ID_REGEX = re.compile(r"^SK-\d{6}$")
CANONICAL_ROLE_ID_REGEX = re.compile(r"^RL-\d{6}$")

# Authoritative mapping statuses: canonical assessable entities vs unassessed candidate/raw terms
CANONICAL_MAPPING_STATUSES = {"verified", "resolved", "canonical"}
UNASSESSED_MAPPING_STATUSES = {"unresolved", "unmapped", "candidate", "provisional"}
VALID_MAPPING_STATUSES = CANONICAL_MAPPING_STATUSES | UNASSESSED_MAPPING_STATUSES


# Specific validation error identifying affected profile, field, and constraint
class ProfileValidationError(ValueError):
    def __init__(
        self,
        message: str,
        profile_type: str | None = None,
        field: str | None = None,
        identifier: str | None = None,
    ):
        super().__init__(message)
        self.profile_type = profile_type
        self.field = field
        self.identifier = identifier


# Helper to check if a numeric value is finite and valid
def _check_finite_number(
    val: Any,
    field_name: str,
    profile_type: str,
    context: str,
) -> float:
    if val is None:
        raise ProfileValidationError(
            f"[{profile_type}] {context}: field '{field_name}' is required and cannot be null",
            profile_type=profile_type,
            field=field_name,
        )
    if isinstance(val, bool) or not isinstance(val, (int, float)):
        raise ProfileValidationError(
            f"[{profile_type}] {context}: field '{field_name}' must be numeric, got {type(val).__name__}",
            profile_type=profile_type,
            field=field_name,
        )
    float_val = float(val)
    if math.isnan(float_val) or math.isinf(float_val):
        raise ProfileValidationError(
            f"[{profile_type}] {context}: field '{field_name}' must be finite, got {float_val}",
            profile_type=profile_type,
            field=field_name,
        )
    return float_val


# Pydantic schema for validating C01 industry role requirements
class IndustryRequirementInput(BaseModel):
    skill_id: str | None = Field(
        None,
        validation_alias=AliasChoices("skill_id", "skillId"),
    )
    candidate_skill_id: str | None = Field(
        None,
        validation_alias=AliasChoices("candidate_skill_id", "candidateSkillId"),
    )
    standard_name: str
    primary_observed_term: str | None = None
    observed_terms: list[str] = Field(default_factory=list)
    mapping_status: str = "verified"
    skill_type: str = Field(
        "TECHNICAL",
        validation_alias=AliasChoices("skill_type", "skillType"),
    )
    required_proficiency_level: str = Field(
        "INTERMEDIATE",
        validation_alias=AliasChoices(
            "required_proficiency_level", "requiredProficiencyLevel"
        ),
    )
    required_proficiency_score: float = Field(
        ...,
        validation_alias=AliasChoices(
            "required_proficiency_score", "requiredProficiencyScore"
        ),
    )
    demand_weight: float = Field(
        ...,
        validation_alias=AliasChoices("demand_weight", "DemandWeight", "demandWeight"),
    )

    model_config = ConfigDict(populate_by_name=True)

    # Extract nested fields and validate requirement rules before instantiation
    @model_validator(mode="before")
    @classmethod
    def extract_nested_and_validate(cls, data: Any) -> Any:
        if not isinstance(data, dict):
            return data

        # Extract nested required_proficiency object if flat score not provided
        if (
            "required_proficiency_score" not in data
            and "requiredProficiencyScore" not in data
        ):
            req_prof = data.get("required_proficiency") or data.get(
                "requiredProficiency"
            )
            if isinstance(req_prof, dict):
                if "score" in req_prof:
                    data["required_proficiency_score"] = req_prof["score"]
                if "level" in req_prof and "required_proficiency_level" not in data:
                    data["required_proficiency_level"] = req_prof["level"]

        # Validate mapping status
        raw_status = data.get("mapping_status", "verified")
        if (
            not isinstance(raw_status, str)
            or raw_status.lower() not in VALID_MAPPING_STATUSES
        ):
            std_name = data.get("standard_name", "unknown")
            raise ProfileValidationError(
                f"[IndustryProfile] requirement '{std_name}': invalid mapping_status '{raw_status}'",
                profile_type="industry_profile",
                field="mapping_status",
            )
        data["mapping_status"] = raw_status.lower()

        # Validate canonical skill_id
        skill_id = data.get("skill_id") or data.get("skillId")
        std_name = data.get("standard_name", "unknown")
        if data["mapping_status"] in CANONICAL_MAPPING_STATUSES:
            if not skill_id or not isinstance(skill_id, str):
                raise ProfileValidationError(
                    f"[IndustryProfile] requirement '{std_name}': mapping_status is '{raw_status}' but canonical skill_id is missing",
                    profile_type="industry_profile",
                    field="skill_id",
                )
            if not CANONICAL_SKILL_ID_REGEX.match(skill_id):
                raise ProfileValidationError(
                    f"[IndustryProfile] requirement '{std_name}': invalid canonical skill_id '{skill_id}' (must match SK-XXXXXX)",
                    profile_type="industry_profile",
                    field="skill_id",
                )
        elif skill_id and not CANONICAL_SKILL_ID_REGEX.match(skill_id):
            raise ProfileValidationError(
                f"[IndustryProfile] requirement '{std_name}': invalid canonical skill_id '{skill_id}' (must match SK-XXXXXX)",
                profile_type="industry_profile",
                field="skill_id",
            )

        # Validate demand_weight: must be finite and >= 0.0
        weight_raw = (
            data.get("demand_weight")
            if "demand_weight" in data
            else data.get("DemandWeight", data.get("demandWeight"))
        )
        weight = _check_finite_number(
            weight_raw, "demand_weight", "IndustryProfile", f"requirement '{std_name}'"
        )
        if weight < 0.0:
            raise ProfileValidationError(
                f"[IndustryProfile] requirement '{std_name}': demand_weight {weight} cannot be negative",
                profile_type="industry_profile",
                field="demand_weight",
            )
        data["demand_weight"] = weight

        # Validate required_proficiency_score: scoring formulas divide by it, so it must be strictly > 0.0 and <= 1.0
        score_raw = (
            data.get("required_proficiency_score")
            if "required_proficiency_score" in data
            else data.get("requiredProficiencyScore")
        )
        score = _check_finite_number(
            score_raw,
            "required_proficiency_score",
            "IndustryProfile",
            f"requirement '{std_name}'",
        )
        if score <= 0.0 or score > 1.0:
            raise ProfileValidationError(
                f"[IndustryProfile] requirement '{std_name}': required_proficiency_score {score} must be strictly > 0.0 and <= 1.0",
                profile_type="industry_profile",
                field="required_proficiency_score",
            )
        data["required_proficiency_score"] = score

        return data


# Pydantic schema for validating C01 industry role profiles
class IndustryProfileInput(BaseModel):
    role_id: str | None = Field(
        None,
        validation_alias=AliasChoices("role_id", "roleId"),
    )
    candidate_role_id: str | None = Field(
        None,
        validation_alias=AliasChoices(
            "candidate_role_id", "candidate_roleId", "candidateRoleId"
        ),
    )
    primary_observed_title: str
    observed_titles: list[str] = Field(default_factory=list)
    mapping_status: str = "verified"
    career_level: str = Field(
        "ENTRY_LEVEL",
        validation_alias=AliasChoices("career_level", "careerLevel"),
    )
    profile_version: str = Field(
        ...,
        validation_alias=AliasChoices("profile_version", "profileVersion"),
    )
    requirements: list[IndustryRequirementInput] = Field(..., min_length=1)

    model_config = ConfigDict(populate_by_name=True)

    # Validate role identifiers, mapping status, and duplicate requirements
    @model_validator(mode="before")
    @classmethod
    def validate_role_profile(cls, data: Any) -> Any:
        if not isinstance(data, dict):
            return data

        raw_status = data.get("mapping_status", "verified")
        if (
            not isinstance(raw_status, str)
            or raw_status.lower() not in VALID_MAPPING_STATUSES
        ):
            raise ProfileValidationError(
                f"[IndustryProfile]: invalid role mapping_status '{raw_status}'",
                profile_type="industry_profile",
                field="mapping_status",
            )
        data["mapping_status"] = raw_status.lower()

        role_id = data.get("role_id") or data.get("roleId")
        candidate_id = (
            data.get("candidate_role_id")
            or data.get("candidate_roleId")
            or data.get("candidateRoleId")
        )
        if not role_id and not candidate_id and not data.get("primary_observed_title"):
            raise ProfileValidationError(
                "[IndustryProfile]: profile must contain a role_id, candidate_role_id, or primary_observed_title",
                profile_type="industry_profile",
                field="role_id",
            )

        if data["mapping_status"] in CANONICAL_MAPPING_STATUSES:
            if not role_id or not isinstance(role_id, str):
                raise ProfileValidationError(
                    f"[IndustryProfile]: mapping_status is '{raw_status}' but canonical role_id is missing",
                    profile_type="industry_profile",
                    field="role_id",
                )
            if not CANONICAL_ROLE_ID_REGEX.match(role_id):
                raise ProfileValidationError(
                    f"[IndustryProfile]: invalid canonical role_id '{role_id}' (must match RL-XXXXXX)",
                    profile_type="industry_profile",
                    field="role_id",
                )
        elif role_id and not CANONICAL_ROLE_ID_REGEX.match(role_id):
            raise ProfileValidationError(
                f"[IndustryProfile]: invalid role_id '{role_id}' (must match RL-XXXXXX)",
                profile_type="industry_profile",
                field="role_id",
            )

        # Validate requirements list structure and absence of duplicates
        reqs = data.get("requirements")
        if not isinstance(reqs, list) or len(reqs) == 0:
            raise ProfileValidationError(
                "[IndustryProfile]: requirements must be a non-empty list",
                profile_type="industry_profile",
                field="requirements",
            )

        seen_skills = set()
        for r in reqs:
            if not isinstance(r, dict):
                continue
            s_id = r.get("skill_id") or r.get("skillId")
            if s_id:
                if s_id in seen_skills:
                    raise ProfileValidationError(
                        f"[IndustryProfile]: duplicate requirement for canonical skill_id '{s_id}'",
                        profile_type="industry_profile",
                        field="requirements",
                    )
                seen_skills.add(s_id)

        return data


# Pydantic schema for validating C02 student skill items
class UserSkillInput(BaseModel):
    skill_id: str | None = Field(
        None,
        validation_alias=AliasChoices("skill_id", "skillId"),
    )
    candidate_skill_id: str | None = Field(
        None,
        validation_alias=AliasChoices("candidate_skill_id", "candidateSkillId"),
    )
    standard_name: str
    primary_observed_term: str | None = None
    observed_terms: list[str] = Field(default_factory=list)
    mapping_status: str = "verified"
    skill_type: str = Field(
        "TECHNICAL",
        validation_alias=AliasChoices("skill_type", "skillType"),
    )
    proficiency_level: str = Field(
        "INTERMEDIATE",
        validation_alias=AliasChoices("proficiency_level", "proficiencyLevel"),
    )
    proficiency_score: float = Field(
        ...,
        validation_alias=AliasChoices("proficiency_score", "proficiencyScore"),
    )
    evidence_confidence: float = Field(
        ...,
        validation_alias=AliasChoices("evidence_confidence", "evidenceConfidence"),
    )
    verification_status: str = Field(
        "VERIFIED",
        validation_alias=AliasChoices("verification_status", "verificationStatus"),
    )

    model_config = ConfigDict(populate_by_name=True)

    # Extract nested fields and validate student skill rules before instantiation
    @model_validator(mode="before")
    @classmethod
    def extract_nested_and_validate(cls, data: Any) -> Any:
        if not isinstance(data, dict):
            return data

        # Extract nested proficiency object if flat score not provided
        if "proficiency_score" not in data and "proficiencyScore" not in data:
            prof = data.get("proficiency")
            if isinstance(prof, dict):
                if "score" in prof:
                    data["proficiency_score"] = prof["score"]
                if "level" in prof and "proficiency_level" not in data:
                    data["proficiency_level"] = prof["level"]

        # Validate mapping status
        raw_status = data.get("mapping_status", "verified")
        if (
            not isinstance(raw_status, str)
            or raw_status.lower() not in VALID_MAPPING_STATUSES
        ):
            std_name = data.get("standard_name", "unknown")
            raise ProfileValidationError(
                f"[UserSkillProfile] skill '{std_name}': invalid mapping_status '{raw_status}'",
                profile_type="user_skill_profile",
                field="mapping_status",
            )
        data["mapping_status"] = raw_status.lower()

        # Validate canonical skill_id
        skill_id = data.get("skill_id") or data.get("skillId")
        std_name = data.get("standard_name", "unknown")
        if data["mapping_status"] in CANONICAL_MAPPING_STATUSES:
            if not skill_id or not isinstance(skill_id, str):
                raise ProfileValidationError(
                    f"[UserSkillProfile] skill '{std_name}': mapping_status is '{raw_status}' but canonical skill_id is missing",
                    profile_type="user_skill_profile",
                    field="skill_id",
                )
            if not CANONICAL_SKILL_ID_REGEX.match(skill_id):
                raise ProfileValidationError(
                    f"[UserSkillProfile] skill '{std_name}': invalid canonical skill_id '{skill_id}' (must match SK-XXXXXX)",
                    profile_type="user_skill_profile",
                    field="skill_id",
                )
        elif skill_id and not CANONICAL_SKILL_ID_REGEX.match(skill_id):
            raise ProfileValidationError(
                f"[UserSkillProfile] skill '{std_name}': invalid canonical skill_id '{skill_id}' (must match SK-XXXXXX)",
                profile_type="user_skill_profile",
                field="skill_id",
            )

        # Validate proficiency_score: must be finite and between 0.0 and 1.0
        prof_raw = (
            data.get("proficiency_score")
            if "proficiency_score" in data
            else data.get("proficiencyScore")
        )
        score = _check_finite_number(
            prof_raw, "proficiency_score", "UserSkillProfile", f"skill '{std_name}'"
        )
        if score < 0.0 or score > 1.0:
            raise ProfileValidationError(
                f"[UserSkillProfile] skill '{std_name}': proficiency_score {score} must be between 0.0 and 1.0",
                profile_type="user_skill_profile",
                field="proficiency_score",
            )
        data["proficiency_score"] = score

        # Validate evidence_confidence: must be finite and between 0.0 and 1.0
        conf_raw = (
            data.get("evidence_confidence")
            if "evidence_confidence" in data
            else data.get("evidenceConfidence")
        )
        conf = _check_finite_number(
            conf_raw,
            "evidence_confidence",
            "UserSkillProfile",
            f"skill '{std_name}'",
        )
        if conf < 0.0 or conf > 1.0:
            raise ProfileValidationError(
                f"[UserSkillProfile] skill '{std_name}': evidence_confidence {conf} must be between 0.0 and 1.0",
                profile_type="user_skill_profile",
                field="evidence_confidence",
            )
        data["evidence_confidence"] = conf

        return data


# Pydantic schema for validating C02 student skill profiles
class UserSkillProfileInput(BaseModel):
    user_id: uuid.UUID = Field(
        ...,
        validation_alias=AliasChoices("user_id", "userId"),
    )
    profile_version: str = Field(
        ...,
        validation_alias=AliasChoices("profile_version", "profileVersion"),
    )
    skills: list[UserSkillInput] = Field(default_factory=list)

    model_config = ConfigDict(populate_by_name=True)

    # Validate skills list and ensure no duplicate canonical skills exist
    @model_validator(mode="before")
    @classmethod
    def validate_user_profile(cls, data: Any) -> Any:
        if not isinstance(data, dict):
            return data

        skills = data.get("skills", [])
        if not isinstance(skills, list):
            raise ProfileValidationError(
                "[UserSkillProfile]: skills must be a list",
                profile_type="user_skill_profile",
                field="skills",
            )

        seen_skills = set()
        for s in skills:
            if not isinstance(s, dict):
                continue
            s_id = s.get("skill_id") or s.get("skillId")
            if s_id:
                if s_id in seen_skills:
                    raise ProfileValidationError(
                        f"[UserSkillProfile]: duplicate skill entry for canonical skill_id '{s_id}'",
                        profile_type="user_skill_profile",
                        field="skills",
                    )
                seen_skills.add(s_id)

        return data


# Validate an existing IndustryProfile SQLAlchemy model before algorithm execution
def validate_industry_profile(profile: Any) -> None:
    raw_status = getattr(profile, "mapping_status", "verified")
    if not raw_status or raw_status.lower() not in VALID_MAPPING_STATUSES:
        raise ProfileValidationError(
            f"[IndustryProfile: role_id={getattr(profile, 'role_id', None)}]: invalid mapping_status '{raw_status}'",
            profile_type="industry_profile",
            field="mapping_status",
            identifier=str(getattr(profile, "role_id", None)),
        )

    role_id = getattr(profile, "role_id", None)
    candidate_id = getattr(profile, "candidate_role_id", None)
    if (
        not role_id
        and not candidate_id
        and not getattr(profile, "primary_observed_title", None)
    ):
        raise ProfileValidationError(
            "[IndustryProfile]: profile must have role_id, candidate_role_id, or primary_observed_title",
            profile_type="industry_profile",
            field="role_id",
        )

    if raw_status.lower() in CANONICAL_MAPPING_STATUSES:
        if not role_id:
            raise ProfileValidationError(
                f"[IndustryProfile]: mapping_status is '{raw_status}' but canonical role_id is missing",
                profile_type="industry_profile",
                field="role_id",
            )
        if not CANONICAL_ROLE_ID_REGEX.match(role_id):
            raise ProfileValidationError(
                f"[IndustryProfile]: invalid canonical role_id '{role_id}' (must match RL-XXXXXX)",
                profile_type="industry_profile",
                field="role_id",
                identifier=role_id,
            )
    elif role_id and not CANONICAL_ROLE_ID_REGEX.match(role_id):
        raise ProfileValidationError(
            f"[IndustryProfile]: invalid role_id '{role_id}' (must match RL-XXXXXX)",
            profile_type="industry_profile",
            field="role_id",
            identifier=role_id,
        )

    requirements = getattr(profile, "requirements", [])
    if not requirements:
        raise ProfileValidationError(
            f"[IndustryProfile: role_id={role_id}]: requirements cannot be empty",
            profile_type="industry_profile",
            field="requirements",
            identifier=str(role_id),
        )

    seen_skills = set()
    for req in requirements:
        std_name = getattr(req, "standard_name", "unknown")
        req_status = getattr(req, "mapping_status", "verified")
        if not req_status or req_status.lower() not in VALID_MAPPING_STATUSES:
            raise ProfileValidationError(
                f"[IndustryProfile: role_id={role_id}] requirement '{std_name}': invalid mapping_status '{req_status}'",
                profile_type="industry_profile",
                field="mapping_status",
            )

        skill_id = getattr(req, "skill_id", None)
        if req_status.lower() in CANONICAL_MAPPING_STATUSES:
            if not skill_id:
                raise ProfileValidationError(
                    f"[IndustryProfile: role_id={role_id}] requirement '{std_name}': mapping_status is '{req_status}' but canonical skill_id is missing",
                    profile_type="industry_profile",
                    field="skill_id",
                )
            if not CANONICAL_SKILL_ID_REGEX.match(skill_id):
                raise ProfileValidationError(
                    f"[IndustryProfile: role_id={role_id}] requirement '{std_name}': invalid canonical skill_id '{skill_id}' (must match SK-XXXXXX)",
                    profile_type="industry_profile",
                    field="skill_id",
                )
        elif skill_id and not CANONICAL_SKILL_ID_REGEX.match(skill_id):
            raise ProfileValidationError(
                f"[IndustryProfile: role_id={role_id}] requirement '{std_name}': invalid canonical skill_id '{skill_id}' (must match SK-XXXXXX)",
                profile_type="industry_profile",
                field="skill_id",
            )

        weight = _check_finite_number(
            getattr(req, "demand_weight", None),
            "demand_weight",
            "IndustryProfile",
            f"role_id={role_id}, requirement='{std_name}'",
        )
        if weight < 0.0:
            raise ProfileValidationError(
                f"[IndustryProfile: role_id={role_id}] requirement '{std_name}': demand_weight {weight} cannot be negative",
                profile_type="industry_profile",
                field="demand_weight",
            )

        score = _check_finite_number(
            getattr(req, "required_proficiency_score", None),
            "required_proficiency_score",
            "IndustryProfile",
            f"role_id={role_id}, requirement='{std_name}'",
        )
        if score <= 0.0 or score > 1.0:
            raise ProfileValidationError(
                f"[IndustryProfile: role_id={role_id}] requirement '{std_name}': required_proficiency_score {score} must be strictly > 0.0 and <= 1.0",
                profile_type="industry_profile",
                field="required_proficiency_score",
            )

        if skill_id:
            if skill_id in seen_skills:
                raise ProfileValidationError(
                    f"[IndustryProfile: role_id={role_id}]: duplicate requirement for canonical skill_id '{skill_id}'",
                    profile_type="industry_profile",
                    field="requirements",
                )
            seen_skills.add(skill_id)


# Validate an existing UserSkillProfile SQLAlchemy model before algorithm execution
def validate_user_skill_profile(profile: Any) -> None:
    user_id = getattr(profile, "user_id", None)
    if not user_id:
        raise ProfileValidationError(
            "[UserSkillProfile]: user_id is required",
            profile_type="user_skill_profile",
            field="user_id",
        )

    skills = getattr(profile, "skills", [])
    seen_skills = set()
    for sk in skills:
        std_name = getattr(sk, "standard_name", "unknown")
        sk_status = getattr(sk, "mapping_status", "verified")
        if not sk_status or sk_status.lower() not in VALID_MAPPING_STATUSES:
            raise ProfileValidationError(
                f"[UserSkillProfile: user_id={user_id}] skill '{std_name}': invalid mapping_status '{sk_status}'",
                profile_type="user_skill_profile",
                field="mapping_status",
            )

        skill_id = getattr(sk, "skill_id", None)
        if sk_status.lower() in CANONICAL_MAPPING_STATUSES:
            if not skill_id:
                raise ProfileValidationError(
                    f"[UserSkillProfile: user_id={user_id}] skill '{std_name}': mapping_status is '{sk_status}' but canonical skill_id is missing",
                    profile_type="user_skill_profile",
                    field="skill_id",
                )
            if not CANONICAL_SKILL_ID_REGEX.match(skill_id):
                raise ProfileValidationError(
                    f"[UserSkillProfile: user_id={user_id}] skill '{std_name}': invalid canonical skill_id '{skill_id}' (must match SK-XXXXXX)",
                    profile_type="user_skill_profile",
                    field="skill_id",
                )
        elif skill_id and not CANONICAL_SKILL_ID_REGEX.match(skill_id):
            raise ProfileValidationError(
                f"[UserSkillProfile: user_id={user_id}] skill '{std_name}': invalid canonical skill_id '{skill_id}' (must match SK-XXXXXX)",
                profile_type="user_skill_profile",
                field="skill_id",
            )

        score = _check_finite_number(
            getattr(sk, "proficiency_score", None),
            "proficiency_score",
            "UserSkillProfile",
            f"user_id={user_id}, skill='{std_name}'",
        )
        if score < 0.0 or score > 1.0:
            raise ProfileValidationError(
                f"[UserSkillProfile: user_id={user_id}] skill '{std_name}': proficiency_score {score} must be between 0.0 and 1.0",
                profile_type="user_skill_profile",
                field="proficiency_score",
            )

        conf = _check_finite_number(
            getattr(sk, "evidence_confidence", None),
            "evidence_confidence",
            "UserSkillProfile",
            f"user_id={user_id}, skill='{std_name}'",
        )
        if conf < 0.0 or conf > 1.0:
            raise ProfileValidationError(
                f"[UserSkillProfile: user_id={user_id}] skill '{std_name}': evidence_confidence {conf} must be between 0.0 and 1.0",
                profile_type="user_skill_profile",
                field="evidence_confidence",
            )

        if skill_id:
            if skill_id in seen_skills:
                raise ProfileValidationError(
                    f"[UserSkillProfile: user_id={user_id}]: duplicate skill entry for canonical skill_id '{skill_id}'",
                    profile_type="user_skill_profile",
                    field="skills",
                )
            seen_skills.add(skill_id)


# Validate an industry role profile dictionary payload
def validate_industry_profile_data(data: dict[str, Any]) -> IndustryProfileInput:
    try:
        return IndustryProfileInput.model_validate(data)
    except ProfileValidationError:
        raise
    except ValidationError as val_err:
        first_err = val_err.errors()[0] if val_err.errors() else {}
        loc = ".".join(str(k) for k in first_err.get("loc", []))
        msg = first_err.get("msg", str(val_err)).replace("Value error, ", "")
        raise ProfileValidationError(
            msg, profile_type="industry_profile", field=loc
        ) from val_err


# Validate an industry requirement dictionary payload
def validate_industry_requirement_data(
    data: dict[str, Any],
) -> IndustryRequirementInput:
    try:
        return IndustryRequirementInput.model_validate(data)
    except ProfileValidationError:
        raise
    except ValidationError as val_err:
        first_err = val_err.errors()[0] if val_err.errors() else {}
        loc = ".".join(str(k) for k in first_err.get("loc", []))
        msg = first_err.get("msg", str(val_err)).replace("Value error, ", "")
        raise ProfileValidationError(
            msg, profile_type="industry_profile", field=loc
        ) from val_err


# Validate a user skill profile dictionary payload
def validate_user_skill_profile_data(data: dict[str, Any]) -> UserSkillProfileInput:
    try:
        return UserSkillProfileInput.model_validate(data)
    except ProfileValidationError:
        raise
    except ValidationError as val_err:
        first_err = val_err.errors()[0] if val_err.errors() else {}
        loc = ".".join(str(k) for k in first_err.get("loc", []))
        msg = first_err.get("msg", str(val_err)).replace("Value error, ", "")
        raise ProfileValidationError(
            msg, profile_type="user_skill_profile", field=loc
        ) from val_err


# Validate a user skill dictionary payload
def validate_user_skill_data(data: dict[str, Any]) -> UserSkillInput:
    try:
        return UserSkillInput.model_validate(data)
    except ProfileValidationError:
        raise
    except ValidationError as val_err:
        first_err = val_err.errors()[0] if val_err.errors() else {}
        loc = ".".join(str(k) for k in first_err.get("loc", []))
        msg = first_err.get("msg", str(val_err)).replace("Value error, ", "")
        raise ProfileValidationError(
            msg, profile_type="user_skill_profile", field=loc
        ) from val_err
