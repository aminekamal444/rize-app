-- =============================================================================
-- RIZE — Migration 003: Fix handle_new_user trigger search_path
-- File: 003_fix_handle_new_user_search_path.sql
-- 
-- Why: Migration 001 created handle_new_user() without setting search_path.
-- Postgres triggers run in the schema of the triggering table (auth.users),
-- so "INSERT INTO profiles" fails with "relation does not exist" because it
-- looks in auth schema instead of public.
-- 
-- Fix: Set search_path explicitly and qualify the table name with public.
-- 
-- This migration is idempotent — safe to run multiple times.
-- =============================================================================

CREATE OR REPLACE FUNCTION public.handle_new_user()
RETURNS TRIGGER 
LANGUAGE plpgsql 
SECURITY DEFINER 
SET search_path = public
AS $$
BEGIN
    INSERT INTO public.profiles (id)
    VALUES (NEW.id)
    ON CONFLICT (id) DO NOTHING;
    RETURN NEW;
END;
$$;

-- =============================================================================
-- END OF MIGRATION 003
-- =============================================================================