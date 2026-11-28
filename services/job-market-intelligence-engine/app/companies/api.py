"""Company job posts: companies post jobs, an admin verifies each company, students apply on Skillaro.

Every endpoint needs a logged-in caller (Authorization: Bearer <token from the Auth Service>):

Company (role hr)
    GET/POST/PATCH /jobs/company                       the caller's company (POST creates it, waiting for an admin)
    GET  /jobs/company/skill-list                      skill names and education choices for the post form
    POST /jobs/company/skills                          find skills, education, years and certificates in a description
    GET/POST /jobs/company/vacancies                   the company's job posts / post a job (DRAFT or PUBLISHED)
    GET/PUT /jobs/company/vacancies/{id}               one job post / replace it
    PATCH /jobs/company/vacancies/{id}                 {status: PUBLISHED | CLOSED | DRAFT}
    GET  /jobs/company/applications                    applicants (?vacancy_id=&status=)
    GET  /jobs/company/applications/{id}               one applicant
    PATCH /jobs/company/applications/{id}              {status: SEEN (opened) | SHORTLISTED | NOT_SELECTED}
    GET  /jobs/company/applications/{id}/cv            the applicant's CV (PDF)
Admin (role admin)
    GET  /jobs/admin/companies                         every company and its status
    POST /jobs/admin/companies/{id}/verify | reject | reopen
Students (any logged-in user; applying needs role user)
    GET  /jobs/vacancies, /jobs/vacancies/{id}         live jobs from verified companies
    POST /jobs/vacancies/{id}/applications             apply (multipart: phone, education, note, consent, cv)
    GET  /jobs/applications                            my applications, and my last CV / phone / education
    DELETE /jobs/applications/{id}                     withdraw (deletes the application and its CV)

Needs SKILLBRIDGE_DATABASE_URL (the job_market tables) and SKILLBRIDGE_AUTH_URL; without them these answer 503.
"""

from __future__ import annotations

import re
import threading
import uuid
from collections.abc import Iterator
from contextlib import contextmanager
from datetime import date, datetime
from pathlib import PurePath
from typing import Literal

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, Response, UploadFile, status
from pydantic import BaseModel, Field, field_validator
from sqlalchemy import create_engine
from sqlalchemy.engine import Connection, Engine

from app.collectors.config import load_settings
from app.companies import store
from app.companies.auth import ADMIN, COMPANY, STUDENT, Caller, current_caller, require_role
from app.companies.skills import EDUCATION_OPTIONS, canonical_skill, detect
from app.database.role_profiles import QUALIFICATION, SKILL_TYPE

router = APIRouter(prefix="/jobs", tags=["company job posts"])

SECTORS = ("IT", "HR", "Management", "Agriculture", "Other")
CAREER_LEVELS = ("INTERN", "TRAINEE", "JUNIOR", "MID_LEVEL", "SENIOR", "LEAD")
EMPLOYMENT_TYPES = ("FULL_TIME", "PART_TIME", "CONTRACT", "INTERNSHIP")
APPLICATION_STATUSES = ("NEW", "SEEN", "SHORTLISTED", "NOT_SELECTED")
MAX_CV_BYTES = 2 * 1024 * 1024
EMAIL = re.compile(r"^[^\s@]+@[^\s@]+\.[a-z]{2,}$", re.IGNORECASE)
WEB = re.compile(r"^(https?://)?[a-z0-9-]+(\.[a-z0-9-]+)+(:\d+)?(/\S*)?$", re.IGNORECASE)
PHONE = re.compile(r"^\+?[0-9][0-9 ()-]{6,18}[0-9]$")

# --- database ------------------------------------------------------------------------------------------

_engine: dict = {"url": None, "engine": None}
_engine_lock = threading.Lock()


def engine() -> Engine:
    url = load_settings().database_url
    if not url:
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, "Company job posts need SKILLBRIDGE_DATABASE_URL")
    with _engine_lock:
        if _engine["url"] != url:
            _engine.update(url=url, engine=create_engine(url, pool_pre_ping=True))
        return _engine["engine"]


@contextmanager
def transaction() -> Iterator[Connection]:
    """One database transaction; the store's errors become HTTP answers."""
    try:
        with engine().begin() as conn:
            yield conn
    except store.NotFound as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(exc)) from None
    except store.Conflict as exc:
        raise HTTPException(status.HTTP_409_CONFLICT, str(exc)) from None
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from None


def _company(conn: Connection, caller: Caller):
    require_role(caller, COMPANY)
    company = store.company_of_user(conn, caller.id)
    if company is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Create your company profile first")
    return company


# --- models ----------------------------------------------------------------------------------------------


def _clean(value: str | None) -> str | None:
    value = " ".join((value or "").split())
    return value or None


class CompanyIn(BaseModel):
    name: str = Field(min_length=2, max_length=120)
    website: str | None = Field(default=None, max_length=200)
    sector: Literal[SECTORS]  # type: ignore[valid-type]
    city: str | None = Field(default=None, max_length=80)
    description: str | None = Field(default=None, max_length=1000)

    @field_validator("name")
    @classmethod
    def _name(cls, value: str | None) -> str | None:
        if value is None:
            return None
        value = " ".join(value.split())
        if len(value) < 2:
            raise ValueError("Enter the company name")
        return value

    @field_validator("website")
    @classmethod
    def _website(cls, value: str | None) -> str | None:
        value = _clean(value)
        if value and not WEB.match(value):
            raise ValueError("Enter the company's web address, for example yourcompany.lk")
        return value

    @field_validator("city", "description")
    @classmethod
    def _text(cls, value: str | None) -> str | None:
        return value.strip() or None if value else None


class CompanyPatch(CompanyIn):
    name: str | None = Field(default=None, min_length=2, max_length=120)  # type: ignore[assignment]
    sector: Literal[SECTORS] | None = None  # type: ignore[valid-type,assignment]


class CompanyOut(BaseModel):
    company_id: uuid.UUID
    name: str
    website: str | None
    sector: str | None
    city: str | None
    description: str | None
    contact_name: str | None
    contact_email: str | None
    status: str  # PENDING | VERIFIED | REJECTED
    created_at: datetime
    verified_at: datetime | None
    rejected_at: datetime | None
    published: int | None = None  # admin list: published jobs that haven't passed their closing date
    drafts: int | None = None
    applicants: int | None = None  # the company's own view
    new_applicants: int | None = None


class SkillIn(BaseModel):
    name: str = Field(min_length=1, max_length=80)
    importance: Literal["REQUIRED", "PREFERRED"] = "REQUIRED"
    skill_type: Literal["TECHNICAL", "BEHAVIOURAL"] | None = None  # for a skill that isn't in the skill list


class VacancyIn(BaseModel):
    title: str = Field(min_length=2, max_length=150)
    career_level: Literal[CAREER_LEVELS]  # type: ignore[valid-type]
    employment_type: Literal[EMPLOYMENT_TYPES]  # type: ignore[valid-type]
    location: str | None = Field(default=None, max_length=120)
    closing_date: date | None = None
    apply_url: str | None = Field(default=None, max_length=300)
    description: str = Field(default="", max_length=8000)
    status: Literal["DRAFT", "PUBLISHED"] = "DRAFT"
    skills: list[SkillIn] = Field(default_factory=list, max_length=40)
    education: str | None = None
    minimum_years: int | None = Field(default=None, ge=0, le=40)
    certifications: list[str] = Field(default_factory=list, max_length=10)

    @field_validator("title", "location")
    @classmethod
    def _one_line(cls, value: str | None) -> str | None:
        return _clean(value)

    @field_validator("apply_url")
    @classmethod
    def _apply_url(cls, value: str | None) -> str | None:
        value = _clean(value)
        if not value:
            return None
        if EMAIL.match(value):
            return value
        if WEB.match(value):
            return value if value.lower().startswith(("http://", "https://")) else f"https://{value}"
        raise ValueError("Your own application page must be a web address or an email address. Or leave it empty.")

    @field_validator("education")
    @classmethod
    def _education(cls, value: str | None) -> str | None:
        if value and value not in EDUCATION_OPTIONS:
            raise ValueError(f"Education must be one of: {', '.join(EDUCATION_OPTIONS)}")
        return value or None

    @field_validator("certifications")
    @classmethod
    def _certificates(cls, value: list[str]) -> list[str]:
        return list(dict.fromkeys(c for c in (_clean(v) for v in value) if c))[:10]


class CompanyInfo(BaseModel):
    company_id: uuid.UUID
    name: str
    sector: str | None
    city: str | None
    website: str | None


class SkillOut(BaseModel):
    name: str
    skill_type: str
    importance: str
    skill_id: str | None = None


class VacancyOut(BaseModel):
    vacancy_id: uuid.UUID
    title: str
    career_level: str | None
    employment_type: str | None
    location: str | None
    description: str
    closing_date: date | None
    apply_url: str | None  # for students: only after they applied
    status: str  # DRAFT | PUBLISHED | CLOSED
    state: str  # DRAFT | WAITING | HIDDEN | LIVE | EXPIRED | CLOSED
    published_at: datetime | None
    created_at: datetime
    updated_at: datetime
    company: CompanyInfo
    required: list[str]
    preferred: list[str]
    skills: list[SkillOut]
    education: str | None
    minimum_years: int | None
    certifications: list[str]
    applicants: int | None = None
    new_applicants: int | None = None
    application_status: str | None = None  # the calling student's application, if any


class StatusIn(BaseModel):
    status: str


class DetectIn(BaseModel):
    title: str = Field(default="", max_length=150)
    description: str = Field(max_length=8000)


class DetectedSkillOut(BaseModel):
    name: str
    skill_type: str
    category: str
    importance: str
    in_skill_list: bool


class DetectOut(BaseModel):
    skills: list[DetectedSkillOut]
    education: str | None
    minimum_years: int | None
    certifications: list[str]


class SkillListOut(BaseModel):
    skills: list[dict]
    education_options: list[str]


class ApplicationOut(BaseModel):
    application_id: uuid.UUID
    vacancy_id: uuid.UUID
    job_title: str
    full_name: str
    email: str
    phone: str
    education: str | None
    note: str | None
    status: str
    applied_at: datetime
    updated_at: datetime
    cv_file_name: str | None
    cv_size_bytes: int | None


class MyApplication(BaseModel):
    application_id: uuid.UUID
    vacancy_id: uuid.UUID
    status: str
    applied_at: datetime
    title: str
    location: str | None
    company_id: uuid.UUID
    company_name: str
    job_open: bool
    cv_file_name: str | None


class MyApplications(BaseModel):
    applications: list[MyApplication]
    last_cv: dict | None
    last_phone: str | None
    last_education: str | None


# --- company -------------------------------------------------------------------------------------------


@router.get("/company", response_model=CompanyOut)
def my_company(caller: Caller = Depends(current_caller)) -> dict:
    with transaction() as conn:
        company = _company(conn, caller)
        return {**store.company_dict(company), **store.company_counts(conn, company.company_id)}


@router.post("/company", response_model=CompanyOut, status_code=status.HTTP_201_CREATED)
def create_company(body: CompanyIn, caller: Caller = Depends(current_caller)) -> dict:
    require_role(caller, COMPANY)
    with transaction() as conn:
        store.create_company(conn, caller.id, caller.full_name, caller.email, body.model_dump(), store.utc_now())
        return store.company_dict(store.company_of_user(conn, caller.id))


@router.patch("/company", response_model=CompanyOut)
def update_company(body: CompanyPatch, caller: Caller = Depends(current_caller)) -> dict:
    with transaction() as conn:
        company = _company(conn, caller)
        store.update_company(conn, company, body.model_dump(exclude_unset=True))
        return store.company_dict(store.company_of_user(conn, caller.id))


@router.get("/company/skill-list", response_model=SkillListOut)
def skill_list(caller: Caller = Depends(current_caller)) -> dict:
    require_role(caller, COMPANY)
    skills = sorted(({"name": s.name, "skill_type": SKILL_TYPE.get(s.category, "TECHNICAL")}
                     for s in store.lexicon().skills if s.category != QUALIFICATION), key=lambda s: s["name"].casefold())
    return {"skills": skills, "education_options": list(EDUCATION_OPTIONS)}


@router.post("/company/skills", response_model=DetectOut)
def find_skills(body: DetectIn, caller: Caller = Depends(current_caller)) -> dict:
    with transaction() as conn:
        company = _company(conn, caller)
    found = detect(body.title, body.description, company.sector, store.lexicon())
    return {"skills": [vars(s) for s in found.skills], "education": found.education,
            "minimum_years": found.minimum_years, "certifications": found.certifications}


@router.get("/company/vacancies", response_model=list[VacancyOut])
def my_vacancies(caller: Caller = Depends(current_caller)) -> list[dict]:
    with transaction() as conn:
        return store.company_vacancies_list(conn, _company(conn, caller))


@router.post("/company/vacancies", response_model=VacancyOut, status_code=status.HTTP_201_CREATED)
def post_vacancy(body: VacancyIn, caller: Caller = Depends(current_caller)) -> dict:
    with transaction() as conn:
        company = _company(conn, caller)
        data = _vacancy_input(body)
        vacancy_id = store.save_vacancy(conn, company, caller.id, data, store.utc_now())
        return store.company_vacancy(conn, company, vacancy_id)


@router.get("/company/vacancies/{vacancy_id}", response_model=VacancyOut)
def my_vacancy(vacancy_id: uuid.UUID, caller: Caller = Depends(current_caller)) -> dict:
    with transaction() as conn:
        return store.company_vacancy(conn, _company(conn, caller), vacancy_id)


@router.put("/company/vacancies/{vacancy_id}", response_model=VacancyOut)
def replace_vacancy(vacancy_id: uuid.UUID, body: VacancyIn, caller: Caller = Depends(current_caller)) -> dict:
    with transaction() as conn:
        company = _company(conn, caller)
        data = _vacancy_input(body)
        current = store.company_vacancy(conn, company, vacancy_id)
        if current["status"] == "CLOSED" and data.status == "DRAFT":
            data.status = "CLOSED"  # editing a closed job keeps it closed
        store.save_vacancy(conn, company, caller.id, data, store.utc_now(), vacancy_id)
        return store.company_vacancy(conn, company, vacancy_id)


@router.patch("/company/vacancies/{vacancy_id}", response_model=VacancyOut)
def change_vacancy_status(vacancy_id: uuid.UUID, body: StatusIn, caller: Caller = Depends(current_caller)) -> dict:
    if body.status not in ("DRAFT", "PUBLISHED", "CLOSED"):
        raise HTTPException(422, "Status must be DRAFT, PUBLISHED or CLOSED")
    with transaction() as conn:
        company = _company(conn, caller)
        current = store.company_vacancy(conn, company, vacancy_id)
        if body.status == "PUBLISHED":
            _check_publishable(current["title"], current["description"], len(current["skills"]), current["closing_date"])
        store.set_vacancy_status(conn, company.company_id, vacancy_id, body.status, store.utc_now())
        return store.company_vacancy(conn, company, vacancy_id)


def _vacancy_input(body: VacancyIn) -> store.VacancyInput:
    lexicon = store.lexicon()
    skills: dict[str, tuple[str, str, str]] = {}
    for item in body.skills:
        found = canonical_skill(item.name, lexicon)
        if found is None:
            raise ValueError(f"{item.name} is a qualification: choose it under Education or Certificates")
        name, skill_type, in_list = found
        skills.setdefault(name.casefold(), (name, skill_type if in_list else (item.skill_type or skill_type), item.importance))
    if body.status == "PUBLISHED":
        _check_publishable(body.title, body.description, len(skills), body.closing_date)
    return store.VacancyInput(
        title=body.title, career_level=body.career_level, employment_type=body.employment_type,
        location=body.location, closing_date=body.closing_date, apply_url=body.apply_url,
        description=body.description.strip(), status=body.status, skills=list(skills.values()),
        education=body.education, minimum_years=body.minimum_years, certifications=body.certifications,
    )


def _check_publishable(title: str, description: str, skill_count: int, closing: date | None) -> None:
    if len((description or "").split()) < 5:
        raise ValueError("Write the job description before publishing")
    if skill_count == 0:
        raise ValueError("Add at least one skill before publishing, so students can see what you need")
    if closing is not None and closing < store.today():
        raise ValueError("The closing date has passed. Choose a later date to publish")


# --- the company's applicants --------------------------------------------------------------------------


@router.get("/company/applications", response_model=list[ApplicationOut])
def applicants(vacancy_id: uuid.UUID | None = None, status_filter: str | None = Query(default=None, alias="status"),
               caller: Caller = Depends(current_caller)) -> list[dict]:
    if status_filter and status_filter not in APPLICATION_STATUSES:
        raise HTTPException(422, "Unknown status")
    with transaction() as conn:
        company = _company(conn, caller)
        return store.company_applications(conn, company.company_id, vacancy_id, status_filter)


@router.get("/company/applications/{application_id}", response_model=ApplicationOut)
def applicant(application_id: uuid.UUID, caller: Caller = Depends(current_caller)) -> dict:
    with transaction() as conn:
        company = _company(conn, caller)
        return store.company_application(conn, company.company_id, application_id)


@router.patch("/company/applications/{application_id}", response_model=ApplicationOut)
def change_applicant_status(application_id: uuid.UUID, body: StatusIn, caller: Caller = Depends(current_caller)) -> dict:
    if body.status not in ("SEEN", "SHORTLISTED", "NOT_SELECTED"):
        raise HTTPException(422, "Status must be SEEN, SHORTLISTED or NOT_SELECTED")
    with transaction() as conn:
        company = _company(conn, caller)
        return store.set_application_status(conn, company.company_id, application_id, body.status, store.utc_now())


@router.get("/company/applications/{application_id}/cv")
def applicant_cv(application_id: uuid.UUID, caller: Caller = Depends(current_caller)) -> Response:
    with transaction() as conn:
        company = _company(conn, caller)
        name, content_type, content = store.application_cv(conn, company.company_id, application_id)
    safe = re.sub(r'[^A-Za-z0-9._ -]', "_", name)
    return Response(content, media_type=content_type,
                    headers={"Content-Disposition": f'inline; filename="{safe}"', "Cache-Control": "private, no-store"})


# --- admin -----------------------------------------------------------------------------------------------


@router.get("/admin/companies", response_model=list[CompanyOut])
def admin_companies(caller: Caller = Depends(current_caller)) -> list[dict]:
    require_role(caller, ADMIN)
    with transaction() as conn:
        return store.all_companies(conn)


@router.post("/admin/companies/{company_id}/{action}", response_model=CompanyOut)
def review_company(company_id: uuid.UUID, action: Literal["verify", "reject", "reopen"],
                   caller: Caller = Depends(current_caller)) -> dict:
    require_role(caller, ADMIN)
    with transaction() as conn:
        store.review_company(conn, company_id, action, caller.id, store.utc_now())
        return next(c for c in store.all_companies(conn) if c["company_id"] == company_id)


# --- students ----------------------------------------------------------------------------------------------


def _for_student(item: dict) -> dict:
    """Students see a company's own application page only after they applied on Skillaro."""
    return item if item.get("application_status") else {**item, "apply_url": None}


@router.get("/vacancies", response_model=list[VacancyOut])
def vacancies(caller: Caller = Depends(current_caller)) -> list[dict]:
    with transaction() as conn:
        return [_for_student(v) for v in store.live_vacancies(conn, caller.id)]


@router.get("/vacancies/{vacancy_id}", response_model=VacancyOut)
def vacancy(vacancy_id: uuid.UUID, caller: Caller = Depends(current_caller)) -> dict:
    with transaction() as conn:
        return _for_student(store.live_vacancy(conn, vacancy_id, caller.id))


@router.post("/vacancies/{vacancy_id}/applications", response_model=MyApplication, status_code=status.HTTP_201_CREATED)
def apply(
    vacancy_id: uuid.UUID,
    phone: str = Form(max_length=40),
    consent: bool = Form(),
    education: str | None = Form(default=None, max_length=300),
    note: str | None = Form(default=None, max_length=1000),
    cv: UploadFile | None = File(default=None),
    caller: Caller = Depends(current_caller),
) -> dict:
    require_role(caller, STUDENT)
    if not consent:
        raise HTTPException(422, "Agree to share your details with the company first")
    phone = " ".join(phone.split())
    if not PHONE.match(phone):
        raise HTTPException(422, "Enter a phone number, for example 077 123 4567")
    file = None
    if cv is not None and cv.filename:
        content = cv.file.read(MAX_CV_BYTES + 1)
        if len(content) > MAX_CV_BYTES:
            raise HTTPException(413, "Your CV must be 2 MB or smaller")
        if not content.startswith(b"%PDF-"):
            raise HTTPException(422, "Your CV must be a PDF file")
        file = (PurePath(cv.filename).name[-120:] or "CV.pdf", "application/pdf", content)
    data = store.ApplicationInput(phone=phone, education=_clean(education), note=(note or "").strip() or None, cv=file)
    with transaction() as conn:
        application_id = store.apply(conn, vacancy_id, caller.id, caller.full_name, caller.email, data, store.utc_now())
        mine = store.my_applications(conn, caller.id)["applications"]
    return next(a for a in mine if a["application_id"] == application_id)


@router.get("/applications", response_model=MyApplications)
def my_applications(caller: Caller = Depends(current_caller)) -> dict:
    with transaction() as conn:
        return store.my_applications(conn, caller.id)


@router.delete("/applications/{application_id}", status_code=status.HTTP_204_NO_CONTENT)
def withdraw(application_id: uuid.UUID, caller: Caller = Depends(current_caller)) -> Response:
    with transaction() as conn:
        store.withdraw(conn, caller.id, application_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
