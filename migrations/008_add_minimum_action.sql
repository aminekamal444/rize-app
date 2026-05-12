-- =============================================================================
-- RIZE — Migration 008: Add minimum action field to daily_actions
-- File: 008_add_minimum_action.sql
--
-- Why: Path B AI improvements add a per-action 'minimum' field — the
-- absolute lowest-effort version of each action for low-motivation days.
-- =============================================================================

ALTER TABLE daily_actions
ADD COLUMN IF NOT EXISTS minimum TEXT DEFAULT '';
