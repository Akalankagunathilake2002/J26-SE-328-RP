-- Add skill_nature column to skills table if not present
ALTER TABLE IF EXISTS skills
ADD COLUMN IF NOT EXISTS skill_nature VARCHAR(50);

-- Safely add check constraint if table exists and constraint is not already present
DO $$
BEGIN
    IF EXISTS (
        SELECT 1
        FROM information_schema.tables
        WHERE table_name = 'skills'
    ) AND NOT EXISTS (
        SELECT 1
        FROM pg_constraint
        WHERE conname = 'check_valid_skill_nature'
          AND conrelid = 'skills'::regclass
    ) THEN
        ALTER TABLE skills
        ADD CONSTRAINT check_valid_skill_nature
        CHECK (skill_nature IN ('TECHNICAL', 'BEHAVIOURAL', 'OTHER') OR skill_nature IS NULL);
    END IF;
END $$;
