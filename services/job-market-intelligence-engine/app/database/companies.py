"""Company job posts: the companies, their vacancies and the students' applications, as C01 writes them.

On the shared database they are created by infrastructure/neon/setup.sql (job_market schema), with its
CHECK and UNIQUE rules; these definitions only describe the columns, so C01 can read and write them and
the tests can create them on SQLite. They share the metadata of the contract tables (app/database/contract.py),
because a vacancy's skills are a VACANCY role profile there.
"""

from __future__ import annotations

from sqlalchemy import (
    Boolean,
    Column,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    LargeBinary,
    String,
    Table,
    Text,
    UniqueConstraint,
    Uuid,
)

from app.database.contract import metadata

companies = Table(
    "companies", metadata,
    Column("company_id", Uuid, primary_key=True),
    Column("name", Text, nullable=False),
    Column("website", Text),
    Column("sector", String(50)),
    Column("description", Text),
    Column("verified", Boolean, nullable=False, default=False),
    Column("created_by_user_id", Uuid),
    Column("created_at", DateTime(timezone=True), nullable=False),
    # Added for company job posts (28 Nov 2026)
    Column("city", Text),
    Column("contact_name", Text),  # the account holder, copied from auth.users when the company signs up
    Column("contact_email", Text),
    Column("verified_at", DateTime(timezone=True)),
    Column("rejected_at", DateTime(timezone=True)),  # set: an admin rejected the company
    Column("reviewed_by_user_id", Uuid),
)

company_users = Table(
    "company_users", metadata,
    Column("company_id", Uuid, ForeignKey("companies.company_id"), primary_key=True),
    Column("user_id", Uuid, primary_key=True),
    Column("added_at", DateTime(timezone=True), nullable=False),
)

company_vacancies = Table(
    "company_vacancies", metadata,
    Column("vacancy_id", Uuid, primary_key=True),
    Column("company_id", Uuid, ForeignKey("companies.company_id"), nullable=False),
    Column("posted_by_user_id", Uuid, nullable=False),
    Column("job_title", Text, nullable=False),
    Column("role_id", String(50)),
    Column("candidate_role_id", Uuid),
    Column("career_level", String(30)),
    Column("employment_type", String(30)),
    Column("location", Text),
    Column("description", Text),
    Column("closing_date", Date),
    Column("status", String(20), nullable=False),  # DRAFT | PUBLISHED | CLOSED
    Column("published_at", DateTime(timezone=True)),
    Column("created_at", DateTime(timezone=True), nullable=False),
    Column("updated_at", DateTime(timezone=True), nullable=False),
    Column("apply_url", Text),  # the company's own application page (web link or email), optional
)

vacancy_applications = Table(
    "vacancy_applications", metadata,
    Column("application_id", Uuid, primary_key=True),
    Column("vacancy_id", Uuid, ForeignKey("company_vacancies.vacancy_id", ondelete="CASCADE"), nullable=False),
    Column("student_user_id", Uuid, nullable=False),
    # What the student agreed to share, copied when they applied
    Column("full_name", Text, nullable=False),
    Column("email", Text, nullable=False),
    Column("phone", String(40), nullable=False),
    Column("education", Text),
    Column("note", Text),
    Column("status", String(20), nullable=False),  # NEW | SEEN | SHORTLISTED | NOT_SELECTED
    Column("consent_at", DateTime(timezone=True), nullable=False),
    Column("applied_at", DateTime(timezone=True), nullable=False),
    Column("updated_at", DateTime(timezone=True), nullable=False),
    UniqueConstraint("vacancy_id", "student_user_id", name="uq_vacancy_applications_student"),
)

application_cvs = Table(
    "application_cvs", metadata,
    Column("application_id", Uuid, ForeignKey("vacancy_applications.application_id", ondelete="CASCADE"),
           primary_key=True),
    Column("file_name", Text, nullable=False),
    Column("content_type", String(100), nullable=False),
    Column("size_bytes", Integer, nullable=False),
    Column("content", LargeBinary, nullable=False),
)

COMPANY_TABLES = (companies, company_users, company_vacancies, vacancy_applications, application_cvs)
