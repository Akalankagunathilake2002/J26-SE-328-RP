-- Migration: 002_create_candidate_entities.sql
-- Description: Create candidate_entities table for proposed new canonical skills and roles

CREATE TABLE IF NOT EXISTS candidate_entities (
    candidate_entity_id VARCHAR(50) PRIMARY KEY,
    entity_type VARCHAR(20) NOT NULL,
    submitted_name VARCHAR(255) NOT NULL,
    normalized_name VARCHAR(255) NOT NULL,
    description TEXT,
    proposed_skill_type VARCHAR(100),
    proposed_skill_nature VARCHAR(50),
    source_component VARCHAR(50),
    source_reference VARCHAR(255),
    review_status VARCHAR(50) NOT NULL DEFAULT 'PENDING',
    review_note TEXT,
    matched_entity_id VARCHAR(50),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    reviewed_at TIMESTAMP WITH TIME ZONE,
    CONSTRAINT check_valid_candidate_entity_type CHECK (entity_type IN ('SKILL', 'ROLE')),
    CONSTRAINT check_valid_candidate_review_status CHECK (review_status IN ('PENDING', 'APPROVED', 'REJECTED')),
    CONSTRAINT check_valid_proposed_skill_type CHECK (
        proposed_skill_type IN ('PROGRAMMING_LANGUAGE', 'PROGRAMMING_SKILL', 'PROGRAMMING_PARADIGM', 'SOFTWARE_OR_TOOL', 'KNOWLEDGE', 'OTHER_SKILL')
        OR proposed_skill_type IS NULL
    ),
    CONSTRAINT check_valid_proposed_skill_nature CHECK (
        proposed_skill_nature IN ('TECHNICAL', 'BEHAVIOURAL', 'OTHER')
        OR proposed_skill_nature IS NULL
    ),
    CONSTRAINT check_candidate_role_no_skill_fields CHECK (
        (entity_type = 'SKILL')
        OR (proposed_skill_type IS NULL AND proposed_skill_nature IS NULL)
    )
);

CREATE INDEX IF NOT EXISTS ix_candidate_entities_normalized_name
    ON candidate_entities (normalized_name);

CREATE INDEX IF NOT EXISTS ix_candidate_entities_review_status
    ON candidate_entities (review_status);
