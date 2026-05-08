-- =============================================================================
-- RIZE — Migration 004: Storage RLS policies
-- File: 004_storage_rls_policies.sql
--
-- Why: Migration 001 created storage buckets but didn't add RLS policies on
-- storage.objects. Phase 2 needed them when we started uploading photos.
-- Without these, every upload is rejected with "new row violates row-level
-- security policy" — which is the bug we hit during onboarding photo upload.
--
-- Fix: For each private bucket (progress-photos, profile-photos,
-- wardrobe-thumbnails), allow authenticated users to read/write only files in
-- their own folder. The user's auth.uid() must match the first folder segment
-- of the file path. So uploads go to "<user_id>/<filename>".
-- =============================================================================

-- progress-photos bucket
CREATE POLICY "progress-photos read own"
ON storage.objects FOR SELECT TO authenticated
USING (bucket_id = 'progress-photos' AND auth.uid()::text = (storage.foldername(name))[1]);

CREATE POLICY "progress-photos insert own"
ON storage.objects FOR INSERT TO authenticated
WITH CHECK (bucket_id = 'progress-photos' AND auth.uid()::text = (storage.foldername(name))[1]);

CREATE POLICY "progress-photos update own"
ON storage.objects FOR UPDATE TO authenticated
USING (bucket_id = 'progress-photos' AND auth.uid()::text = (storage.foldername(name))[1]);

CREATE POLICY "progress-photos delete own"
ON storage.objects FOR DELETE TO authenticated
USING (bucket_id = 'progress-photos' AND auth.uid()::text = (storage.foldername(name))[1]);

-- profile-photos bucket
CREATE POLICY "profile-photos read own"
ON storage.objects FOR SELECT TO authenticated
USING (bucket_id = 'profile-photos' AND auth.uid()::text = (storage.foldername(name))[1]);

CREATE POLICY "profile-photos insert own"
ON storage.objects FOR INSERT TO authenticated
WITH CHECK (bucket_id = 'profile-photos' AND auth.uid()::text = (storage.foldername(name))[1]);

CREATE POLICY "profile-photos update own"
ON storage.objects FOR UPDATE TO authenticated
USING (bucket_id = 'profile-photos' AND auth.uid()::text = (storage.foldername(name))[1]);

CREATE POLICY "profile-photos delete own"
ON storage.objects FOR DELETE TO authenticated
USING (bucket_id = 'profile-photos' AND auth.uid()::text = (storage.foldername(name))[1]);

-- wardrobe-thumbnails bucket
CREATE POLICY "wardrobe-thumbnails read own"
ON storage.objects FOR SELECT TO authenticated
USING (bucket_id = 'wardrobe-thumbnails' AND auth.uid()::text = (storage.foldername(name))[1]);

CREATE POLICY "wardrobe-thumbnails insert own"
ON storage.objects FOR INSERT TO authenticated
WITH CHECK (bucket_id = 'wardrobe-thumbnails' AND auth.uid()::text = (storage.foldername(name))[1]);

CREATE POLICY "wardrobe-thumbnails update own"
ON storage.objects FOR UPDATE TO authenticated
USING (bucket_id = 'wardrobe-thumbnails' AND auth.uid()::text = (storage.foldername(name))[1]);

CREATE POLICY "wardrobe-thumbnails delete own"
ON storage.objects FOR DELETE TO authenticated
USING (bucket_id = 'wardrobe-thumbnails' AND auth.uid()::text = (storage.foldername(name))[1]);

-- barber-card-references is public read, no user-scoped policy needed