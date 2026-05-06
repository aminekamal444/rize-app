from __future__ import annotations

from functools import wraps
from typing import Optional

from flask import redirect, session, url_for


_SESSION_KEY = "user_id"


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


def set_user_session(user_id: str) -> None:
    """Store the authenticated user_id in the session."""
    session[_SESSION_KEY] = user_id


def clear_user_session() -> None:
    """Remove the user from the session (logout)."""
    session.pop(_SESSION_KEY, None)
