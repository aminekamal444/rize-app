-- =============================================================================
-- RIZE — Migration 005: Prevent duplicate baseline photos per user
-- File: 005_prevent_duplicate_baseline.sql
--
-- Why: Multiple rapid clicks on the photo upload button created multiple
-- baseline rows. Session only tracks the latest photo_id but AI analysis
-- updated different rows, leaving users with broken NULL data.
--
-- Fix: Database-level unique constraint guaranteeing one baseline per user.
-- App-level upsert in onboarding_photo_post handles the user-facing flow.
-- This is defense-in-depth at the schema layer.
-- =============================================================================

CREATE UNIQUE INDEX IF NOT EXISTS photos_one_baseline_per_user
ON photos (user_id)
WHERE type = 'baseline';

-- Note: a partial unique index allows multiple non-baseline photos per user
-- (weekly check-ins, future progress photos), but exactly one 'baseline' row.
