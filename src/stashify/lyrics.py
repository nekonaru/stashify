"""Fetch plain-text lyrics, lrclib first, community fallback.

Returns None on any failure; lyrics are always optional and must never block
a download.
"""

from __future__ import annotations

import requests

from .models import Track

LRCLIB_URL = "https://lrclib.net/api/get"
OVH_URL = "https://api.lyrics.ovh/v1"
TIMEOUT = 10
MAX_LYRICS_BYTES = 256 * 1024
USER_AGENT = "stashify/1.4 (https://github.com/nekonaru/stashify)"


def _fetch_lrclib(track: Track) -> str | None:
    params = {
        "artist_name": track.artist,
        "track_name": track.title,
    }
    if track.album:
        params["album_name"] = track.album
    if track.duration_ms:
        params["duration"] = int(track.duration_ms // 1000)
    try:
        response = requests.get(
            LRCLIB_URL, params=params, timeout=TIMEOUT,
            headers={"User-Agent": USER_AGENT},
        )
    except requests.RequestException:
        return None
    if response.status_code != 200:
        return None
    if len(response.content) > MAX_LYRICS_BYTES:
        return None
    try:
        lyrics = (response.json() or {}).get("plainLyrics") or ""
    except ValueError:
        return None
    return lyrics.strip() or None


def _fetch_ovh(track: Track) -> str | None:
    artist = requests.utils.quote(track.artist, safe="")
    title = requests.utils.quote(track.title, safe="")
    try:
        response = requests.get(f"{OVH_URL}/{artist}/{title}", timeout=TIMEOUT)
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
    return lyrics.strip() or None


def fetch_lyrics(track: Track) -> str | None:
    return _fetch_lrclib(track) or _fetch_ovh(track)
