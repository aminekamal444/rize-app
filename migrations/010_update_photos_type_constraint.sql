-- =============================================================================
-- RIZE — Migration 010: Add new baseline photo types to check constraint
-- File: 010_update_photos_type_constraint.sql
--
-- Why: Phase 6b added baseline_front, baseline_side, baseline_body as new
-- photo types. The existing photos_type_check constraint doesn't include
-- these values, causing inserts to fail.
-- =============================================================================

ALTER TABLE photos
DROP CONSTRAINT IF EXISTS photos_type_check;

ALTER TABLE photos
ADD CONSTRAINT photos_type_check
CHECK (type IN (
  'baseline',
  'baseline_front',
  'baseline_side',
  'baseline_body',
  'progress',
  'wardrobe'
));
