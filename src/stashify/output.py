"""Output path rendering and safe file naming."""

from __future__ import annotations

import re

from .models import Track

DEFAULT_TEMPLATE = "{artist} - {title}"
MAX_SEGMENT = 120

_ILLEGAL = re.compile(r'[<>:"/\\|?*\x00-\x1f]')
_SPACES = re.compile(r"\s+")
_TOKENS = re.compile(r"\{([a-z_]+)\}")


def release_year(track: Track) -> str:
    match = re.match(r"^(\d{4})", track.release_date or "")
    return match.group(1) if match else ""


def safe_segment(text: str) -> str:
    text = _ILLEGAL.sub("", text or "")
    text = _SPACES.sub(" ", text).strip().strip(".")
    text = text[:MAX_SEGMENT].rstrip(" .")
    return text


def _token_value(name: str, track: Track) -> str:
    values = {
        "artist": track.artist,
        "artists": track.artists_text,
        "title": track.title,
        "album": track.album,
        "album_artist": track.album_artist or track.artist,
        "track_number": str(track.track_number) if track.track_number else "",
        "disc_number": str(track.disc_number) if track.disc_number else "",
        "release_year": release_year(track),
    }
    return values.get(name, "")


def render_template(template: str, track: Track) -> str:
    """Render a path template into a relative, safe path string."""
    template = template or DEFAULT_TEMPLATE

    def replace(match: re.Match) -> str:
        value = _token_value(match.group(1), track)
        return value.replace("/", "-").replace("\\", "-")

    rendered = _TOKENS.sub(replace, template)
    parts = []
    for segment in rendered.split("/"):
        cleaned = safe_segment(segment)
        if cleaned:
            parts.append(cleaned)
    if not parts:
        parts = [safe_segment(f"{track.artist} - {track.title}")]
    return "/".join(parts)
