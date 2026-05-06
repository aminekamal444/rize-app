from __future__ import annotations

import json
import os
import re
from functools import lru_cache
from typing import Optional

import anthropic

_MODEL_VISION = "claude-haiku-4-5-20251001"
_MODEL_TEXT = "claude-haiku-4-5-20251001"


@lru_cache(maxsize=1)
def get_claude() -> anthropic.Anthropic:
    """Return a cached Anthropic client."""
    return anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])


def ask_claude(prompt: str, max_tokens: int = 1000) -> str:
    """Send a text-only prompt and return the response string."""
    client = get_claude()
    message = client.messages.create(
        model=_MODEL_TEXT,
        max_tokens=max_tokens,
        messages=[{"role": "user", "content": prompt}],
    )
    return message.content[0].text


def ask_claude_vision(
    prompt: str,
    image_base64: str,
    media_type: str,
    max_tokens: int = 1500,
) -> str:
    """Send a prompt with an attached image and return the response string."""
    client = get_claude()
    message = client.messages.create(
        model=_MODEL_VISION,
        max_tokens=max_tokens,
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": media_type,
                            "data": image_base64,
                        },
                    },
                    {"type": "text", "text": prompt},
                ],
            }
        ],
    )
    return message.content[0].text


def ask_claude_json(
    prompt: str,
    max_tokens: int = 600,
    image_base64: Optional[str] = None,
    media_type: Optional[str] = None,
) -> dict:
    """
    Send a prompt expecting a JSON response.

    Strips markdown code fences if present, parses the JSON, and returns
    the dict. Raises ValueError if the response cannot be parsed.
    """
    if image_base64 and media_type:
        raw = ask_claude_vision(prompt, image_base64, media_type, max_tokens)
    else:
        raw = ask_claude(prompt, max_tokens)

    # Strip code fences Claude sometimes adds despite instructions
    cleaned = re.sub(r"^```(?:json)?\s*|\s*```$", "", raw.strip(), flags=re.MULTILINE).strip()

    try:
        return json.loads(cleaned)
    except json.JSONDecodeError as exc:
        raise ValueError(f"Claude returned non-JSON: {cleaned[:200]}") from exc
