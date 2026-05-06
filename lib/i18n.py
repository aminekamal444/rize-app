from __future__ import annotations

import json
import os
from typing import Optional

from flask import session

_SUPPORTED_LANGUAGES = ("fr", "en", "ar")
_DEFAULT_LANGUAGE = "fr"
_RTL_LANGUAGES = {"ar"}

_translations: Optional[dict] = None


def _load_translations() -> dict:
    global _translations
    if _translations is None:
        path = os.path.join(os.path.dirname(__file__), "translations.json")
        with open(path, encoding="utf-8") as f:
            _translations = json.load(f)
    return _translations


def get_language() -> str:
    """
    Return the active language code for the current request.

    Priority: session["lang"] > profile (not yet wired in Phase 1) > default (fr).
    """
    lang = session.get("lang", _DEFAULT_LANGUAGE)
    if lang not in _SUPPORTED_LANGUAGES:
        lang = _DEFAULT_LANGUAGE
    return lang


def t(key: str) -> str:
    """
    Look up a translation key for the current request's language.

    Returns the key itself if the translation is missing, so missing keys
    are visible in the UI without crashing.
    """
    translations = _load_translations()
    lang = get_language()
    entry = translations.get(key)
    if entry is None:
        return key
    return entry.get(lang) or entry.get(_DEFAULT_LANGUAGE) or key


def is_rtl() -> bool:
    """Return True when the current language renders right-to-left."""
    return get_language() in _RTL_LANGUAGES
