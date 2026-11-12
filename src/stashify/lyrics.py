"""Fetch plain-text lyrics from a free community lyrics API.

Returns None on any failure; lyrics are always optional and must never block
a download.
"""

from __future__ import annotations

import requests

from .models import Track

API_URL = "https://api.lyrics.ovh/v1"
TIMEOUT = 10
MAX_LYRICS_BYTES = 64 * 1024


def fetch_lyrics(track: Track) -> str | None:
    artist = requests.utils.quote(track.artist, safe="")
    title = requests.utils.quote(track.title, safe="")
    try:
        response = requests.get(
            f"{API_URL}/{artist}/{title}", timeout=TIMEOUT
        )
    except requests.RequestException:
        return None
    if response.status_code != 200:
        return None
    if len(response.content) > MAX_LYRICS_BYTES:
        return None
    try:
        lyrics = (response.json() or {}).get("lyrics") or ""
    except ValueError:
        return None
    lyrics = lyrics.strip()
    return lyrics or None
