-- =============================================================================
-- RIZE — Migration 002: Onboarding Step & New Profile Columns
-- File: 002_onboarding_step.sql
-- Apply: paste into Supabase SQL editor and run manually.
-- Do NOT run this file directly from the backend.
-- =============================================================================

-- -----------------------------------------------------------------------------
-- PROFILES — new columns for onboarding flow
-- -----------------------------------------------------------------------------

ALTER TABLE profiles
    ADD COLUMN IF NOT EXISTS onboarding_step      SMALLINT NOT NULL DEFAULT 0
        CHECK (onboarding_step BETWEEN 0 AND 7),
    ADD COLUMN IF NOT EXISTS biggest_goal         TEXT,
    ADD COLUMN IF NOT EXISTS biggest_insecurity   TEXT,
    ADD COLUMN IF NOT EXISTS target_archetype     TEXT;

-- -----------------------------------------------------------------------------
-- PHOTOS — observations from baseline AI scoring
-- Stored as a JSON array of strings, e.g.:
--   ["Your collar sits too high...", "The baggy fit adds bulk...", ...]
-- -----------------------------------------------------------------------------

ALTER TABLE photos
    ADD COLUMN IF NOT EXISTS observations JSONB;

-- =============================================================================
-- END OF MIGRATION 002
-- =============================================================================
