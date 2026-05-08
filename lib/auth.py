from __future__ import annotations

from functools import wraps
from typing import Optional, Tuple

from flask import redirect, session, url_for


_SESSION_KEY = "user_id"
_ACCESS_TOKEN_KEY = "sb_access_token"
_REFRESH_TOKEN_KEY = "sb_refresh_token"


def login_required(f):
    """Decorator that redirects to /login if no authenticated user in session."""
    @wraps(f)
    def decorated(*args, **kwargs):
        if not get_current_user():
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return decorated


def get_current_user() -> Optional[str]:
    """Return the user_id from the session, or None if not logged in."""
    return session.get(_SESSION_KEY)


def set_user_session(
    user_id: str,
    access_token: str = "",
    refresh_token: str = "",
) -> None:
    """Store the authenticated user_id and Supabase JWT tokens in the session."""
    session[_SESSION_KEY] = user_id
    if access_token:
        session[_ACCESS_TOKEN_KEY] = access_token
    if refresh_token:
        session[_REFRESH_TOKEN_KEY] = refresh_token


def get_supabase_tokens() -> Tuple[str, str]:
    """Return (access_token, refresh_token) from session, or ('', '') if absent."""
    return (
        session.get(_ACCESS_TOKEN_KEY, ""),
        session.get(_REFRESH_TOKEN_KEY, ""),
    )


def clear_user_session() -> None:
    """Remove the user and all tokens from the session (logout)."""
    session.pop(_SESSION_KEY, None)
    session.pop(_ACCESS_TOKEN_KEY, None)
    session.pop(_REFRESH_TOKEN_KEY, None)
