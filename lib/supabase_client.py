from __future__ import annotations

import os
from functools import lru_cache

from supabase import create_client, Client


@lru_cache(maxsize=1)
def get_supabase() -> Client:
    """Return a cached Supabase client using env vars."""
    url: str = os.environ["SUPABASE_URL"]
    key: str = os.environ["SUPABASE_ANON_KEY"]
    return create_client(url, key)
