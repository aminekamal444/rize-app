-- =============================================================================
-- RIZE — Migration 009: Update photos unique constraint for multi-angle baseline
-- File: 009_photo_type_unique_constraint.sql
--
-- Why: The existing constraint (photos_one_baseline_per_user) only allows
-- one baseline row per user. With 3-photo capture, we need one row per
-- (user_id, type) combination:
--   baseline_front, baseline_side, baseline_body
-- This migration drops the old constraint and creates the new one.
-- =============================================================================

-- Drop the old partial unique index from migration 005
DROP INDEX IF EXISTS photos_one_baseline_per_user;

-- Create new partial unique index: one row per (user_id, type) for baseline types
CREATE UNIQUE INDEX IF NOT EXISTS photos_one_per_type_per_user
ON photos (user_id, type)
WHERE type IN ('baseline_front', 'baseline_side', 'baseline_body', 'baseline');

-- Note: 'baseline' is included for backward compatibility with existing rows
-- that used the old single-photo approach.
