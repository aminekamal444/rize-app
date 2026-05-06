-- =============================================================================
-- RIZE — Initial Schema Migration
-- File: 001_initial_schema.sql
-- Apply: paste into Supabase SQL editor and run manually.
-- Do NOT run this file directly from the backend.
-- =============================================================================

-- -----------------------------------------------------------------------------
-- STORAGE BUCKETS (create manually in Supabase Dashboard > Storage)
-- -----------------------------------------------------------------------------
-- Create the following four buckets in the Supabase Dashboard UI:
--
--   1. profile-photos
--      Private. RLS policy: authenticated users can read/write only their own
--      objects (folder path must start with auth.uid()::text).
--
--   2. progress-photos
--      Private. Same RLS pattern as profile-photos.
--
--   3. wardrobe-thumbnails
--      Private. Same RLS pattern — only thumbnails are stored, never originals.
--
--   4. barber-card-references
--      Public read (anyone can view haircut reference images).
--      Write restricted to service-role key only (admin upload via dashboard).
--
-- Bucket storage policies (example for profile-photos, repeat for each):
--   SELECT policy: (auth.uid()::text = (storage.foldername(name))[1])
--   INSERT policy: (auth.uid()::text = (storage.foldername(name))[1])
--   UPDATE policy: (auth.uid()::text = (storage.foldername(name))[1])
--   DELETE policy: (auth.uid()::text = (storage.foldername(name))[1])
-- -----------------------------------------------------------------------------


-- =============================================================================
-- EXTENSIONS
-- =============================================================================

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";


-- =============================================================================
-- PROFILES
-- Extends auth.users. One row per user. Created automatically via trigger.
-- =============================================================================

CREATE TABLE IF NOT EXISTS profiles (
    id              UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT now(),

    -- Basics filled during onboarding
    display_name    TEXT,
    age             SMALLINT CHECK (age BETWEEN 13 AND 120),
    city            TEXT,
    preferred_language  TEXT NOT NULL DEFAULT 'fr' CHECK (preferred_language IN ('fr', 'en', 'ar')),

    -- Journey state
    onboarding_complete BOOLEAN NOT NULL DEFAULT FALSE,
    journey_start_date  DATE,
    journey_day         SMALLINT NOT NULL DEFAULT 0 CHECK (journey_day BETWEEN 0 AND 30),
    streak_current      SMALLINT NOT NULL DEFAULT 0,
    streak_best         SMALLINT NOT NULL DEFAULT 0,

    -- AI-assigned archetype from baseline scoring
    archetype       TEXT,
    baseline_score  SMALLINT CHECK (baseline_score BETWEEN 0 AND 100)
);

ALTER TABLE profiles ENABLE ROW LEVEL SECURITY;

CREATE POLICY "profiles: user reads own row"
    ON profiles FOR SELECT
    USING (auth.uid() = id);

CREATE POLICY "profiles: user updates own row"
    ON profiles FOR UPDATE
    USING (auth.uid() = id)
    WITH CHECK (auth.uid() = id);

-- Allow insert only via the trigger below (service role creates the row).
-- Users can also upsert during onboarding, so we allow insert for authenticated.
CREATE POLICY "profiles: user inserts own row"
    ON profiles FOR INSERT
    WITH CHECK (auth.uid() = id);


-- Trigger: auto-create a profiles row when a new auth user is created
CREATE OR REPLACE FUNCTION handle_new_user()
RETURNS TRIGGER LANGUAGE plpgsql SECURITY DEFINER AS $$
BEGIN
    INSERT INTO profiles (id)
    VALUES (NEW.id)
    ON CONFLICT (id) DO NOTHING;
    RETURN NEW;
END;
$$;

DROP TRIGGER IF EXISTS on_auth_user_created ON auth.users;

CREATE TRIGGER on_auth_user_created
    AFTER INSERT ON auth.users
    FOR EACH ROW EXECUTE FUNCTION handle_new_user();

-- Trigger: keep updated_at current on profiles
CREATE OR REPLACE FUNCTION set_updated_at()
RETURNS TRIGGER LANGUAGE plpgsql AS $$
BEGIN
    NEW.updated_at = now();
    RETURN NEW;
END;
$$;

DROP TRIGGER IF EXISTS profiles_updated_at ON profiles;

CREATE TRIGGER profiles_updated_at
    BEFORE UPDATE ON profiles
    FOR EACH ROW EXECUTE FUNCTION set_updated_at();


-- =============================================================================
-- PHOTOS
-- Every photo uploaded by a user (baseline, progress, coach-attached).
-- Original wardrobe photos are never stored; only wardrobe thumbnails go in
-- the wardrobe_items table.
-- =============================================================================

CREATE TABLE IF NOT EXISTS photos (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id         UUID NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),

    type            TEXT NOT NULL CHECK (type IN ('baseline', 'progress', 'coach')),
    storage_path    TEXT NOT NULL,      -- path inside Supabase Storage bucket
    bucket          TEXT NOT NULL,      -- bucket name (profile-photos, progress-photos, …)

    -- AI scoring results (null until scored)
    score_overall   SMALLINT CHECK (score_overall BETWEEN 0 AND 100),
    score_hair      SMALLINT CHECK (score_hair BETWEEN 0 AND 100),
    score_style     SMALLINT CHECK (score_style BETWEEN 0 AND 100),
    score_fitness   SMALLINT CHECK (score_fitness BETWEEN 0 AND 100),
    score_skin      SMALLINT CHECK (score_skin BETWEEN 0 AND 100),
    tagline         TEXT,
    strength        TEXT,
    improvement     TEXT,

    -- Which journey day was this taken on (0 = baseline)
    journey_day     SMALLINT NOT NULL DEFAULT 0
);

ALTER TABLE photos ENABLE ROW LEVEL SECURITY;

CREATE POLICY "photos: user reads own rows"
    ON photos FOR SELECT
    USING (auth.uid() = user_id);

CREATE POLICY "photos: user inserts own rows"
    ON photos FOR INSERT
    WITH CHECK (auth.uid() = user_id);

CREATE POLICY "photos: user deletes own rows"
    ON photos FOR DELETE
    USING (auth.uid() = user_id);


-- =============================================================================
-- DAILY_PLANS
-- One row per journey day per user. Defines the focus pillar for that day.
-- Generated in bulk at the end of onboarding (days 1-30).
-- =============================================================================

CREATE TABLE IF NOT EXISTS daily_plans (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id         UUID NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),

    journey_day     SMALLINT NOT NULL CHECK (journey_day BETWEEN 1 AND 30),
    focus_pillar    TEXT NOT NULL CHECK (focus_pillar IN ('hair', 'style', 'fitness', 'skin', 'recovery')),
    summary         TEXT,               -- short AI-generated description for this day
    is_recovery_day BOOLEAN NOT NULL DEFAULT FALSE,

    UNIQUE (user_id, journey_day)
);

ALTER TABLE daily_plans ENABLE ROW LEVEL SECURITY;

CREATE POLICY "daily_plans: user reads own rows"
    ON daily_plans FOR SELECT
    USING (auth.uid() = user_id);

CREATE POLICY "daily_plans: user inserts own rows"
    ON daily_plans FOR INSERT
    WITH CHECK (auth.uid() = user_id);

CREATE POLICY "daily_plans: user updates own rows"
    ON daily_plans FOR UPDATE
    USING (auth.uid() = user_id)
    WITH CHECK (auth.uid() = user_id);


-- =============================================================================
-- DAILY_ACTIONS
-- 1-3 concrete actions per daily_plan. Completion is tracked here.
-- =============================================================================

CREATE TABLE IF NOT EXISTS daily_actions (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id         UUID NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
    daily_plan_id   UUID NOT NULL REFERENCES daily_plans(id) ON DELETE CASCADE,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),

    position        SMALLINT NOT NULL CHECK (position BETWEEN 1 AND 3),
    pillar          TEXT NOT NULL CHECK (pillar IN ('hair', 'style', 'fitness', 'skin', 'recovery')),
    title           TEXT NOT NULL,
    description     TEXT,
    completed       BOOLEAN NOT NULL DEFAULT FALSE,
    completed_at    TIMESTAMPTZ,

    UNIQUE (daily_plan_id, position)
);

ALTER TABLE daily_actions ENABLE ROW LEVEL SECURITY;

CREATE POLICY "daily_actions: user reads own rows"
    ON daily_actions FOR SELECT
    USING (auth.uid() = user_id);

CREATE POLICY "daily_actions: user inserts own rows"
    ON daily_actions FOR INSERT
    WITH CHECK (auth.uid() = user_id);

CREATE POLICY "daily_actions: user updates own rows"
    ON daily_actions FOR UPDATE
    USING (auth.uid() = user_id)
    WITH CHECK (auth.uid() = user_id);


-- =============================================================================
-- COACH_MESSAGES
-- Persistent chat history with the AI coach. Each row is one message.
-- =============================================================================

CREATE TABLE IF NOT EXISTS coach_messages (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id         UUID NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),

    role            TEXT NOT NULL CHECK (role IN ('user', 'assistant')),
    content         TEXT NOT NULL,

    -- Optional: journey day context when the message was sent
    journey_day     SMALLINT,

    -- If a photo was attached to a user message (processed in memory, never stored)
    had_photo       BOOLEAN NOT NULL DEFAULT FALSE
);

ALTER TABLE coach_messages ENABLE ROW LEVEL SECURITY;

CREATE POLICY "coach_messages: user reads own rows"
    ON coach_messages FOR SELECT
    USING (auth.uid() = user_id);

CREATE POLICY "coach_messages: user inserts own rows"
    ON coach_messages FOR INSERT
    WITH CHECK (auth.uid() = user_id);

CREATE POLICY "coach_messages: user deletes own rows"
    ON coach_messages FOR DELETE
    USING (auth.uid() = user_id);


-- =============================================================================
-- WARDROBE_ITEMS
-- User's uploaded wardrobe pieces. Only thumbnail stored — original discarded.
-- AI-extracted metadata is stored as flat columns.
-- =============================================================================

CREATE TABLE IF NOT EXISTS wardrobe_items (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id         UUID NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),

    -- Storage: only the thumbnail is stored (200x200, 60% JPEG)
    thumbnail_url   TEXT NOT NULL,      -- public or signed URL from Supabase Storage

    -- AI-extracted metadata
    category        TEXT CHECK (category IN ('top', 'bottom', 'shoes', 'outerwear', 'accessory', 'other')),
    color_primary   TEXT,
    color_secondary TEXT,
    style_tags      TEXT[],             -- e.g. ['casual', 'streetwear']
    formality       TEXT CHECK (formality IN ('casual', 'smart_casual', 'formal', 'sport')),
    season          TEXT CHECK (season IN ('all', 'warm', 'cold')),
    ai_description  TEXT,               -- one-sentence AI description for prompt context

    -- User label (optional, added after upload)
    label           TEXT,
    is_active       BOOLEAN NOT NULL DEFAULT TRUE  -- soft-delete / hide from wardrobe
);

ALTER TABLE wardrobe_items ENABLE ROW LEVEL SECURITY;

CREATE POLICY "wardrobe_items: user reads own rows"
    ON wardrobe_items FOR SELECT
    USING (auth.uid() = user_id);

CREATE POLICY "wardrobe_items: user inserts own rows"
    ON wardrobe_items FOR INSERT
    WITH CHECK (auth.uid() = user_id);

CREATE POLICY "wardrobe_items: user updates own rows"
    ON wardrobe_items FOR UPDATE
    USING (auth.uid() = user_id)
    WITH CHECK (auth.uid() = user_id);

CREATE POLICY "wardrobe_items: user deletes own rows"
    ON wardrobe_items FOR DELETE
    USING (auth.uid() = user_id);


-- =============================================================================
-- OUTFIT_RECOMMENDATIONS
-- Daily AI-generated outfit suggestions from the user's wardrobe.
-- =============================================================================

CREATE TABLE IF NOT EXISTS outfit_recommendations (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id         UUID NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),

    journey_day     SMALLINT NOT NULL,
    occasion        TEXT,               -- e.g. 'casual', 'work', 'date'
    description     TEXT NOT NULL,      -- AI-generated outfit description
    rationale       TEXT,               -- why this works for their profile
    item_ids        UUID[],             -- references to wardrobe_items used

    UNIQUE (user_id, journey_day)
);

ALTER TABLE outfit_recommendations ENABLE ROW LEVEL SECURITY;

CREATE POLICY "outfit_recommendations: user reads own rows"
    ON outfit_recommendations FOR SELECT
    USING (auth.uid() = user_id);

CREATE POLICY "outfit_recommendations: user inserts own rows"
    ON outfit_recommendations FOR INSERT
    WITH CHECK (auth.uid() = user_id);

CREATE POLICY "outfit_recommendations: user updates own rows"
    ON outfit_recommendations FOR UPDATE
    USING (auth.uid() = user_id)
    WITH CHECK (auth.uid() = user_id);


-- =============================================================================
-- BARBER_CARDS
-- Generated when a haircut action appears in the daily plan.
-- Trilingual instructions (stored as JSON), shareable.
-- =============================================================================

CREATE TABLE IF NOT EXISTS barber_cards (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id         UUID NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),

    journey_day     SMALLINT NOT NULL,
    haircut_name    TEXT NOT NULL,

    -- Trilingual content as JSON objects: {"fr": "...", "en": "...", "ar": "..."}
    instructions_fr TEXT NOT NULL,
    instructions_en TEXT NOT NULL,
    instructions_ar TEXT NOT NULL,

    -- Optional reference image from barber-card-references bucket
    reference_image_url TEXT,

    -- Guard and length details
    sides_guard     TEXT,
    top_length      TEXT,
    beard_style     TEXT
);

ALTER TABLE barber_cards ENABLE ROW LEVEL SECURITY;

CREATE POLICY "barber_cards: user reads own rows"
    ON barber_cards FOR SELECT
    USING (auth.uid() = user_id);

CREATE POLICY "barber_cards: user inserts own rows"
    ON barber_cards FOR INSERT
    WITH CHECK (auth.uid() = user_id);

CREATE POLICY "barber_cards: user updates own rows"
    ON barber_cards FOR UPDATE
    USING (auth.uid() = user_id)
    WITH CHECK (auth.uid() = user_id);


-- =============================================================================
-- WEEKLY_CHECK_INS
-- Weekly progress photo + AI re-scoring + score delta vs previous week.
-- =============================================================================

CREATE TABLE IF NOT EXISTS weekly_check_ins (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id         UUID NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),

    week_number     SMALLINT NOT NULL CHECK (week_number BETWEEN 1 AND 4),
    photo_id        UUID REFERENCES photos(id) ON DELETE SET NULL,

    -- Scores for this week
    score_overall   SMALLINT CHECK (score_overall BETWEEN 0 AND 100),
    score_hair      SMALLINT CHECK (score_hair BETWEEN 0 AND 100),
    score_style     SMALLINT CHECK (score_style BETWEEN 0 AND 100),
    score_fitness   SMALLINT CHECK (score_fitness BETWEEN 0 AND 100),
    score_skin      SMALLINT CHECK (score_skin BETWEEN 0 AND 100),

    -- Deltas vs previous check-in (null for week 1 vs baseline)
    delta_overall   SMALLINT,
    delta_hair      SMALLINT,
    delta_style     SMALLINT,
    delta_fitness   SMALLINT,
    delta_skin      SMALLINT,

    -- Adherence: percentage of actions completed this week
    adherence_rate  SMALLINT CHECK (adherence_rate BETWEEN 0 AND 100),

    -- AI-generated summary of progress this week
    ai_summary      TEXT,

    UNIQUE (user_id, week_number)
);

ALTER TABLE weekly_check_ins ENABLE ROW LEVEL SECURITY;

CREATE POLICY "weekly_check_ins: user reads own rows"
    ON weekly_check_ins FOR SELECT
    USING (auth.uid() = user_id);

CREATE POLICY "weekly_check_ins: user inserts own rows"
    ON weekly_check_ins FOR INSERT
    WITH CHECK (auth.uid() = user_id);

CREATE POLICY "weekly_check_ins: user updates own rows"
    ON weekly_check_ins FOR UPDATE
    USING (auth.uid() = user_id)
    WITH CHECK (auth.uid() = user_id);


-- =============================================================================
-- END OF MIGRATION 001
-- =============================================================================
