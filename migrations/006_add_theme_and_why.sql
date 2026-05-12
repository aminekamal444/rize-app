-- =============================================================================
-- RIZE — Migration 006: Add theme to daily_plans and why to daily_actions
-- File: 006_add_theme_and_why.sql
--
-- Why: Phase 6a AI prompt improvements add a day-level theme (emotional/
-- conceptual framing) and an action-level 'why' (explanation of why this
-- action matters for this user). These need columns in the database.
-- =============================================================================

ALTER TABLE daily_plans
ADD COLUMN IF NOT EXISTS theme TEXT DEFAULT '';

ALTER TABLE daily_actions
ADD COLUMN IF NOT EXISTS why TEXT DEFAULT '';
