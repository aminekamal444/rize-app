-- =============================================================================
-- RIZE — Migration 007: Add lifestyle fields to profiles
-- File: 007_add_lifestyle_fields.sql
--
-- Why: Path B AI improvements need lifestyle context (daily pattern,
-- activity level, upcoming events) to generate accurate, leveraged plans.
-- =============================================================================

ALTER TABLE profiles
ADD COLUMN IF NOT EXISTS daily_pattern TEXT DEFAULT '';

ALTER TABLE profiles
ADD COLUMN IF NOT EXISTS activity_level TEXT DEFAULT '';

ALTER TABLE profiles
ADD COLUMN IF NOT EXISTS upcoming_context TEXT DEFAULT '';
