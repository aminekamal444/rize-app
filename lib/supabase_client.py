from __future__ import annotations

import os
from functools import lru_cache

from supabase import create_client, Client


@lru_cache(maxsize=1)
def get_supabase() -> Client:
    """Return a cached anonymous Supabase client (no user auth)."""
    url: str = os.environ["SUPABASE_URL"]
    key: str = os.environ["SUPABASE_ANON_KEY"]
    return create_client(url, key)


@lru_cache(maxsize=1)
def get_admin_supabase() -> Client:
    """
    Return a cached Supabase client using the service-role key.

    SECURITY: This client BYPASSES Row Level Security. Use ONLY for backend
    storage operations where:
      - The user has already been verified via Flask session (@login_required)
      - The operation path is scoped to that user (e.g., '<user_id>/file.jpg')
      - No user-supplied input determines the storage path or bucket

    Never use this client for table operations or anywhere user input
    influences what is read/written.
    """
    url: str = os.environ["SUPABASE_URL"]
    key: str = os.environ["SUPABASE_SERVICE_ROLE_KEY"]
    return create_client(url, key)


def get_authed_supabase(access_token: str, refresh_token: str = "") -> Client:
    """
    Return a per-request Supabase client authenticated with the user's JWT.

    Creates a fresh client instance each call (not cached) so that different
    users' tokens cannot overwrite each other. All DB and storage operations
    that must respect RLS (user can only access their own rows) must use this
    client — not the shared get_supabase() client.

    The access_token and refresh_token come from the Flask session where they
    are stored at login/signup time (lib/auth.set_user_session).
    """
    url: str = os.environ["SUPABASE_URL"]
    key: str = os.environ["SUPABASE_ANON_KEY"]
    client = create_client(url, key)
    if access_token:
        client.auth.set_session(access_token, refresh_token)
    return client
