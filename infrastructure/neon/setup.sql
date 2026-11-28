-- Skillaro shared database on Neon: database `skillaro`, one schema per component.
-- Built from the team's Skillaro_DB_Contract_v2 (24 Nov 2026). Generated; see infrastructure/neon/README.md.
-- Run it as the Neon owner role with infrastructure/neon/setup.sh (it passes the login passwords).
-- Safe to run again: everything is IF NOT EXISTS, and passwords are reset to the values in infrastructure/.env.

\set ON_ERROR_STOP on
\set QUIET on

\getenv auth_pw NEON_AUTH_PASSWORD
\getenv ssks_pw NEON_SSKS_PASSWORD
\getenv job_market_pw NEON_JOB_MARKET_PASSWORD
\getenv skill_profile_pw NEON_SKILL_PROFILE_PASSWORD
\getenv readiness_pw NEON_READINESS_PASSWORD
\getenv learning_pw NEON_LEARNING_PASSWORD
\getenv interview_pw NEON_INTERVIEW_PASSWORD

-- The owner can switch to the roles it creates (needed to create each schema's tables as its own login).
SET createrole_self_grant = 'set, inherit';

CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
REVOKE CREATE ON SCHEMA public FROM PUBLIC;

-- One login per service
SELECT format('CREATE ROLE %I LOGIN PASSWORD %L', r, p)
FROM (VALUES ('auth_svc', :'auth_pw'),
             ('ssks_svc', :'ssks_pw'),
             ('job_market_svc', :'job_market_pw'),
             ('skill_profile_svc', :'skill_profile_pw'),
             ('readiness_svc', :'readiness_pw'),
             ('learning_svc', :'learning_pw'),
             ('interview_svc', :'interview_pw')) AS v(r, p)
WHERE NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = r) \gexec

SELECT format('ALTER ROLE %I WITH LOGIN PASSWORD %L', r, p)
FROM (VALUES ('auth_svc', :'auth_pw'),
             ('ssks_svc', :'ssks_pw'),
             ('job_market_svc', :'job_market_pw'),
             ('skill_profile_svc', :'skill_profile_pw'),
             ('readiness_svc', :'readiness_pw'),
             ('learning_svc', :'learning_pw'),
             ('interview_svc', :'interview_pw')) AS v(r, p) \gexec

CREATE SCHEMA IF NOT EXISTS auth AUTHORIZATION auth_svc;
ALTER ROLE auth_svc SET search_path = auth, public;
CREATE SCHEMA IF NOT EXISTS ssks AUTHORIZATION ssks_svc;
ALTER ROLE ssks_svc SET search_path = ssks, public;
CREATE SCHEMA IF NOT EXISTS job_market AUTHORIZATION job_market_svc;
ALTER ROLE job_market_svc SET search_path = job_market, public;
CREATE SCHEMA IF NOT EXISTS skill_profile AUTHORIZATION skill_profile_svc;
ALTER ROLE skill_profile_svc SET search_path = skill_profile, public;
CREATE SCHEMA IF NOT EXISTS readiness AUTHORIZATION readiness_svc;
ALTER ROLE readiness_svc SET search_path = readiness, public;
CREATE SCHEMA IF NOT EXISTS learning AUTHORIZATION learning_svc;
ALTER ROLE learning_svc SET search_path = learning, public;
CREATE SCHEMA IF NOT EXISTS interview AUTHORIZATION interview_svc;
ALTER ROLE interview_svc SET search_path = interview, public;

-- ================================================================ auth  (login auth_svc)
SET ROLE auth_svc;
CREATE TABLE IF NOT EXISTS auth.users (
    id uuid NOT NULL,
    full_name varchar(120) NOT NULL,
    email varchar(254) NOT NULL UNIQUE,
    password_hash varchar(255) NOT NULL,
    role varchar(20) NOT NULL,
    created_at timestamptz DEFAULT now() NOT NULL,
    CONSTRAINT pk_users PRIMARY KEY (id)
);

RESET ROLE;

-- ================================================================ ssks  (login ssks_svc)
SET ROLE ssks_svc;
CREATE TABLE IF NOT EXISTS ssks.skills (
    skill_id varchar(50) NOT NULL,
    preferred_name varchar(255) NOT NULL,
    description text,
    skill_type varchar(100) NOT NULL,
    skill_nature varchar(50),
    status varchar(50) NOT NULL,
    created_at timestamptz DEFAULT now() NOT NULL,
    updated_at timestamptz DEFAULT now() NOT NULL,
    CONSTRAINT pk_skills PRIMARY KEY (skill_id)
);

CREATE TABLE IF NOT EXISTS ssks.roles (
    role_id varchar(50) NOT NULL,
    preferred_name varchar(255) NOT NULL,
    description text,
    status varchar(50) NOT NULL,
    created_at timestamptz DEFAULT now() NOT NULL,
    updated_at timestamptz DEFAULT now() NOT NULL,
    CONSTRAINT pk_roles PRIMARY KEY (role_id)
);

CREATE TABLE IF NOT EXISTS ssks.domains (
    domain_id varchar(50) NOT NULL,
    name varchar(255) NOT NULL,
    code varchar(50) NOT NULL UNIQUE,
    description text,
    status varchar(50) NOT NULL,
    CONSTRAINT pk_domains PRIMARY KEY (domain_id)
);

CREATE TABLE IF NOT EXISTS ssks.skill_domains (
    skill_id varchar(50) NOT NULL,
    domain_id varchar(50) NOT NULL,
    CONSTRAINT pk_skill_domains PRIMARY KEY (skill_id, domain_id),
    CONSTRAINT fk_skill_domains_skill_id FOREIGN KEY (skill_id) REFERENCES ssks.skills (skill_id),
    CONSTRAINT fk_skill_domains_domain_id FOREIGN KEY (domain_id) REFERENCES ssks.domains (domain_id)
);

CREATE TABLE IF NOT EXISTS ssks.role_domains (
    role_id varchar(50) NOT NULL,
    domain_id varchar(50) NOT NULL,
    CONSTRAINT pk_role_domains PRIMARY KEY (role_id, domain_id),
    CONSTRAINT fk_role_domains_role_id FOREIGN KEY (role_id) REFERENCES ssks.roles (role_id),
    CONSTRAINT fk_role_domains_domain_id FOREIGN KEY (domain_id) REFERENCES ssks.domains (domain_id)
);

CREATE TABLE IF NOT EXISTS ssks.candidate_entities (
    candidate_entity_id uuid NOT NULL,
    entity_type varchar(20) NOT NULL,
    submitted_name varchar(255) NOT NULL,
    normalized_name varchar(255) NOT NULL,
    description text,
    proposed_skill_type varchar(100),
    proposed_skill_nature varchar(50),
    source_component varchar(50),
    source_reference varchar(255),
    review_status varchar(50) NOT NULL,
    review_note text,
    matched_entity_id varchar(50),
    created_at timestamptz DEFAULT now() NOT NULL,
    reviewed_at timestamptz,
    reviewed_by uuid,
    CONSTRAINT pk_candidate_entities PRIMARY KEY (candidate_entity_id)
);

CREATE TABLE IF NOT EXISTS ssks.knowledge_sources (
    source_id uuid NOT NULL,
    source_code varchar(100) NOT NULL UNIQUE,
    source_name varchar(255) NOT NULL,
    source_version varchar(100) NOT NULL,
    last_synced_at timestamptz,
    CONSTRAINT pk_knowledge_sources PRIMARY KEY (source_id)
);

CREATE TABLE IF NOT EXISTS ssks.skill_external_ids (
    external_id uuid NOT NULL,
    skill_id varchar(50) NOT NULL,
    source_id uuid NOT NULL,
    external_identifier varchar(255) NOT NULL,
    CONSTRAINT pk_skill_external_ids PRIMARY KEY (external_id),
    CONSTRAINT fk_skill_external_ids_skill_id FOREIGN KEY (skill_id) REFERENCES ssks.skills (skill_id),
    CONSTRAINT fk_skill_external_ids_source_id FOREIGN KEY (source_id) REFERENCES ssks.knowledge_sources (source_id)
);

CREATE TABLE IF NOT EXISTS ssks.role_external_ids (
    external_id uuid NOT NULL,
    role_id varchar(50) NOT NULL,
    source_id uuid NOT NULL,
    external_identifier varchar(255) NOT NULL,
    CONSTRAINT pk_role_external_ids PRIMARY KEY (external_id),
    CONSTRAINT fk_role_external_ids_role_id FOREIGN KEY (role_id) REFERENCES ssks.roles (role_id),
    CONSTRAINT fk_role_external_ids_source_id FOREIGN KEY (source_id) REFERENCES ssks.knowledge_sources (source_id)
);

CREATE TABLE IF NOT EXISTS ssks.skill_embeddings (
    skill_id varchar(50) NOT NULL,
    embedding_model varchar(150) NOT NULL,
    embedding_dimension smallint DEFAULT 384 NOT NULL,
    embedding_text_hash char(64) NOT NULL,
    embedding vector(384) NOT NULL,
    generated_at timestamptz DEFAULT now() NOT NULL,
    CONSTRAINT pk_skill_embeddings PRIMARY KEY (skill_id, embedding_model),
    CONSTRAINT fk_skill_embeddings_skill_id FOREIGN KEY (skill_id) REFERENCES ssks.skills (skill_id) ON DELETE CASCADE,
    CONSTRAINT chk_skill_embedding_dimension CHECK (embedding_dimension = 384)
);

CREATE TABLE IF NOT EXISTS ssks.skill_aliases (
    alias_id uuid NOT NULL,
    skill_id varchar(50) NOT NULL,
    alias_text varchar(255) NOT NULL,
    normalized_alias varchar(255) NOT NULL,
    source_id uuid,
    verification_status varchar(50) NOT NULL,
    CONSTRAINT pk_skill_aliases PRIMARY KEY (alias_id),
    CONSTRAINT fk_skill_aliases_skill_id FOREIGN KEY (skill_id) REFERENCES ssks.skills (skill_id),
    CONSTRAINT fk_skill_aliases_source_id FOREIGN KEY (source_id) REFERENCES ssks.knowledge_sources (source_id)
);

CREATE TABLE IF NOT EXISTS ssks.role_aliases (
    alias_id uuid NOT NULL,
    role_id varchar(50) NOT NULL,
    alias_text varchar(255) NOT NULL,
    normalized_alias varchar(255) NOT NULL,
    source_id uuid,
    verification_status varchar(50) NOT NULL,
    CONSTRAINT pk_role_aliases PRIMARY KEY (alias_id),
    CONSTRAINT fk_role_aliases_role_id FOREIGN KEY (role_id) REFERENCES ssks.roles (role_id),
    CONSTRAINT fk_role_aliases_source_id FOREIGN KEY (source_id) REFERENCES ssks.knowledge_sources (source_id)
);

CREATE TABLE IF NOT EXISTS ssks.skill_relationships (
    relationship_id uuid NOT NULL,
    source_skill_id varchar(50) NOT NULL,
    target_skill_id varchar(50) NOT NULL,
    relationship_type varchar(50) NOT NULL,
    verification_status varchar(50) DEFAULT 'VERIFIED' NOT NULL,
    source_id uuid,
    evidence_note text,
    evidence_description text,
    evidence_url varchar(500),
    reviewed_by uuid,
    created_at timestamptz DEFAULT now() NOT NULL,
    updated_at timestamptz DEFAULT now() NOT NULL,
    CONSTRAINT pk_skill_relationships PRIMARY KEY (relationship_id),
    CONSTRAINT fk_skill_relationships_source_skill_id FOREIGN KEY (source_skill_id) REFERENCES ssks.skills (skill_id),
    CONSTRAINT fk_skill_relationships_target_skill_id FOREIGN KEY (target_skill_id) REFERENCES ssks.skills (skill_id),
    CONSTRAINT fk_skill_relationships_source_id FOREIGN KEY (source_id) REFERENCES ssks.knowledge_sources (source_id),
    CONSTRAINT chk_skill_relationships_type CHECK (relationship_type IN ('EQUIVALENT_TO', 'BROADER_THAN', 'NARROWER_THAN', 'PART_OF', 'PREREQUISITE_OF', 'RELATED_TO')),
    CONSTRAINT chk_skill_relationships_verification_status CHECK (verification_status IN ('VERIFIED', 'UNVERIFIED')),
    CONSTRAINT chk_skill_relationships_no_self_reference CHECK (source_skill_id <> target_skill_id),
    CONSTRAINT uq_skill_relationships_directional UNIQUE (source_skill_id, target_skill_id, relationship_type)
);

CREATE TABLE IF NOT EXISTS ssks.candidate_skill_relationships (
    candidate_relationship_id uuid NOT NULL,
    source_skill_id varchar(50) NOT NULL,
    target_skill_id varchar(50) NOT NULL,
    proposed_relationship_type varchar(50) NOT NULL,
    confidence_score double precision,
    review_status varchar(50) NOT NULL,
    source_id uuid,
    review_note text,
    evidence_description text,
    evidence_url varchar(500),
    reviewed_by varchar(100),
    canonical_relationship_id uuid,
    created_at timestamptz DEFAULT now() NOT NULL,
    reviewed_at timestamptz,
    CONSTRAINT pk_candidate_skill_relationships PRIMARY KEY (candidate_relationship_id),
    CONSTRAINT fk_candidate_skill_relationships_source_skill_id FOREIGN KEY (source_skill_id) REFERENCES ssks.skills (skill_id),
    CONSTRAINT fk_candidate_skill_relationships_target_skill_id FOREIGN KEY (target_skill_id) REFERENCES ssks.skills (skill_id),
    CONSTRAINT fk_candidate_skill_relationships_source_id FOREIGN KEY (source_id) REFERENCES ssks.knowledge_sources (source_id),
    CONSTRAINT fk_candidate_skill_relationships_canonical_relationship_id FOREIGN KEY (canonical_relationship_id) REFERENCES ssks.skill_relationships (relationship_id)
);

CREATE INDEX IF NOT EXISTS idx_skill_embeddings_model ON ssks.skill_embeddings (embedding_model);
GRANT USAGE ON SCHEMA ssks TO readiness_svc;
GRANT SELECT ON ssks.skills, ssks.roles, ssks.domains, ssks.skill_aliases, ssks.role_aliases, ssks.skill_domains, ssks.role_domains, ssks.skill_relationships, ssks.skill_embeddings TO readiness_svc;
RESET ROLE;

-- ================================================================ job_market  (login job_market_svc)
SET ROLE job_market_svc;
CREATE TABLE IF NOT EXISTS job_market.job_ads (
    site varchar(50) NOT NULL,
    job_id varchar(50) NOT NULL,
    url text NOT NULL,
    job_title text,
    company text,
    location text,
    posted_date date,
    closing_date date,
    employment_type text,
    experience_level text,
    salary_text text,
    description_text text,
    requirements_text text,
    is_image_ad boolean NOT NULL,
    status varchar(20) NOT NULL,
    collected_at timestamptz,
    last_seen_at timestamptz,
    status_changed_at timestamptz,
    role text,
    role_mapped boolean,
    seniority text,
    has_text boolean,
    flags text,
    loaded_at timestamptz NOT NULL,
    CONSTRAINT pk_job_ads PRIMARY KEY (site, job_id)
);

CREATE TABLE IF NOT EXISTS job_market.job_ad_sectors (
    site varchar(50) NOT NULL,
    job_id varchar(50) NOT NULL,
    sector varchar(50) NOT NULL,
    CONSTRAINT pk_job_ad_sectors PRIMARY KEY (site, job_id, sector),
    CONSTRAINT fk_job_ad_sectors_site_job_id FOREIGN KEY (site, job_id) REFERENCES job_market.job_ads (site, job_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS job_market.job_ad_skills (
    id integer GENERATED BY DEFAULT AS IDENTITY NOT NULL,
    site varchar(50) NOT NULL,
    job_id varchar(50) NOT NULL,
    extractor varchar(20) NOT NULL,
    raw_text text NOT NULL,
    start_char integer NOT NULL,
    end_char integer NOT NULL,
    label text,
    lexicon_skill text,
    counted_as text,
    ssk_id varchar(50),
    ssks_name text,
    match_type varchar(20) NOT NULL,
    CONSTRAINT pk_job_ad_skills PRIMARY KEY (id),
    CONSTRAINT fk_job_ad_skills_site_job_id FOREIGN KEY (site, job_id) REFERENCES job_market.job_ads (site, job_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS job_market.job_ad_status_history (
    site varchar(50) NOT NULL,
    job_id varchar(50) NOT NULL,
    changed_at timestamptz NOT NULL,
    status varchar(20) NOT NULL,
    CONSTRAINT pk_job_ad_status_history PRIMARY KEY (site, job_id, changed_at, status),
    CONSTRAINT fk_job_ad_status_history_site_job_id FOREIGN KEY (site, job_id) REFERENCES job_market.job_ads (site, job_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS job_market.sync_runs (
    site varchar(50) NOT NULL,
    synced_at timestamptz NOT NULL,
    live_on_homepage integer,
    listed integer,
    new_ads integer,
    active integer,
    expired integer,
    removed integer,
    reactivated integer,
    unconfirmed integer,
    CONSTRAINT pk_sync_runs PRIMARY KEY (site, synced_at)
);

CREATE TABLE IF NOT EXISTS job_market.companies (
    company_id uuid NOT NULL,
    name text NOT NULL,
    website text,
    sector varchar(50),
    description text,
    verified boolean DEFAULT false NOT NULL,
    created_by_user_id uuid,
    created_at timestamptz DEFAULT now() NOT NULL,
    CONSTRAINT pk_companies PRIMARY KEY (company_id)
);

CREATE TABLE IF NOT EXISTS job_market.company_users (
    company_id uuid NOT NULL,
    user_id uuid NOT NULL,
    added_at timestamptz DEFAULT now() NOT NULL,
    CONSTRAINT pk_company_users PRIMARY KEY (company_id, user_id),
    CONSTRAINT fk_company_users_company_id FOREIGN KEY (company_id) REFERENCES job_market.companies (company_id)
);

CREATE TABLE IF NOT EXISTS job_market.company_vacancies (
    vacancy_id uuid NOT NULL,
    company_id uuid NOT NULL,
    posted_by_user_id uuid NOT NULL,
    job_title text NOT NULL,
    role_id varchar(50),
    candidate_role_id uuid,
    career_level varchar(30),
    employment_type varchar(30),
    location text,
    description text,
    closing_date date,
    status varchar(20) NOT NULL,
    published_at timestamptz,
    created_at timestamptz DEFAULT now() NOT NULL,
    updated_at timestamptz DEFAULT now() NOT NULL,
    CONSTRAINT pk_company_vacancies PRIMARY KEY (vacancy_id),
    CONSTRAINT fk_company_vacancies_company_id FOREIGN KEY (company_id) REFERENCES job_market.companies (company_id),
    CONSTRAINT chk_company_vacancies_status CHECK (status IN ('DRAFT', 'PUBLISHED', 'CLOSED')),
    CONSTRAINT chk_company_vacancies_career_level CHECK (career_level IS NULL OR career_level IN ('INTERN', 'TRAINEE', 'JUNIOR', 'MID_LEVEL', 'SENIOR', 'LEAD', 'PRINCIPAL', 'EXECUTIVE')),
    CONSTRAINT chk_company_vacancies_role_ids CHECK (role_id IS NULL OR candidate_role_id IS NULL)
);

CREATE TABLE IF NOT EXISTS job_market.role_profiles (
    profile_id uuid NOT NULL,
    profile_type varchar(10) NOT NULL,
    vacancy_id uuid,
    role_id varchar(50),
    candidate_role_id uuid,
    primary_observed_title text NOT NULL,
    observed_titles text[],
    mapping_status varchar(50) NOT NULL,
    profile_status varchar(20) NOT NULL,
    profile_version varchar(40) NOT NULL,
    career_level varchar(30),
    domain_id varchar(50),
    sector varchar(50),
    job_posting_count integer,
    ads_with_text integer,
    observation_period_from date,
    observation_period_to date,
    published_at timestamptz,
    created_at timestamptz DEFAULT now() NOT NULL,
    CONSTRAINT pk_role_profiles PRIMARY KEY (profile_id),
    CONSTRAINT fk_role_profiles_vacancy_id FOREIGN KEY (vacancy_id) REFERENCES job_market.company_vacancies (vacancy_id),
    CONSTRAINT chk_role_profiles_type CHECK (profile_type IN ('ROLE', 'VACANCY')),
    CONSTRAINT chk_role_profiles_status CHECK (profile_status IN ('DRAFT', 'PUBLISHED', 'ARCHIVED')),
    CONSTRAINT chk_role_profiles_career_level CHECK (career_level IS NULL OR career_level IN ('INTERN', 'TRAINEE', 'JUNIOR', 'MID_LEVEL', 'SENIOR', 'LEAD', 'PRINCIPAL', 'EXECUTIVE')),
    CONSTRAINT chk_role_profiles_target CHECK ((profile_type = 'ROLE' AND vacancy_id IS NULL AND career_level IS NOT NULL AND (role_id IS NULL) <> (candidate_role_id IS NULL)) OR (profile_type = 'VACANCY' AND vacancy_id IS NOT NULL AND (role_id IS NULL OR candidate_role_id IS NULL))),
    CONSTRAINT chk_role_profiles_mapping CHECK ((mapping_status = 'VERIFIED' AND role_id IS NOT NULL AND candidate_role_id IS NULL) OR (mapping_status = 'CANDIDATE' AND role_id IS NULL AND candidate_role_id IS NOT NULL) OR (mapping_status = 'UNMAPPED' AND role_id IS NULL AND candidate_role_id IS NULL)),
    CONSTRAINT chk_role_profiles_period CHECK (observation_period_from IS NULL OR observation_period_to IS NULL OR observation_period_from <= observation_period_to)
);

CREATE TABLE IF NOT EXISTS job_market.role_profile_requirements (
    requirement_id uuid NOT NULL,
    profile_id uuid NOT NULL,
    skill_id varchar(50),
    candidate_skill_id uuid,
    standard_name text NOT NULL,
    primary_observed_term text,
    observed_terms text[],
    mapping_status varchar(50) NOT NULL,
    skill_type varchar(50) NOT NULL,
    importance varchar(20),
    demand_weight numeric(5,4) NOT NULL,
    demand_frequency numeric(5,4),
    job_ads_containing_skill integer,
    required_proficiency_level varchar(20),
    required_proficiency_score numeric(5,4),
    CONSTRAINT pk_role_profile_requirements PRIMARY KEY (requirement_id),
    CONSTRAINT fk_role_profile_requirements_profile_id FOREIGN KEY (profile_id) REFERENCES job_market.role_profiles (profile_id) ON DELETE CASCADE,
    CONSTRAINT chk_rpr_mapping CHECK ((mapping_status = 'VERIFIED' AND skill_id IS NOT NULL AND candidate_skill_id IS NULL) OR (mapping_status = 'CANDIDATE' AND skill_id IS NULL AND candidate_skill_id IS NOT NULL) OR (mapping_status = 'UNMAPPED' AND skill_id IS NULL AND candidate_skill_id IS NULL)),
    CONSTRAINT chk_rpr_skill_type CHECK (skill_type IN ('TECHNICAL', 'BEHAVIOURAL')),
    CONSTRAINT chk_rpr_importance CHECK (importance IS NULL OR importance IN ('REQUIRED', 'PREFERRED')),
    CONSTRAINT chk_rpr_proficiency_level CHECK (required_proficiency_level IS NULL OR required_proficiency_level IN ('BEGINNER', 'INTERMEDIATE', 'ADVANCED')),
    CONSTRAINT chk_rpr_unit_values CHECK (demand_weight BETWEEN 0 AND 1 AND (demand_frequency IS NULL OR demand_frequency BETWEEN 0 AND 1) AND (required_proficiency_score IS NULL OR required_proficiency_score BETWEEN 0 AND 1)),
    CONSTRAINT chk_rpr_counts CHECK (job_ads_containing_skill IS NULL OR job_ads_containing_skill >= 0)
);

CREATE TABLE IF NOT EXISTS job_market.role_profile_education (
    education_req_id uuid NOT NULL,
    profile_id uuid NOT NULL,
    qualification_level varchar(40) NOT NULL,
    accepted_fields text[],
    completion_requirement varchar(30),
    is_mandatory boolean,
    job_ads_count integer,
    CONSTRAINT pk_role_profile_education PRIMARY KEY (education_req_id),
    CONSTRAINT fk_role_profile_education_profile_id FOREIGN KEY (profile_id) REFERENCES job_market.role_profiles (profile_id) ON DELETE CASCADE,
    CONSTRAINT chk_rpe_completion CHECK (completion_requirement IS NULL OR completion_requirement IN ('COMPLETED', 'IN_PROGRESS', 'EITHER'))
);

CREATE TABLE IF NOT EXISTS job_market.role_profile_experience (
    experience_req_id uuid NOT NULL,
    profile_id uuid NOT NULL,
    minimum_years numeric(4,1),
    relevant_experience_required boolean,
    accepted_experience_types text[],
    job_ads_count integer,
    CONSTRAINT pk_role_profile_experience PRIMARY KEY (experience_req_id),
    CONSTRAINT fk_role_profile_experience_profile_id FOREIGN KEY (profile_id) REFERENCES job_market.role_profiles (profile_id) ON DELETE CASCADE,
    CONSTRAINT chk_rpx_minimum_years CHECK (minimum_years IS NULL OR minimum_years >= 0),
    CONSTRAINT chk_rpx_types CHECK (accepted_experience_types IS NULL OR accepted_experience_types <@ ARRAY['FULL_TIME_EMPLOYMENT', 'PART_TIME_EMPLOYMENT', 'INTERNSHIP', 'APPRENTICESHIP', 'FREELANCE', 'SELF_EMPLOYMENT', 'VOLUNTEERING', 'CONTRACT']::text[])
);

CREATE TABLE IF NOT EXISTS job_market.role_profile_certifications (
    certification_req_id uuid NOT NULL,
    profile_id uuid NOT NULL,
    certification_name text NOT NULL,
    issuing_organization text,
    is_mandatory boolean,
    job_ads_count integer,
    created_at timestamptz DEFAULT now() NOT NULL,
    CONSTRAINT pk_role_profile_certifications PRIMARY KEY (certification_req_id),
    CONSTRAINT fk_role_profile_certifications_profile_id FOREIGN KEY (profile_id) REFERENCES job_market.role_profiles (profile_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS job_market.requirement_evidence (
    requirement_id uuid NOT NULL,
    site varchar(50) NOT NULL,
    job_id varchar(50) NOT NULL,
    text_excerpt text,
    CONSTRAINT pk_requirement_evidence PRIMARY KEY (requirement_id, site, job_id),
    CONSTRAINT fk_requirement_evidence_requirement_id FOREIGN KEY (requirement_id) REFERENCES job_market.role_profile_requirements (requirement_id) ON DELETE CASCADE,
    CONSTRAINT fk_requirement_evidence_site_job_id FOREIGN KEY (site, job_id) REFERENCES job_market.job_ads (site, job_id) ON DELETE CASCADE
);

CREATE UNIQUE INDEX IF NOT EXISTS uq_role_profiles_canonical ON job_market.role_profiles (role_id, career_level, profile_version) WHERE profile_type = 'ROLE' AND role_id IS NOT NULL;
CREATE UNIQUE INDEX IF NOT EXISTS uq_role_profiles_candidate ON job_market.role_profiles (candidate_role_id, career_level, profile_version) WHERE profile_type = 'ROLE' AND candidate_role_id IS NOT NULL;
CREATE UNIQUE INDEX IF NOT EXISTS uq_role_profiles_vacancy ON job_market.role_profiles (vacancy_id, profile_version) WHERE profile_type = 'VACANCY';
CREATE INDEX IF NOT EXISTS idx_rpr_profile ON job_market.role_profile_requirements (profile_id);
GRANT USAGE ON SCHEMA job_market TO readiness_svc;
GRANT SELECT ON job_market.role_profiles, job_market.role_profile_requirements, job_market.role_profile_education, job_market.role_profile_experience, job_market.role_profile_certifications, job_market.requirement_evidence TO readiness_svc;
RESET ROLE;

-- Added after the v2 design (not generated): company job posts and applications.
\ir migrations/2026-11-28-company-job-posts.sql

-- ================================================================ skill_profile  (login skill_profile_svc)
SET ROLE skill_profile_svc;
CREATE TABLE IF NOT EXISTS skill_profile.user_profiles (
    user_id varchar(64) NOT NULL,
    profile jsonb NOT NULL,
    updated_at timestamptz DEFAULT now() NOT NULL,
    CONSTRAINT pk_user_profiles PRIMARY KEY (user_id)
);

CREATE TABLE IF NOT EXISTS skill_profile.student_profiles (
    profile_id uuid NOT NULL,
    user_id uuid NOT NULL,
    profile_version varchar(40) NOT NULL,
    domain_id varchar(50),
    completeness_score numeric(5,4),
    created_at timestamptz DEFAULT now() NOT NULL,
    CONSTRAINT pk_student_profiles PRIMARY KEY (profile_id),
    CONSTRAINT uq_student_profiles_version UNIQUE (user_id, profile_version),
    CONSTRAINT chk_student_profiles_completeness CHECK ((completeness_score IS NULL OR completeness_score BETWEEN 0 AND 1))
);

CREATE TABLE IF NOT EXISTS skill_profile.profile_skills (
    profile_skill_id uuid NOT NULL,
    student_profile_id uuid NOT NULL,
    skill_id varchar(50),
    candidate_skill_id uuid,
    standard_name varchar(255) NOT NULL,
    primary_observed_term text,
    observed_terms text[] DEFAULT '{}' NOT NULL,
    mapping_status varchar(50) NOT NULL,
    skill_type varchar(50) NOT NULL,
    evidence_confidence numeric(5,4) NOT NULL,
    proficiency_score numeric(5,4),
    proficiency_level varchar(20),
    proficiency_source varchar(30),
    created_at timestamptz DEFAULT now() NOT NULL,
    CONSTRAINT pk_profile_skills PRIMARY KEY (profile_skill_id),
    CONSTRAINT fk_profile_skills_student_profile_id FOREIGN KEY (student_profile_id) REFERENCES skill_profile.student_profiles (profile_id) ON DELETE CASCADE,
    CONSTRAINT chk_profile_skills_mapping CHECK ((mapping_status = 'VERIFIED' AND skill_id IS NOT NULL AND candidate_skill_id IS NULL) OR (mapping_status = 'CANDIDATE' AND skill_id IS NULL AND candidate_skill_id IS NOT NULL) OR (mapping_status = 'UNMAPPED' AND skill_id IS NULL AND candidate_skill_id IS NULL)),
    CONSTRAINT chk_profile_skills_skill_type CHECK (skill_type IN ('TECHNICAL', 'BEHAVIOURAL')),
    CONSTRAINT chk_profile_skills_level CHECK (proficiency_level IS NULL OR proficiency_level IN ('BEGINNER', 'INTERMEDIATE', 'ADVANCED')),
    CONSTRAINT chk_profile_skills_source CHECK (proficiency_source IS NULL OR proficiency_source IN ('SELF_REPORTED', 'ASSESSMENT', 'INFERRED', 'NOT_ASSESSED')),
    CONSTRAINT chk_profile_skills_unit_values CHECK (evidence_confidence BETWEEN 0 AND 1 AND (proficiency_score IS NULL OR proficiency_score BETWEEN 0 AND 1))
);

CREATE TABLE IF NOT EXISTS skill_profile.profile_evidence (
    evidence_id uuid NOT NULL,
    profile_skill_id uuid NOT NULL,
    source_type varchar(30),
    source_name text,
    evidence_type varchar(40),
    excerpt text,
    verified boolean DEFAULT false NOT NULL,
    CONSTRAINT pk_profile_evidence PRIMARY KEY (evidence_id),
    CONSTRAINT fk_profile_evidence_profile_skill_id FOREIGN KEY (profile_skill_id) REFERENCES skill_profile.profile_skills (profile_skill_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS skill_profile.education_records (
    education_id uuid NOT NULL,
    profile_id uuid NOT NULL,
    qualification_level varchar(40),
    field_of_study text,
    completion_status varchar(20),
    institution text,
    start_date date,
    end_date date,
    CONSTRAINT pk_education_records PRIMARY KEY (education_id),
    CONSTRAINT fk_education_records_profile_id FOREIGN KEY (profile_id) REFERENCES skill_profile.student_profiles (profile_id) ON DELETE CASCADE,
    CONSTRAINT chk_education_completion CHECK (completion_status IS NULL OR completion_status IN ('COMPLETED', 'IN_PROGRESS', 'NOT_COMPLETED')),
    CONSTRAINT chk_education_dates CHECK (start_date IS NULL OR end_date IS NULL OR start_date <= end_date)
);

CREATE TABLE IF NOT EXISTS skill_profile.experience_records (
    experience_id uuid NOT NULL,
    profile_id uuid NOT NULL,
    position text,
    role_id varchar(50),
    candidate_role_id uuid,
    mapping_status varchar(50),
    experience_type varchar(40),
    organisation text,
    start_date date,
    end_date date,
    is_current boolean,
    description text,
    CONSTRAINT pk_experience_records PRIMARY KEY (experience_id),
    CONSTRAINT fk_experience_records_profile_id FOREIGN KEY (profile_id) REFERENCES skill_profile.student_profiles (profile_id) ON DELETE CASCADE,
    CONSTRAINT chk_experience_mapping CHECK (mapping_status IS NULL OR ((mapping_status = 'VERIFIED' AND role_id IS NOT NULL AND candidate_role_id IS NULL) OR (mapping_status = 'CANDIDATE' AND role_id IS NULL AND candidate_role_id IS NOT NULL) OR (mapping_status = 'UNMAPPED' AND role_id IS NULL AND candidate_role_id IS NULL))),
    CONSTRAINT chk_experience_type CHECK (experience_type IS NULL OR experience_type IN ('FULL_TIME_EMPLOYMENT', 'PART_TIME_EMPLOYMENT', 'INTERNSHIP', 'APPRENTICESHIP', 'FREELANCE', 'SELF_EMPLOYMENT', 'VOLUNTEERING', 'CONTRACT')),
    CONSTRAINT chk_experience_dates CHECK (start_date IS NULL OR end_date IS NULL OR start_date <= end_date)
);

CREATE INDEX IF NOT EXISTS idx_profile_skills_profile ON skill_profile.profile_skills (student_profile_id);
GRANT USAGE ON SCHEMA skill_profile TO readiness_svc;
GRANT SELECT ON skill_profile.student_profiles, skill_profile.profile_skills, skill_profile.profile_evidence, skill_profile.education_records, skill_profile.experience_records TO readiness_svc;
RESET ROLE;

-- ================================================================ readiness  (login readiness_svc)
SET ROLE readiness_svc;
CREATE TABLE IF NOT EXISTS readiness.user_skill_profiles (
    id uuid NOT NULL,
    user_id uuid NOT NULL,
    profile_version varchar(100) NOT NULL,
    domain_id varchar(50),
    domain_name varchar(255),
    completeness_score double precision,
    source_message_id varchar(100),
    raw_payload jsonb NOT NULL,
    received_at timestamptz NOT NULL,
    CONSTRAINT pk_user_skill_profiles PRIMARY KEY (id)
);

CREATE TABLE IF NOT EXISTS readiness.user_skill_profile_skills (
    id uuid NOT NULL,
    user_skill_profile_id uuid NOT NULL,
    skill_id varchar(50),
    candidate_skill_id varchar(50),
    standard_name varchar(255) NOT NULL,
    primary_observed_term varchar(255) NOT NULL,
    observed_terms varchar[] NOT NULL,
    mapping_status varchar(50) NOT NULL,
    skill_type varchar(100) NOT NULL,
    proficiency_level varchar(50) NOT NULL,
    proficiency_score double precision,
    evidence_confidence double precision,
    verification_status varchar(50) NOT NULL,
    CONSTRAINT pk_user_skill_profile_skills PRIMARY KEY (id),
    CONSTRAINT fk_user_skill_profile_skills_user_skill_profile_id FOREIGN KEY (user_skill_profile_id) REFERENCES readiness.user_skill_profiles (id)
);

CREATE TABLE IF NOT EXISTS readiness.skill_evidence (
    id uuid NOT NULL,
    user_skill_profile_skill_id uuid NOT NULL,
    evidence_id varchar(100) NOT NULL,
    source_type varchar(50) NOT NULL,
    source_name varchar(255) NOT NULL,
    evidence_type varchar(100) NOT NULL,
    excerpt text NOT NULL,
    strength double precision NOT NULL,
    verified boolean NOT NULL,
    CONSTRAINT pk_skill_evidence PRIMARY KEY (id),
    CONSTRAINT fk_skill_evidence_user_skill_profile_skill_id FOREIGN KEY (user_skill_profile_skill_id) REFERENCES readiness.user_skill_profile_skills (id)
);

CREATE TABLE IF NOT EXISTS readiness.industry_profiles (
    id uuid NOT NULL,
    role_id varchar(50),
    candidate_role_id varchar(50),
    role_name varchar(255),
    primary_observed_title varchar(255) NOT NULL,
    observed_titles varchar[] NOT NULL,
    mapping_status varchar(50) NOT NULL,
    profile_status varchar(50) NOT NULL,
    domain_id varchar(50),
    domain_name varchar(255),
    career_level varchar(50) NOT NULL,
    profile_version varchar(100) NOT NULL,
    job_posting_count integer,
    observation_period_from date,
    observation_period_to date,
    source_message_id varchar(100),
    raw_payload jsonb NOT NULL,
    received_at timestamptz NOT NULL,
    CONSTRAINT pk_industry_profiles PRIMARY KEY (id)
);

CREATE TABLE IF NOT EXISTS readiness.industry_profile_requirements (
    id uuid NOT NULL,
    industry_profile_id uuid NOT NULL,
    skill_id varchar(50),
    candidate_skill_id varchar(50),
    standard_name varchar(255) NOT NULL,
    primary_observed_term varchar(255) NOT NULL,
    observed_terms varchar[] NOT NULL,
    mapping_status varchar(50) NOT NULL,
    skill_type varchar(100) NOT NULL,
    required_proficiency_level varchar(50) NOT NULL,
    required_proficiency_score double precision,
    demand_weight double precision NOT NULL,
    demand_frequency double precision,
    job_ads_containing_skill integer,
    required_count integer,
    preferred_count integer,
    mentioned_count integer,
    CONSTRAINT pk_industry_profile_requirements PRIMARY KEY (id),
    CONSTRAINT fk_industry_profile_requirements_industry_profile_id FOREIGN KEY (industry_profile_id) REFERENCES readiness.industry_profiles (id)
);

CREATE TABLE IF NOT EXISTS readiness.industry_skill_evidence (
    id uuid NOT NULL,
    requirement_id uuid NOT NULL,
    source_id varchar(100) NOT NULL,
    company varchar(255),
    job_title varchar(255),
    source_date date,
    text_excerpt text NOT NULL,
    CONSTRAINT pk_industry_skill_evidence PRIMARY KEY (id),
    CONSTRAINT fk_industry_skill_evidence_requirement_id FOREIGN KEY (requirement_id) REFERENCES readiness.industry_profile_requirements (id)
);

CREATE TABLE IF NOT EXISTS readiness.analyses (
    analysis_id uuid NOT NULL,
    user_id uuid NOT NULL,
    user_skill_profile_id uuid NOT NULL,
    industry_profile_id uuid NOT NULL,
    snapshot_id uuid NOT NULL,
    matching_method varchar(50) NOT NULL,
    scoring_config_version varchar(50) NOT NULL,
    readiness_score double precision,
    status varchar(30) NOT NULL,
    started_at timestamptz NOT NULL,
    completed_at timestamptz,
    error_message text,
    CONSTRAINT pk_analyses PRIMARY KEY (analysis_id),
    CONSTRAINT fk_analyses_user_skill_profile_id FOREIGN KEY (user_skill_profile_id) REFERENCES readiness.user_skill_profiles (id),
    CONSTRAINT fk_analyses_industry_profile_id FOREIGN KEY (industry_profile_id) REFERENCES readiness.industry_profiles (id)
);

CREATE TABLE IF NOT EXISTS readiness.analysis_skill_results (
    id uuid NOT NULL,
    analysis_id uuid NOT NULL,
    industry_requirement_id uuid,
    user_skill_profile_skill_id uuid,
    required_skill_name varchar(255) NOT NULL,
    matched_skill_name varchar(255),
    match_type varchar(50) NOT NULL,
    relationship_id varchar(50),
    coverage_credit double precision NOT NULL,
    required_proficiency varchar(50) NOT NULL,
    user_proficiency varchar(50),
    evidence_confidence double precision,
    industry_weight double precision,
    satisfaction double precision,
    gap double precision,
    result_status varchar(50) NOT NULL,
    CONSTRAINT pk_analysis_skill_results PRIMARY KEY (id),
    CONSTRAINT fk_analysis_skill_results_analysis_id FOREIGN KEY (analysis_id) REFERENCES readiness.analyses (analysis_id),
    CONSTRAINT fk_analysis_skill_results_industry_requirement_id FOREIGN KEY (industry_requirement_id) REFERENCES readiness.industry_profile_requirements (id),
    CONSTRAINT fk_analysis_skill_results_user_skill_profile_skill_id FOREIGN KEY (user_skill_profile_skill_id) REFERENCES readiness.user_skill_profile_skills (id)
);

CREATE TABLE IF NOT EXISTS readiness.analysis_priority_skills (
    id uuid NOT NULL,
    analysis_id uuid NOT NULL,
    skill_id varchar(50) NOT NULL,
    skill_name varchar(255) NOT NULL,
    priority_rank integer NOT NULL,
    learning_priority_score double precision NOT NULL,
    gap double precision NOT NULL,
    required_proficiency varchar(50) NOT NULL,
    user_proficiency varchar(50),
    CONSTRAINT pk_analysis_priority_skills PRIMARY KEY (id),
    CONSTRAINT fk_analysis_priority_skills_analysis_id FOREIGN KEY (analysis_id) REFERENCES readiness.analyses (analysis_id)
);

CREATE TABLE IF NOT EXISTS readiness.analysis_reports (
    id uuid NOT NULL,
    analysis_id uuid NOT NULL,
    report_version varchar(50) NOT NULL,
    report_payload jsonb NOT NULL,
    generation_method varchar(50) NOT NULL,
    generated_at timestamptz DEFAULT now() NOT NULL,
    status varchar(30) NOT NULL,
    CONSTRAINT pk_analysis_reports PRIMARY KEY (id),
    CONSTRAINT fk_analysis_reports_analysis_id FOREIGN KEY (analysis_id) REFERENCES readiness.analyses (analysis_id)
);

CREATE TABLE IF NOT EXISTS readiness.candidate_discovery_runs (
    id uuid NOT NULL,
    analysis_id uuid NOT NULL,
    embedding_model varchar(100) NOT NULL,
    similarity_threshold double precision NOT NULL,
    status varchar(30) NOT NULL,
    candidates_submitted_count integer NOT NULL,
    started_at timestamptz NOT NULL,
    completed_at timestamptz,
    CONSTRAINT pk_candidate_discovery_runs PRIMARY KEY (id),
    CONSTRAINT fk_candidate_discovery_runs_analysis_id FOREIGN KEY (analysis_id) REFERENCES readiness.analyses (analysis_id)
);

GRANT USAGE ON SCHEMA readiness TO learning_svc;
GRANT SELECT ON readiness.analyses, readiness.analysis_priority_skills TO learning_svc;
RESET ROLE;

-- ================================================================ learning  (login learning_svc)
SET ROLE learning_svc;
CREATE TABLE IF NOT EXISTS learning.learning_documents (
    id uuid NOT NULL,
    title varchar(255) NOT NULL,
    source varchar(255) NOT NULL,
    url text,
    topic varchar(100) NOT NULL,
    target_role varchar(100) NOT NULL,
    created_at timestamptz DEFAULT now(),
    CONSTRAINT pk_learning_documents PRIMARY KEY (id)
);

CREATE TABLE IF NOT EXISTS learning.learning_chunks (
    id uuid NOT NULL,
    document_id uuid NOT NULL,
    chunk_index integer NOT NULL,
    content text NOT NULL,
    metadata jsonb NOT NULL,
    embedding vector,
    created_at timestamptz DEFAULT now(),
    CONSTRAINT pk_learning_chunks PRIMARY KEY (id),
    CONSTRAINT fk_learning_chunks_document_id FOREIGN KEY (document_id) REFERENCES learning.learning_documents (id)
);

CREATE TABLE IF NOT EXISTS learning.student_learning_sessions (
    id uuid NOT NULL,
    student_id uuid NOT NULL,
    target_role varchar(100) NOT NULL,
    session_title varchar(255),
    created_at timestamptz DEFAULT now(),
    analysis_id uuid,
    analysis_context jsonb,
    CONSTRAINT pk_student_learning_sessions PRIMARY KEY (id)
);

CREATE TABLE IF NOT EXISTS learning.student_learning_queries (
    id uuid NOT NULL,
    session_id uuid,
    student_id uuid NOT NULL,
    question text NOT NULL,
    learning_priority varchar(100),
    answer text NOT NULL,
    recommended_next_topic varchar(100),
    retrieved_chunk_ids uuid[],
    sources jsonb,
    created_at timestamptz DEFAULT now(),
    CONSTRAINT pk_student_learning_queries PRIMARY KEY (id),
    CONSTRAINT fk_student_learning_queries_session_id FOREIGN KEY (session_id) REFERENCES learning.student_learning_sessions (id)
);

CREATE TABLE IF NOT EXISTS learning.student_topic_progress (
    id uuid NOT NULL,
    student_id uuid NOT NULL,
    topic varchar(100) NOT NULL,
    target_role varchar(100) NOT NULL,
    queries_count integer,
    status varchar(50),
    last_studied_at timestamptz,
    analysis_id uuid,
    skill_id varchar(50),
    CONSTRAINT pk_student_topic_progress PRIMARY KEY (id)
);

CREATE TABLE IF NOT EXISTS learning.learning_experiment_logs (
    id uuid NOT NULL,
    query_text text NOT NULL,
    top_k integer,
    retrieval_strategy varchar(50),
    embedding_model varchar(100) NOT NULL,
    llm_model varchar(100) NOT NULL,
    retrieved_chunk_ids uuid[],
    similarity_scores numeric[],
    retrieval_latency_ms numeric(10,2),
    generation_latency_ms numeric(10,2),
    total_latency_ms numeric(10,2),
    generated_output text NOT NULL,
    is_baseline integer,
    created_at timestamptz DEFAULT now(),
    CONSTRAINT pk_learning_experiment_logs PRIMARY KEY (id)
);

CREATE TABLE IF NOT EXISTS learning.rag_benchmark_runs (
    id uuid NOT NULL,
    status varchar(20) NOT NULL,
    started_at timestamptz,
    finished_at timestamptz,
    items_done integer,
    items_total integer,
    results jsonb,
    error text,
    CONSTRAINT pk_rag_benchmark_runs PRIMARY KEY (id)
);

CREATE TABLE IF NOT EXISTS learning.edu_lesson_cache (
    id uuid NOT NULL,
    target_role varchar(100) NOT NULL,
    topic varchar(100) NOT NULL,
    level varchar(20) NOT NULL,
    lesson jsonb NOT NULL,
    created_at timestamptz DEFAULT now(),
    CONSTRAINT pk_edu_lesson_cache PRIMARY KEY (id)
);

CREATE TABLE IF NOT EXISTS learning.edu_mastery (
    id uuid NOT NULL,
    student_id uuid NOT NULL,
    topic varchar(100) NOT NULL,
    level varchar(20) NOT NULL,
    mcq_correct integer NOT NULL,
    mcq_total integer NOT NULL,
    open_score double precision,
    completed_at timestamptz,
    CONSTRAINT pk_edu_mastery PRIMARY KEY (id)
);

CREATE TABLE IF NOT EXISTS learning.edu_review_items (
    id uuid NOT NULL,
    student_id uuid NOT NULL,
    topic varchar(100) NOT NULL,
    level varchar(20) NOT NULL,
    question jsonb NOT NULL,
    box integer NOT NULL,
    due_at timestamptz NOT NULL,
    last_reviewed_at timestamptz,
    done boolean NOT NULL,
    created_at timestamptz DEFAULT now(),
    CONSTRAINT pk_edu_review_items PRIMARY KEY (id)
);

RESET ROLE;

-- ================================================================ interview  (login interview_svc)
SET ROLE interview_svc;
CREATE TABLE IF NOT EXISTS interview.interview_documents (
    id uuid NOT NULL,
    title varchar(255) NOT NULL,
    role varchar(100) NOT NULL,
    topic varchar(100) NOT NULL,
    difficulty varchar(50) NOT NULL,
    source varchar(255) NOT NULL,
    created_at timestamptz DEFAULT now(),
    CONSTRAINT pk_interview_documents PRIMARY KEY (id)
);

CREATE TABLE IF NOT EXISTS interview.interview_chunks (
    id uuid NOT NULL,
    document_id uuid NOT NULL,
    chunk_index integer NOT NULL,
    content text NOT NULL,
    expected_answer text,
    rubric jsonb NOT NULL,
    metadata jsonb NOT NULL,
    embedding vector,
    created_at timestamptz DEFAULT now(),
    CONSTRAINT pk_interview_chunks PRIMARY KEY (id),
    CONSTRAINT fk_interview_chunks_document_id FOREIGN KEY (document_id) REFERENCES interview.interview_documents (id)
);

CREATE TABLE IF NOT EXISTS interview.interview_sessions (
    id uuid NOT NULL,
    student_id uuid NOT NULL,
    target_role varchar(100) NOT NULL,
    experience_level varchar(50) NOT NULL,
    status varchar(50),
    candidate_name varchar(100),
    duration_minutes integer,
    candidate_intro text,
    created_at timestamptz DEFAULT now(),
    CONSTRAINT pk_interview_sessions PRIMARY KEY (id)
);

CREATE TABLE IF NOT EXISTS interview.interview_turns (
    id uuid NOT NULL,
    session_id uuid NOT NULL,
    phase varchar(20) NOT NULL,
    question text NOT NULL,
    topic varchar(100) NOT NULL,
    difficulty varchar(50) NOT NULL,
    transcript text,
    reference_answer text,
    rubric_criteria jsonb,
    follow_up_of uuid,
    technical_accuracy_score numeric(3,2),
    relevance_score numeric(3,2),
    explanation_quality_score numeric(3,2),
    clarity_score numeric(3,2),
    technical_feedback text,
    communication_feedback text,
    missing_concepts jsonb,
    strengths jsonb,
    areas_for_improvement jsonb,
    created_at timestamptz DEFAULT now(),
    CONSTRAINT pk_interview_turns PRIMARY KEY (id),
    CONSTRAINT fk_interview_turns_session_id FOREIGN KEY (session_id) REFERENCES interview.interview_sessions (id),
    CONSTRAINT fk_interview_turns_follow_up_of FOREIGN KEY (follow_up_of) REFERENCES interview.interview_turns (id)
);

CREATE TABLE IF NOT EXISTS interview.interview_experiment_logs (
    id uuid NOT NULL,
    turn_id uuid,
    stt_latency_ms numeric(10,2),
    retrieval_latency_ms numeric(10,2),
    evaluation_latency_ms numeric(10,2),
    created_at timestamptz DEFAULT now(),
    CONSTRAINT pk_interview_experiment_logs PRIMARY KEY (id),
    CONSTRAINT fk_interview_experiment_logs_turn_id FOREIGN KEY (turn_id) REFERENCES interview.interview_turns (id)
);

RESET ROLE;

-- Summary
\unset QUIET
SELECT n.nspname AS schema, pg_get_userbyid(n.nspowner) AS owner, count(c.oid) AS tables
FROM pg_namespace n LEFT JOIN pg_class c ON c.relnamespace = n.oid AND c.relkind = 'r'
WHERE n.nspname IN ('auth', 'ssks', 'job_market', 'skill_profile', 'readiness', 'learning', 'interview')
GROUP BY n.nspname, n.nspowner ORDER BY n.nspname;
