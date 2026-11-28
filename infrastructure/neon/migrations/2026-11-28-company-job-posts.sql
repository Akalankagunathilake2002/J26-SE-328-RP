-- Company job posts (28 Nov 2026): companies post jobs, an admin verifies each company, students apply on
-- Skillaro and the company sees each applicant's name, contact details, education, CV and note.
-- Owner: C01 (job_market_svc). The code is services/job-market-intelligence-engine/app/companies/.
--
-- setup.sql runs this file. To add it to a database made before 28 Nov 2026, run it as the Neon owner:
--   psql "$NEON_OWNER_URL" -X -f infrastructure/neon/migrations/2026-11-28-company-job-posts.sql
-- Safe to run again: everything is IF NOT EXISTS.

\set ON_ERROR_STOP on
SET ROLE job_market_svc;

-- Who signed the company up, and the admin's decision. verified stays the contract's flag; rejected_at set means
-- an admin rejected the company (its jobs stay hidden). Neither set: waiting for an admin.
ALTER TABLE job_market.companies
    ADD COLUMN IF NOT EXISTS city text,
    ADD COLUMN IF NOT EXISTS contact_name text,
    ADD COLUMN IF NOT EXISTS contact_email text,
    ADD COLUMN IF NOT EXISTS verified_at timestamptz,
    ADD COLUMN IF NOT EXISTS rejected_at timestamptz,
    ADD COLUMN IF NOT EXISTS reviewed_by_user_id uuid;

-- The company's own application page (a web link or an email), optional: students see it after applying.
ALTER TABLE job_market.company_vacancies
    ADD COLUMN IF NOT EXISTS apply_url text;

DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'chk_companies_review') THEN
        ALTER TABLE job_market.companies
            ADD CONSTRAINT chk_companies_review CHECK (NOT (verified AND rejected_at IS NOT NULL));
    END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'chk_company_vacancies_employment_type') THEN
        ALTER TABLE job_market.company_vacancies
            ADD CONSTRAINT chk_company_vacancies_employment_type
            CHECK (employment_type IS NULL OR employment_type IN ('FULL_TIME', 'PART_TIME', 'CONTRACT', 'INTERNSHIP'));
    END IF;
END $$;

-- One company per company account.
CREATE UNIQUE INDEX IF NOT EXISTS uq_company_users_user ON job_market.company_users (user_id);
CREATE INDEX IF NOT EXISTS idx_company_vacancies_company ON job_market.company_vacancies (company_id);

-- A student's application: a copy of what they agreed to share when they applied. Withdrawing deletes it.
CREATE TABLE IF NOT EXISTS job_market.vacancy_applications (
    application_id uuid NOT NULL,
    vacancy_id uuid NOT NULL,
    student_user_id uuid NOT NULL,
    full_name text NOT NULL,
    email text NOT NULL,
    phone varchar(40) NOT NULL,
    education text,
    note text,
    status varchar(20) DEFAULT 'NEW' NOT NULL,
    consent_at timestamptz NOT NULL,
    applied_at timestamptz DEFAULT now() NOT NULL,
    updated_at timestamptz DEFAULT now() NOT NULL,
    CONSTRAINT pk_vacancy_applications PRIMARY KEY (application_id),
    CONSTRAINT fk_vacancy_applications_vacancy_id FOREIGN KEY (vacancy_id) REFERENCES job_market.company_vacancies (vacancy_id) ON DELETE CASCADE,
    CONSTRAINT uq_vacancy_applications_student UNIQUE (vacancy_id, student_user_id),
    CONSTRAINT chk_vacancy_applications_status CHECK (status IN ('NEW', 'SEEN', 'SHORTLISTED', 'NOT_SELECTED')),
    CONSTRAINT chk_vacancy_applications_note CHECK (note IS NULL OR length(note) <= 1000)
);
CREATE INDEX IF NOT EXISTS idx_vacancy_applications_student ON job_market.vacancy_applications (student_user_id);

-- The applicant's CV (a PDF up to 2 MB), apart from the application so lists never load it.
CREATE TABLE IF NOT EXISTS job_market.application_cvs (
    application_id uuid NOT NULL,
    file_name text NOT NULL,
    content_type varchar(100) NOT NULL,
    size_bytes integer NOT NULL,
    content bytea NOT NULL,
    CONSTRAINT pk_application_cvs PRIMARY KEY (application_id),
    CONSTRAINT fk_application_cvs_application_id FOREIGN KEY (application_id) REFERENCES job_market.vacancy_applications (application_id) ON DELETE CASCADE,
    CONSTRAINT chk_application_cvs_type CHECK (content_type = 'application/pdf'),
    CONSTRAINT chk_application_cvs_size CHECK (size_bytes > 0 AND size_bytes <= 2097152 AND octet_length(content) = size_bytes)
);

RESET ROLE;
