"""Check that the whole Stashify stack works end to end.

`stashify doctor` runs quick checks against Python, FFmpeg, the downloads
folder, Spotify's embed pages, YouTube search and the lyrics API, and prints
a pass/fail report. Use when a download fails and you want to know exactly
which part of the stack is broken, without running a full download.
"""

from __future__ import annotations

import shutil

import requests

from .config import default_download_dir
from .embed import EmbedResolver
from .lyrics import LRCLIB_URL
from .lyrics import USER_AGENT as LYRICS_UA
from .models import Track
from .sources import find_source


def check_python() -> tuple[str, bool, str]:
    import sys

    ok = sys.version_info >= (3, 10)
    label = "Python 3.10 or newer"
    return (label, ok, f"Python {sys.version_info.major}.{sys.version_info.minor}")


def check_ffmpeg() -> tuple[str, bool, str]:
    ffmpeg = shutil.which("ffmpeg")
    path = "FFmpeg on PATH"
    return (path, bool(ffmpeg), ffmpeg or "not found (https://ffmpeg.org/download.html)")


def check_ffprobe() -> tuple[str, bool, str]:
    ffprobe = shutil.which("ffprobe")
    path = "ffprobe on PATH"
    return (path, bool(ffprobe), ffprobe or "not found (comes with FFmpeg)")


def check_download_dir() -> tuple[str, bool, str]:
    folder = default_download_dir()
    detail = str(folder)
    try:
        folder.mkdir(parents=True, exist_ok=True)
        probe = folder / ".stashify-doctor-write-test"
        probe.write_text("ok", encoding="utf-8")
        probe.unlink()
    except OSError as exc:
        return ("Downloads folder writable", False, f"{folder}: {exc}")
    return ("Downloads folder writable", True, detail)


def check_spotify_embed() -> tuple[str, bool, str]:
    try:
        resolver = EmbedResolver(detailed=False)
        tracks = resolver.fetch_tracks(
            "https://open.spotify.com/track/4uLU6hMCjMI75M1A2tKUQC"
        )
    except Exception as exc:
        return ("Spotify embed pages", False, f"failed: {exc}")
    if not tracks:
        return ("Spotify embed pages", False, "embed resolved to no tracks")
    return ("Spotify embed pages", True, f"resolved: {tracks[0].display()}")


def check_youtube() -> tuple[str, bool, str]:
    try:
        source = find_source(
            Track(
                title="Never Gonna Give You Up",
                artists=["Rick Astley"],
                duration_ms=213000,
            )
        )
    except Exception as exc:
        return ("YouTube search", False, f"failed: {exc}")
    return ("YouTube search", True, f"matched: {source.title or source.url}")


def check_lyrics_api() -> tuple[str, bool, str]:
    try:
        response = requests.get(
            LRCLIB_URL,
            params={"artist_name": "Rick Astley", "track_name": "Never Gonna Give You Up"},
            timeout=10,
            headers={"User-Agent": LYRICS_UA},
        )
    except requests.RequestException as exc:
        return ("Lyrics API (lrclib.net)", False, f"failed: {exc}")
    ok = response.status_code == 200
    detail = "reachable" if ok else f"HTTP {response.status_code}"
    return ("Lyrics API (lrclib.net)", ok, detail)


def run_doctor() -> int:
    checks = [
        check_python,
        check_ffmpeg,
        check_ffprobe,
        check_download_dir,
        check_spotify_embed,
        check_youtube,
        check_lyrics_api,
    ]
    results = [check() for check in checks]

    width = max(len(label) for label, _, _ in results)
    failures = 0
    for label, ok, detail in results:
        failures += 0 if ok else 1
        mark = "OK  " if ok else "FAIL"
        print(f"{mark} {label:<{width}}  {detail}")

    print()
    if failures:
        print(f"{failures} of {len(results)} checks failed. Fix the items above and try again.")
        return 1
    print(f"All {len(results)} checks passed. Stashify is ready to run.")
    return 0
