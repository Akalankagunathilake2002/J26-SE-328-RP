-- Migration: 003_refine_and_verify_candidate_relationships.sql
-- Description: Add structured evidence, provenance, and canonical link columns to candidate and skill relationships

ALTER TABLE candidate_skill_relationships
    ADD COLUMN IF NOT EXISTS evidence_description TEXT,
    ADD COLUMN IF NOT EXISTS evidence_url VARCHAR(500),
    ADD COLUMN IF NOT EXISTS reviewed_by VARCHAR(100),
    ADD COLUMN IF NOT EXISTS canonical_relationship_id VARCHAR(50);

ALTER TABLE skill_relationships
    ADD COLUMN IF NOT EXISTS evidence_description TEXT,
    ADD COLUMN IF NOT EXISTS evidence_url VARCHAR(500),
    ADD COLUMN IF NOT EXISTS reviewed_by VARCHAR(100);
