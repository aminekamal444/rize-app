from __future__ import annotations

import base64
import io
from typing import Tuple

from PIL import Image
from werkzeug.datastructures import FileStorage


def compress_to_thumbnail(
    file_storage: FileStorage,
    max_size: int,
    quality: int,
) -> io.BytesIO:
    """
    Open an uploaded image, resize it to fit within max_size x max_size
    (preserving aspect ratio), convert to RGB, and return a JPEG BytesIO
    buffer ready for upload.
    """
    img = Image.open(file_storage.stream)
    img = img.convert("RGB")
    img.thumbnail((max_size, max_size), Image.LANCZOS)

    buffer = io.BytesIO()
    img.save(buffer, format="JPEG", quality=quality, optimize=True)
    buffer.seek(0)
    return buffer


def thumbnail_for_wardrobe(file_storage: FileStorage) -> io.BytesIO:
    """200 x 200, 60 % quality — wardrobe item thumbnails."""
    return compress_to_thumbnail(file_storage, max_size=200, quality=60)


def thumbnail_for_progress(file_storage: FileStorage) -> io.BytesIO:
    """800 x 800, 70 % quality — weekly progress photos."""
    return compress_to_thumbnail(file_storage, max_size=800, quality=70)


def thumbnail_for_baseline(file_storage: FileStorage) -> io.BytesIO:
    """1200 x 1200, 80 % quality — onboarding baseline photos."""
    return compress_to_thumbnail(file_storage, max_size=1200, quality=80)


def to_base64(file_storage: FileStorage) -> Tuple[str, str]:
    """
    Read the uploaded file into memory and return (base64_string, media_type).
    The file is never written to disk — use this before sending to Claude.
    """
    media_type = file_storage.content_type or "image/jpeg"
    data = file_storage.read()
    b64 = base64.standard_b64encode(data).decode("utf-8")
    return b64, media_type
