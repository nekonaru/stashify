"""Find the best audio source for a Spotify track.

YouTube is the first choice. SoundCloud is the fallback used when YouTube
yields nothing acceptable. Search results are scored with a transparent
heuristic: duration closeness and word overlap between the Spotify metadata
and the video title. The highest scoring candidate wins.

SoundCloud is stricter about duration because unlicensed previews are 30
seconds long; a preview must never be saved as the track.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

import yt_dlp

from .models import Track

SEARCH_COUNT = 8
MIN_ACCEPT_SCORE = 30
SOUNDCLOUD_MAX_DURATION_DIFF = 15.0

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
    provider: str = "youtube"


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


_YT_OPTIONS = {
    "quiet": True,
    "no_warnings": True,
    "skip_download": True,
    "extract_flat": True,
    "default_search": "ytsearch",
}
_SC_OPTIONS = {
    "quiet": True,
    "no_warnings": True,
    "skip_download": True,
    "extract_flat": True,
    "default_search": "scsearch",
}


def _entries_for(
    prefix: str,
    query: str,
    options: dict,
    cookies_from_browser: str | None,
) -> list[dict]:
    call_options = dict(options)
    call_options["default_search"] = prefix
    if cookies_from_browser:
        call_options["cookiesfrombrowser"] = (cookies_from_browser,)
    try:
        with yt_dlp.YoutubeDL(call_options) as ydl:
            result = ydl.extract_info(f"{prefix}{SEARCH_COUNT}:{query}", download=False)
    except Exception as exc:  # yt-dlp raises many error types; surface one clear message.
        from .errors import SourceNotFoundError

        raise SourceNotFoundError(f"Could not search {prefix}: {exc}") from exc
    return (result or {}).get("entries") or []


def _youtube_entries(query: str, cookies_from_browser: str | None) -> list[dict]:
    return _entries_for("ytsearch", query, _YT_OPTIONS, cookies_from_browser)


def _soundcloud_entries(query: str, cookies_from_browser: str | None) -> list[dict]:
    return _entries_for("scsearch", query, _SC_OPTIONS, cookies_from_browser)


def _pick_best(track: Track, entries: list[dict], provider: str) -> Source | None:
    best: Source | None = None
    for entry in entries:
        if not entry:
            continue
        url = entry.get("url") or entry.get("id")
        if not url:
            continue
        if not str(url).startswith("http"):
            if provider == "soundcloud":
                url = f"https://soundcloud.com/{url}"
            else:
                url = f"https://www.youtube.com/watch?v={url}"
        duration = entry.get("duration")
        duration_seconds = float(duration) if duration is not None else None
        candidate = Source(
            url=str(url),
            title=entry.get("title") or "",
            channel=(entry.get("channel") or entry.get("uploader") or ""),
            duration_seconds=duration_seconds,
            provider=provider,
        )
        candidate.score = score_candidate(track, candidate.title, candidate.duration_seconds)
        if best is None or candidate.score > best.score:
            best = candidate
    return best


def _acceptable_youtube(best: Source | None, track: Track) -> Source | None:
    if best is None or best.score < MIN_ACCEPT_SCORE:
        return None
    if best.duration_seconds is not None and track.duration_ms > 0:
        diff = abs(best.duration_seconds - track.duration_ms / 1000.0)
        if diff > 120:
            # A mismatch this big (e.g. a 10 hour loop) is never the track.
            return None
    return best


def _acceptable_soundcloud(best: Source | None, track: Track) -> Source | None:
    if best is None or best.score < MIN_ACCEPT_SCORE:
        return None
    if best.duration_seconds is None:
        # Without a duration we cannot reject 30-second previews.
        return None
    if track.duration_ms > 0:
        expected = track.duration_ms / 1000.0
        if abs(best.duration_seconds - expected) > SOUNDCLOUD_MAX_DURATION_DIFF:
            # SoundCloud is the fallback; 30-second previews must not pass.
            return None
    return best


def find_source(
    track: Track,
    search_count: int = SEARCH_COUNT,
    cookies_from_browser: str | None = None,
) -> Source:
    query = track.search_query()

    try:
        youtube_entries = _youtube_entries(query, cookies_from_browser)
        if not youtube_entries:
            # YouTube sometimes returns nothing for the plain "artist - title" query.
            youtube_entries = _youtube_entries(
                f"{track.artists_text} {track.title}", cookies_from_browser
            )
        if not youtube_entries:
            youtube_entries = _youtube_entries(
                f"{track.artists_text} {track.title} audio", cookies_from_browser
            )
    except Exception:
        youtube_entries = []  # YouTube blocked/unavailable; try SoundCloud instead.

    best = _pick_best(track, youtube_entries, "youtube")
    accepted = _acceptable_youtube(best, track)
    if accepted:
        return accepted

    # Fallback: SoundCloud. Used only when YouTube yields nothing acceptable.
    soundcloud_entries = _soundcloud_entries(query, cookies_from_browser)
    if not soundcloud_entries:
        soundcloud_entries = _soundcloud_entries(
            f"{track.artists_text} {track.title} audio", cookies_from_browser
        )
    fallback = _pick_best(track, soundcloud_entries, "soundcloud")
    accepted = _acceptable_soundcloud(fallback, track)
    if accepted:
        return accepted

    from .errors import SourceNotFoundError

    if best is None:
        if fallback is None:
            raise SourceNotFoundError(
                f"No results from YouTube or SoundCloud for {track.display()!r}."
            )
        raise SourceNotFoundError(
            f"Only SoundCloud previews found for {track.display()!r} "
            f"(best score {fallback.score:.0f}, duration {fallback.duration_seconds or 0:.0f}s)."
        )
    raise SourceNotFoundError(
        f"Best YouTube match for {track.display()!r} looks unreliable "
        f"(score {best.score:.0f}). SoundCloud offers no better candidate. "
        "Try the full URL instead."
    )
