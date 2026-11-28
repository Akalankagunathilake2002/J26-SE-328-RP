"""Reads and writes company job posts: companies, vacancies (with their VACANCY role profile) and applications.

Rules:
- A company is PENDING until an admin verifies it; REJECTED keeps all its jobs hidden. Changing the name or
  website sends a company back to PENDING.
- A vacancy is live (students see it and can apply) when it is PUBLISHED, its company is verified and its
  closing date (Sri Lanka time) hasn't passed.
- A vacancy's skills, education, minimum years and certificates are its VACANCY role profile
  (Skillaro_DB_Contract_v2): demand_weight 1.0 for REQUIRED skills, 0.5 for PREFERRED. Saving a vacancy writes
  a new profile version (v1, v2 …) and archives the previous one.
- An application keeps a copy of what the student agreed to share (name, email, phone, education, note, CV).
  Withdrawing deletes it, CV included.
"""

from __future__ import annotations

import time
import uuid
from collections import defaultdict
from dataclasses import dataclass
from datetime import date, datetime, timezone
from zoneinfo import ZoneInfo

from sqlalchemy import and_, delete, func, insert, select, update
from sqlalchemy.engine import Connection, Row

from app.collectors.config import load_settings
from app.companies.skills import EDUCATION_LABELS, EDUCATION_OPTIONS
from app.database.companies import (
    application_cvs,
    companies,
    company_users,
    company_vacancies,
    vacancy_applications,
)
from app.database.contract import (
    role_profile_certifications,
    role_profile_education,
    role_profile_experience,
    role_profile_requirements,
    role_profiles,
)
from app.database.role_profiles import lexicon_skill_ids
from app.processing.roles import RoleTaxonomy
from app.processing.skills import SkillLexicon

SRI_LANKA = ZoneInfo("Asia/Colombo")
DEMAND_WEIGHT = {"REQUIRED": 1.0, "PREFERRED": 0.5}
LEXICON_IDS_SECONDS = 3600


class NotFound(Exception):
    pass


class Conflict(Exception):
    pass


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def today() -> date:
    return datetime.now(SRI_LANKA).date()


# --- the skill list, the role taxonomy and SSKS skill ids (loaded once) -----------------------------

_shared: dict = {"lexicon": None, "taxonomy": None, "ids": None, "ids_at": 0.0}


def lexicon() -> SkillLexicon:
    if _shared["lexicon"] is None:
        _shared["lexicon"] = SkillLexicon.load()
    return _shared["lexicon"]


def taxonomy() -> RoleTaxonomy:
    if _shared["taxonomy"] is None:
        _shared["taxonomy"] = RoleTaxonomy.load()
    return _shared["taxonomy"]


def skill_ids() -> dict[str, tuple[str, ...]]:
    """SSKS ids of the lexicon skills: hand-set ones, plus SSKS matches when SKILLBRIDGE_SSKS_URL is set."""
    if _shared["ids"] is None or time.monotonic() - _shared["ids_at"] > LEXICON_IDS_SECONDS:
        _shared["ids"] = lexicon_skill_ids(lexicon(), load_settings().ssks_url)
        _shared["ids_at"] = time.monotonic()
    return _shared["ids"]


# --- companies ---------------------------------------------------------------------------------------


def company_status(row) -> str:
    if row.verified:
        return "VERIFIED"
    return "REJECTED" if row.rejected_at else "PENDING"


def company_of_user(conn: Connection, user_id: uuid.UUID) -> Row | None:
    return conn.execute(
        select(companies).join(company_users, company_users.c.company_id == companies.c.company_id)
        .where(company_users.c.user_id == user_id)
    ).first()


def create_company(conn: Connection, user_id: uuid.UUID, contact_name: str, contact_email: str, fields: dict,
                   now: datetime) -> uuid.UUID:
    if company_of_user(conn, user_id) is not None:
        raise Conflict("Your account already has a company")
    company_id = uuid.uuid4()
    conn.execute(insert(companies).values(
        company_id=company_id, verified=False, created_by_user_id=user_id, created_at=now,
        contact_name=contact_name, contact_email=contact_email, **fields,
    ))
    conn.execute(insert(company_users).values(company_id=company_id, user_id=user_id, added_at=now))
    return company_id


def update_company(conn: Connection, company: Row, fields: dict) -> None:
    """Changing the name or website sends the company back for verification."""
    values = dict(fields)
    if any(k in values and (values[k] or None) != (getattr(company, k) or None) for k in ("name", "website")):
        values.update(verified=False, verified_at=None, rejected_at=None)
    if values:
        conn.execute(update(companies).where(companies.c.company_id == company.company_id).values(**values))


def review_company(conn: Connection, company_id: uuid.UUID, action: str, admin_id: uuid.UUID, now: datetime) -> None:
    values = {
        "verify": {"verified": True, "verified_at": now, "rejected_at": None},
        "reject": {"verified": False, "verified_at": None, "rejected_at": now},
        "reopen": {"verified": False, "verified_at": None, "rejected_at": None},
    }[action]
    done = conn.execute(update(companies).where(companies.c.company_id == company_id)
                        .values(reviewed_by_user_id=admin_id, **values)).rowcount
    if not done:
        raise NotFound("No such company")


def all_companies(conn: Connection) -> list[dict]:
    """Every company with its job counts, newest first (for the admin)."""
    rows = conn.execute(select(companies).order_by(companies.c.created_at.desc())).all()
    vacancies = conn.execute(select(company_vacancies.c.company_id, company_vacancies.c.status,
                                    company_vacancies.c.closing_date)).all()
    counts: dict = defaultdict(lambda: {"published": 0, "drafts": 0})
    for v in vacancies:
        if v.status == "PUBLISHED" and not _past(v.closing_date):
            counts[v.company_id]["published"] += 1
        elif v.status == "DRAFT":
            counts[v.company_id]["drafts"] += 1
    return [{**company_dict(row), **counts[row.company_id]} for row in rows]


def company_dict(row) -> dict:
    return {
        "company_id": row.company_id, "name": row.name, "website": row.website, "sector": row.sector,
        "city": row.city, "description": row.description, "contact_name": row.contact_name,
        "contact_email": row.contact_email, "status": company_status(row), "created_at": row.created_at,
        "verified_at": row.verified_at, "rejected_at": row.rejected_at,
    }


# --- vacancies ---------------------------------------------------------------------------------------


def _past(closing: date | None) -> bool:
    return closing is not None and closing < today()


def vacancy_state(status: str, closing: date | None, company) -> str:
    """What a vacancy is right now: DRAFT, WAITING (published, company not verified), HIDDEN (company
    rejected), LIVE, EXPIRED (closing date passed) or CLOSED."""
    if status in ("DRAFT", "CLOSED"):
        return status
    if _past(closing):
        return "EXPIRED"
    state = company_status(company)
    return "LIVE" if state == "VERIFIED" else "HIDDEN" if state == "REJECTED" else "WAITING"


@dataclass
class VacancyInput:
    title: str
    career_level: str
    employment_type: str
    location: str | None
    closing_date: date | None
    apply_url: str | None
    description: str
    status: str  # DRAFT | PUBLISHED
    skills: list[tuple[str, str, str]]  # (name, skill type, importance)
    education: str | None  # a label of EDUCATION_OPTIONS
    minimum_years: int | None
    certifications: list[str]


def save_vacancy(conn: Connection, company: Row, user_id: uuid.UUID, data: VacancyInput, now: datetime,
                 vacancy_id: uuid.UUID | None = None) -> uuid.UUID:
    role_id = _ssks_role_id(data.title, company.sector)
    values = dict(
        job_title=data.title, role_id=role_id, candidate_role_id=None, career_level=data.career_level,
        employment_type=data.employment_type, location=data.location, description=data.description,
        closing_date=data.closing_date, apply_url=data.apply_url, status=data.status, updated_at=now,
    )
    if vacancy_id is None:
        vacancy_id = uuid.uuid4()
        conn.execute(insert(company_vacancies).values(
            vacancy_id=vacancy_id, company_id=company.company_id, posted_by_user_id=user_id, created_at=now,
            published_at=now if data.status == "PUBLISHED" else None, **values))
    else:
        old = _own_vacancy(conn, company.company_id, vacancy_id)
        if data.status == "PUBLISHED" and old.published_at is None:
            values["published_at"] = now
        conn.execute(update(company_vacancies).where(company_vacancies.c.vacancy_id == vacancy_id).values(**values))
    _write_profile(conn, vacancy_id, data, role_id, company.sector, now)
    return vacancy_id


def set_vacancy_status(conn: Connection, company_id: uuid.UUID, vacancy_id: uuid.UUID, status: str, now: datetime) -> None:
    old = _own_vacancy(conn, company_id, vacancy_id)
    values = {"status": status, "updated_at": now}
    if status == "PUBLISHED" and old.published_at is None:
        values["published_at"] = now
    conn.execute(update(company_vacancies).where(company_vacancies.c.vacancy_id == vacancy_id).values(**values))
    if status == "PUBLISHED":
        conn.execute(update(role_profiles)
                     .where(role_profiles.c.vacancy_id == vacancy_id, role_profiles.c.profile_type == "VACANCY",
                            role_profiles.c.profile_status == "DRAFT")
                     .values(profile_status="PUBLISHED", published_at=now))


def _own_vacancy(conn: Connection, company_id: uuid.UUID, vacancy_id: uuid.UUID) -> Row:
    row = conn.execute(select(company_vacancies).where(company_vacancies.c.vacancy_id == vacancy_id,
                                                       company_vacancies.c.company_id == company_id)).first()
    if row is None:
        raise NotFound("No such job post")
    return row


def _ssks_role_id(title: str, sector: str | None) -> str | None:
    match = taxonomy().classify(title, [sector] if sector else [])
    if not match.mapped:
        return None
    return next((r.ssks_role_id for r in taxonomy().roles if r.name == match.role), None)


def _write_profile(conn: Connection, vacancy_id: uuid.UUID, data: VacancyInput, role_id: str | None,
                   sector: str | None, now: datetime) -> None:
    versions = conn.execute(select(role_profiles.c.profile_version).where(
        role_profiles.c.profile_type == "VACANCY", role_profiles.c.vacancy_id == vacancy_id)).scalars().all()
    conn.execute(update(role_profiles)
                 .where(role_profiles.c.profile_type == "VACANCY", role_profiles.c.vacancy_id == vacancy_id,
                        role_profiles.c.profile_status != "ARCHIVED")
                 .values(profile_status="ARCHIVED"))
    published = data.status == "PUBLISHED" or conn.execute(
        select(company_vacancies.c.status).where(company_vacancies.c.vacancy_id == vacancy_id)).scalar() == "CLOSED"
    profile_id = uuid.uuid4()
    conn.execute(insert(role_profiles).values(
        profile_id=profile_id, profile_type="VACANCY", vacancy_id=vacancy_id, role_id=role_id, candidate_role_id=None,
        primary_observed_title=data.title, observed_titles=[data.title],
        mapping_status="VERIFIED" if role_id else "UNMAPPED",
        profile_status="PUBLISHED" if published else "DRAFT", profile_version=f"v{len(versions) + 1}",
        career_level=data.career_level, domain_id=None, sector=sector, job_posting_count=1, ads_with_text=1,
        observation_period_from=None, observation_period_to=None, published_at=now if published else None,
        created_at=now,
    ))
    ids = skill_ids()
    for name, skill_type, importance in data.skills:
        found = ids.get(name, ())
        conn.execute(insert(role_profile_requirements).values(
            requirement_id=uuid.uuid4(), profile_id=profile_id, skill_id=sorted(found)[0] if found else None,
            candidate_skill_id=None, standard_name=name, primary_observed_term=name, observed_terms=[name],
            mapping_status="VERIFIED" if found else "UNMAPPED", skill_type=skill_type, importance=importance,
            demand_weight=DEMAND_WEIGHT[importance], demand_frequency=None, job_ads_containing_skill=None,
            required_proficiency_level=None, required_proficiency_score=None,
        ))
    if data.education:
        level, completion = EDUCATION_OPTIONS[data.education]
        conn.execute(insert(role_profile_education).values(
            education_req_id=uuid.uuid4(), profile_id=profile_id, qualification_level=level, accepted_fields=None,
            completion_requirement=completion, is_mandatory=True, job_ads_count=None))
    if data.minimum_years is not None:
        conn.execute(insert(role_profile_experience).values(
            experience_req_id=uuid.uuid4(), profile_id=profile_id, minimum_years=data.minimum_years,
            relevant_experience_required=None, accepted_experience_types=None, job_ads_count=None))
    for name in data.certifications:
        conn.execute(insert(role_profile_certifications).values(
            certification_req_id=uuid.uuid4(), profile_id=profile_id, certification_name=name,
            issuing_organization=None, is_mandatory=True, job_ads_count=None, created_at=now))


def requirements_of(conn: Connection, vacancy_ids: list[uuid.UUID]) -> dict[uuid.UUID, dict]:
    """The current (not archived) profile of each vacancy: skills by importance, education, years, certificates."""
    result = {v: {"required": [], "preferred": [], "skills": [], "education": None, "minimum_years": None,
                  "certifications": []} for v in vacancy_ids}
    if not vacancy_ids:
        return result
    profiles = conn.execute(
        select(role_profiles.c.profile_id, role_profiles.c.vacancy_id, role_profiles.c.created_at)
        .where(role_profiles.c.profile_type == "VACANCY", role_profiles.c.vacancy_id.in_(vacancy_ids),
               role_profiles.c.profile_status != "ARCHIVED")
    ).all()
    current: dict = {}
    for p in sorted(profiles, key=lambda p: p.created_at):
        current[p.vacancy_id] = p.profile_id
    by_profile = {profile_id: result[vacancy_id] for vacancy_id, profile_id in current.items()}
    if not by_profile:
        return result
    r = role_profile_requirements.c
    for row in conn.execute(select(r.profile_id, r.standard_name, r.skill_type, r.importance, r.skill_id)
                            .where(r.profile_id.in_(by_profile))).all():
        item = by_profile[row.profile_id]
        item["preferred" if row.importance == "PREFERRED" else "required"].append(row.standard_name)
        item["skills"].append({"name": row.standard_name, "skill_type": row.skill_type,
                               "importance": row.importance or "REQUIRED", "skill_id": row.skill_id})
    e = role_profile_education.c
    for row in conn.execute(select(e.profile_id, e.qualification_level, e.completion_requirement)
                            .where(e.profile_id.in_(by_profile))).all():
        by_profile[row.profile_id]["education"] = _education_label(row.qualification_level, row.completion_requirement)
    x = role_profile_experience.c
    for row in conn.execute(select(x.profile_id, x.minimum_years).where(x.profile_id.in_(by_profile))).all():
        if row.minimum_years is not None:
            by_profile[row.profile_id]["minimum_years"] = int(row.minimum_years)
    c = role_profile_certifications.c
    for row in conn.execute(select(c.profile_id, c.certification_name).where(c.profile_id.in_(by_profile))).all():
        by_profile[row.profile_id]["certifications"].append(row.certification_name)
    return result


def _education_label(level: str, completion: str | None) -> str | None:
    for label, (code, done) in EDUCATION_OPTIONS.items():
        if code == level and done == completion:
            return label
    return EDUCATION_LABELS.get((level, completion))


def company_vacancies_list(conn: Connection, company: Row) -> list[dict]:
    rows = conn.execute(select(company_vacancies).where(company_vacancies.c.company_id == company.company_id)
                        .order_by(company_vacancies.c.created_at.desc())).all()
    reqs = requirements_of(conn, [r.vacancy_id for r in rows])
    apps = conn.execute(select(vacancy_applications.c.vacancy_id, vacancy_applications.c.status)
                        .where(vacancy_applications.c.vacancy_id.in_([r.vacancy_id for r in rows]))).all() if rows else []
    counts: dict = defaultdict(lambda: {"applicants": 0, "new_applicants": 0})
    for a in apps:
        counts[a.vacancy_id]["applicants"] += 1
        counts[a.vacancy_id]["new_applicants"] += a.status == "NEW"
    return [{**vacancy_dict(r, company, reqs[r.vacancy_id]), **counts[r.vacancy_id]} for r in rows]


def company_vacancy(conn: Connection, company: Row, vacancy_id: uuid.UUID) -> dict:
    row = _own_vacancy(conn, company.company_id, vacancy_id)
    return vacancy_dict(row, company, requirements_of(conn, [vacancy_id])[vacancy_id])


def vacancy_dict(row, company, reqs: dict) -> dict:
    return {
        "vacancy_id": row.vacancy_id, "title": row.job_title, "career_level": row.career_level,
        "employment_type": row.employment_type, "location": row.location, "description": row.description or "",
        "closing_date": row.closing_date, "apply_url": row.apply_url, "status": row.status,
        "state": vacancy_state(row.status, row.closing_date, company), "published_at": row.published_at,
        "created_at": row.created_at, "updated_at": row.updated_at,
        "company": {"company_id": company.company_id, "name": company.name, "sector": company.sector,
                    "city": company.city, "website": company.website},
        **reqs,
    }


def _live_clause():
    return and_(company_vacancies.c.status == "PUBLISHED", companies.c.verified.is_(True),
                (company_vacancies.c.closing_date.is_(None)) | (company_vacancies.c.closing_date >= today()))


def live_vacancies(conn: Connection, student_id: uuid.UUID | None) -> list[dict]:
    """Every live vacancy, newest first, with whether (and how) the student applied."""
    rows = conn.execute(
        select(company_vacancies, *[c.label(f"co_{c.name}") for c in companies.c])
        .join(companies, companies.c.company_id == company_vacancies.c.company_id)
        .where(_live_clause()).order_by(company_vacancies.c.published_at.desc())
    ).all()
    reqs = requirements_of(conn, [r.vacancy_id for r in rows])
    mine = _my_statuses(conn, student_id)
    out = []
    for r in rows:
        company = _company_from_prefixed(r)
        item = vacancy_dict(r, company, reqs[r.vacancy_id])
        item["application_status"] = mine.get(r.vacancy_id)
        out.append(item)
    return out


def live_vacancy(conn: Connection, vacancy_id: uuid.UUID, student_id: uuid.UUID | None) -> dict:
    row = conn.execute(
        select(company_vacancies, *[c.label(f"co_{c.name}") for c in companies.c])
        .join(companies, companies.c.company_id == company_vacancies.c.company_id)
        .where(_live_clause(), company_vacancies.c.vacancy_id == vacancy_id)
    ).first()
    if row is None:
        raise NotFound("This job isn't open any more")
    item = vacancy_dict(row, _company_from_prefixed(row), requirements_of(conn, [vacancy_id])[vacancy_id])
    item["application_status"] = _my_statuses(conn, student_id).get(vacancy_id)
    return item


@dataclass
class _Company:
    company_id: uuid.UUID
    name: str
    sector: str | None
    city: str | None
    website: str | None
    verified: bool
    rejected_at: datetime | None


def _company_from_prefixed(row) -> _Company:
    m = row._mapping
    return _Company(m["co_company_id"], m["co_name"], m["co_sector"], m["co_city"], m["co_website"],
                    bool(m["co_verified"]), m["co_rejected_at"])


def _my_statuses(conn: Connection, student_id: uuid.UUID | None) -> dict:
    if student_id is None:
        return {}
    return dict(conn.execute(select(vacancy_applications.c.vacancy_id, vacancy_applications.c.status)
                             .where(vacancy_applications.c.student_user_id == student_id)).all())


# --- applications ------------------------------------------------------------------------------------


@dataclass
class ApplicationInput:
    phone: str
    education: str | None
    note: str | None
    cv: tuple[str, str, bytes] | None  # (file name, content type, bytes); None: reuse the last CV


def apply(conn: Connection, vacancy_id: uuid.UUID, student_id: uuid.UUID, full_name: str, email: str,
          data: ApplicationInput, now: datetime) -> uuid.UUID:
    live_vacancy(conn, vacancy_id, None)  # NotFound unless students can apply
    if conn.execute(select(vacancy_applications.c.application_id).where(
            vacancy_applications.c.vacancy_id == vacancy_id,
            vacancy_applications.c.student_user_id == student_id)).first():
        raise Conflict("You have already applied for this job")
    cv = data.cv or last_cv(conn, student_id, with_content=True)
    if cv is None:
        raise ValueError("Add your CV as a PDF")
    application_id = uuid.uuid4()
    conn.execute(insert(vacancy_applications).values(
        application_id=application_id, vacancy_id=vacancy_id, student_user_id=student_id, full_name=full_name,
        email=email, phone=data.phone, education=data.education, note=data.note, status="NEW",
        consent_at=now, applied_at=now, updated_at=now))
    name, content_type, content = cv
    conn.execute(insert(application_cvs).values(application_id=application_id, file_name=name,
                                                content_type=content_type, size_bytes=len(content), content=content))
    return application_id


def last_cv(conn: Connection, student_id: uuid.UUID, with_content: bool = False):
    """The CV of the student's newest application: (name, type, bytes), or (name, size) without content."""
    cols = [application_cvs.c.file_name, application_cvs.c.content_type, application_cvs.c.size_bytes]
    if with_content:
        cols.append(application_cvs.c.content)
    row = conn.execute(
        select(*cols).join(vacancy_applications,
                           vacancy_applications.c.application_id == application_cvs.c.application_id)
        .where(vacancy_applications.c.student_user_id == student_id)
        .order_by(vacancy_applications.c.applied_at.desc()).limit(1)
    ).first()
    if row is None:
        return None
    return (row.file_name, row.content_type, bytes(row.content)) if with_content else (row.file_name, row.size_bytes)


def my_applications(conn: Connection, student_id: uuid.UUID) -> dict:
    a, v = vacancy_applications.c, company_vacancies.c
    rows = conn.execute(
        select(a.application_id, a.vacancy_id, a.status, a.applied_at, a.phone, a.education,
               v.job_title, v.location, v.status.label("vacancy_status"), v.closing_date,
               companies.c.company_id, companies.c.name.label("company_name"), companies.c.verified,
               companies.c.rejected_at, application_cvs.c.file_name, application_cvs.c.size_bytes)
        .join(company_vacancies, v.vacancy_id == a.vacancy_id)
        .join(companies, companies.c.company_id == v.company_id)
        .outerjoin(application_cvs, application_cvs.c.application_id == a.application_id)
        .where(a.student_user_id == student_id).order_by(a.applied_at.desc())
    ).all()
    items = [{
        "application_id": r.application_id, "vacancy_id": r.vacancy_id, "status": r.status, "applied_at": r.applied_at,
        "title": r.job_title, "location": r.location, "company_id": r.company_id, "company_name": r.company_name,
        "job_open": vacancy_state(r.vacancy_status, r.closing_date, r) == "LIVE",
        "cv_file_name": r.file_name,
    } for r in rows]
    newest = rows[0] if rows else None
    return {
        "applications": items,
        "last_cv": {"file_name": newest.file_name, "size_bytes": newest.size_bytes} if newest and newest.file_name else None,
        "last_phone": newest.phone if newest else None,
        "last_education": newest.education if newest else None,
    }


def withdraw(conn: Connection, student_id: uuid.UUID, application_id: uuid.UUID) -> None:
    own = conn.execute(select(vacancy_applications.c.application_id).where(
        vacancy_applications.c.application_id == application_id,
        vacancy_applications.c.student_user_id == student_id)).first()
    if own is None:
        raise NotFound("No such application")
    conn.execute(delete(application_cvs).where(application_cvs.c.application_id == application_id))
    conn.execute(delete(vacancy_applications).where(vacancy_applications.c.application_id == application_id))


def _company_application_query(company_id: uuid.UUID):
    a, v = vacancy_applications.c, company_vacancies.c
    return (
        select(a.application_id, a.vacancy_id, a.full_name, a.email, a.phone, a.education, a.note, a.status,
               a.applied_at, a.updated_at, v.job_title, application_cvs.c.file_name, application_cvs.c.size_bytes)
        .join(company_vacancies, v.vacancy_id == a.vacancy_id)
        .outerjoin(application_cvs, application_cvs.c.application_id == a.application_id)
        .where(v.company_id == company_id)
    )


def _application_dict(r) -> dict:
    return {
        "application_id": r.application_id, "vacancy_id": r.vacancy_id, "job_title": r.job_title,
        "full_name": r.full_name, "email": r.email, "phone": r.phone, "education": r.education, "note": r.note,
        "status": r.status, "applied_at": r.applied_at, "updated_at": r.updated_at,
        "cv_file_name": r.file_name, "cv_size_bytes": r.size_bytes,
    }


def company_applications(conn: Connection, company_id: uuid.UUID, vacancy_id: uuid.UUID | None = None,
                         status: str | None = None) -> list[dict]:
    query = _company_application_query(company_id)
    if vacancy_id:
        query = query.where(vacancy_applications.c.vacancy_id == vacancy_id)
    if status:
        query = query.where(vacancy_applications.c.status == status)
    return [_application_dict(r) for r in conn.execute(query.order_by(vacancy_applications.c.applied_at.desc())).all()]


def company_application(conn: Connection, company_id: uuid.UUID, application_id: uuid.UUID) -> dict:
    """One application. Reading it changes nothing: the portal marks it SEEN once the company has opened it."""
    row = conn.execute(_company_application_query(company_id)
                       .where(vacancy_applications.c.application_id == application_id)).first()
    if row is None:
        raise NotFound("No such application")
    return _application_dict(row)


def set_application_status(conn: Connection, company_id: uuid.UUID, application_id: uuid.UUID, status: str,
                           now: datetime) -> dict:
    """SEEN (opened), SHORTLISTED or NOT_SELECTED; the student sees each. SEEN never undoes a decision."""
    current = company_application(conn, company_id, application_id)
    if not (status == "SEEN" and current["status"] != "NEW"):
        conn.execute(update(vacancy_applications).where(vacancy_applications.c.application_id == application_id)
                     .values(status=status, updated_at=now))
    return company_application(conn, company_id, application_id)


def application_cv(conn: Connection, company_id: uuid.UUID, application_id: uuid.UUID) -> tuple[str, str, bytes]:
    row = conn.execute(
        select(application_cvs.c.file_name, application_cvs.c.content_type, application_cvs.c.content)
        .join(vacancy_applications, vacancy_applications.c.application_id == application_cvs.c.application_id)
        .join(company_vacancies, company_vacancies.c.vacancy_id == vacancy_applications.c.vacancy_id)
        .where(application_cvs.c.application_id == application_id, company_vacancies.c.company_id == company_id)
    ).first()
    if row is None:
        raise NotFound("No such CV")
    return row.file_name, row.content_type, bytes(row.content)


def company_counts(conn: Connection, company_id: uuid.UUID) -> dict:
    a = vacancy_applications.c
    rows = conn.execute(select(a.status, func.count()).join(company_vacancies, company_vacancies.c.vacancy_id == a.vacancy_id)
                        .where(company_vacancies.c.company_id == company_id).group_by(a.status)).all()
    by_status = dict(rows)
    return {"applicants": sum(by_status.values()), "new_applicants": by_status.get("NEW", 0)}
