"""Find the best YouTube source for a Spotify track.

Search results are scored with a transparent heuristic: duration closeness
and word overlap between the Spotify metadata and the video title. The
highest scoring candidate wins. Everything here is plain Python, no code is
fetched or executed from anywhere.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

import yt_dlp

from .models import Track

SEARCH_COUNT = 8
MIN_ACCEPT_SCORE = 30

_WORD_RE = re.compile(r"[a-z0-9]{3,}")
_PENALTY_TERMS = (
    "karaoke", "cover", "reaction", "remix",
    "live", "instrumental", "sped up", "slowed",
)


@dataclass
class Source:
    url: str
    title: str = ""
    channel: str = ""
    duration_seconds: float | None = None
    score: float = 0.0


def _words(text: str) -> set[str]:
    return set(_WORD_RE.findall((text or "").lower()))


def score_candidate(track: Track, candidate_title: str, duration_seconds: float | None) -> float:
    score = 100.0

    if duration_seconds is not None and track.duration_ms > 0:
        diff = abs(duration_seconds - track.duration_ms / 1000.0)
        if diff <= 2:
            score += 50
        elif diff <= 10:
            score += 20
        elif diff <= 30:
            score += 0
        else:
            score -= 60

    candidate_words = _words(candidate_title)
    wanted = _words(track.search_query())
    overlap = len(wanted & candidate_words)
    score += min(5 * overlap, 25)

    lowered = (candidate_title or "").lower()
    for term in _PENALTY_TERMS:
        # Keep the penalty off when the track itself asks for that kind of version.
        if term in lowered and term not in _words(track.search_query()):
            score -= 40
    if "official" in lowered:
        score += 10

    return score


def _search_entries(query: str, search_count: int) -> list[dict]:
    options = {
        "quiet": True,
        "no_warnings": True,
        "skip_download": True,
        "extract_flat": True,
        "default_search": "ytsearch",
    }
    try:
        with yt_dlp.YoutubeDL(options) as ydl:
            result = ydl.extract_info(f"ytsearch{search_count}:{query}", download=False)
    except Exception as exc:  # yt-dlp raises many error types; surface one clear message.
        from .errors import SourceNotFoundError

        raise SourceNotFoundError(f"Could not search YouTube: {exc}") from exc
    return (result or {}).get("entries") or []


def find_source(track: Track, search_count: int = SEARCH_COUNT) -> Source:
    query = track.search_query()
    entries = _search_entries(query, search_count)
    if not entries:
        # YouTube sometimes returns nothing for the plain "artist - title" query.
        entries = _search_entries(f"{track.artists_text} {track.title}", search_count)
    if not entries:
        entries = _search_entries(
            f"{track.artists_text} {track.title} audio", search_count
        )

    best: Source | None = None
    for entry in entries:
        if not entry:
            continue
        url = entry.get("url") or entry.get("id")
        if not url:
            continue
        if not str(url).startswith("http"):
            url = f"https://www.youtube.com/watch?v={url}"
        duration = entry.get("duration")
        title = entry.get("title") or ""
        candidate = Source(
            url=str(url),
            title=title,
            channel=(entry.get("channel") or entry.get("uploader") or ""),
            duration_seconds=float(duration) if duration is not None else None,
        )
        candidate.score = score_candidate(track, candidate.title, candidate.duration_seconds)
        if best is None or candidate.score > best.score:
            best = candidate

    from .errors import SourceNotFoundError

    if best is None:
        raise SourceNotFoundError(f"No YouTube results for {track.display()!r}.")
    if best.score < MIN_ACCEPT_SCORE:
        raise SourceNotFoundError(
            f"Best YouTube match for {track.display()!r} looks unreliable "
            f"(score {best.score:.0f}). Try the full URL instead."
        )
    return best
