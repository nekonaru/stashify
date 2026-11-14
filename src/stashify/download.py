"""Download audio with yt-dlp and convert it with FFmpeg."""

from __future__ import annotations

import json
import re
import shutil
import subprocess
from pathlib import Path

import yt_dlp

from .errors import DownloadError
from .models import Track
from .sources import Source

LOSSLESS_FORMATS = {"flac", "wav"}
AUDIO_FORMATS = {"mp3", "m4a", "opus", "flac", "wav"}

_CODEC_MAP = {
    "mp3": "mp3",
    "m4a": "m4a",
    "opus": "opus",
    "flac": "flac",
    "wav": "wav",
}

_BITRATE_RE = re.compile(r"^\d{2,4}k?$", re.IGNORECASE)


def validate_bitrate(bitrate: str) -> str:
    """Validate a bitrate like 128k, 192k, 320k. Raises DownloadError if bad."""
    text = (bitrate or "").strip().lower()
    if not _BITRATE_RE.match(text):
        raise DownloadError(
            f"Invalid bitrate {bitrate!r}. Use something like 128k, 192k or 320k."
        )
    return text


def ffmpeg_available() -> bool:
    return shutil.which("ffmpeg") is not None


def _ffprobe_duration(path: Path, ffprobe: str | None = None) -> float:
    """Run ffprobe and return the stream duration in seconds."""
    ffprobe = ffprobe or shutil.which("ffprobe")
    if ffprobe is None:
        raise DownloadError(
            "ffprobe was not found on PATH. Install FFmpeg first: "
            "https://ffmpeg.org/download.html"
        )
    command = [
        ffprobe,
        "-v", "error",
        "-show_entries", "format=duration",
        "-of", "json",
        str(path),
    ]
    try:
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=30,
            check=False,
        )
    except FileNotFoundError as exc:
        raise DownloadError("ffprobe is not runnable on this system.") from exc
    except subprocess.TimeoutExpired as exc:
        raise DownloadError(f"ffprobe timed out on {path}.") from exc
    if result.returncode != 0:
        detail = (result.stderr or "unknown error").strip()
        raise DownloadError(f"ffprobe could not read {path}: {detail}")
    try:
        payload = json.loads(result.stdout or "{}")
        return float(payload["format"]["duration"])
    except (ValueError, KeyError) as exc:
        raise DownloadError(f"ffprobe returned no duration for {path}.") from exc


def verify_media(
    path: Path,
    track: Track | None,
    tolerance: float = 0.20,
    minimum_seconds: float = 20.0,
) -> tuple[bool, str]:
    """Verify a downloaded audio file is readable and roughly the right length.

    Returns (ok, detail). ``ok`` is False only when the file is confirmed
    corrupt or missing (caller should delete it and report the track as
    failed). Environment problems (ffprobe unavailable, timed out) never delete
    the file; they produce (True, "could not verify ...") so working downloads
    are kept. ``detail`` carries a human-readable summary.
    """
    file_path = Path(path)
    if not file_path.is_file():
        return False, "file is missing"
    if file_path.stat().st_size == 0:
        return False, "file is empty"
    ffprobe = shutil.which("ffprobe")
    if ffprobe is None:
        return True, "could not verify (ffprobe not found on PATH)"
    try:
        duration = _ffprobe_duration(file_path, ffprobe)
    except DownloadError as exc:
        text = str(exc).lower()
        # Infrastructure failures keep the file; unreadable files are corrupt.
        if "ffprobe was not found" in text or "ffprobe timed out" in text:
            return True, f"could not verify ({exc})"
        return False, str(exc)
    if track is not None and track.duration_ms > 0:
        expected = track.duration_ms / 1000.0
        allowed = max(minimum_seconds, expected * tolerance)
        diff = abs(duration - expected)
        if diff > allowed:
            return True, f"duration mismatch (expected {expected:.0f}s, got {duration:.0f}s)"
    return True, f"verified ({duration:.0f}s)"



def download_audio(
    source: Source,
    output_base: Path,
    audio_format: str = "mp3",
    bitrate: str = "192k",
    cookies_from_browser: str | None = None,
) -> Path:
    """Download source audio and convert to audio_format.

    output_base is the target path without extension. Returns the final path.
    `cookies_from_browser` is passed to yt-dlp so authenticated browsing
    sessions can bypass YouTube bot checks.
    """
    audio_format = audio_format.lower()
    if audio_format not in AUDIO_FORMATS:
        raise DownloadError(
            f"Unsupported audio format {audio_format!r}. "
            f"Choose from: {', '.join(sorted(AUDIO_FORMATS))}."
        )
    bitrate = validate_bitrate(bitrate)
    if not ffmpeg_available():
        raise DownloadError(
            "FFmpeg was not found on PATH. Install FFmpeg first: "
            "https://ffmpeg.org/download.html"
        )

    output_base = Path(output_base)
    output_base.parent.mkdir(parents=True, exist_ok=True)

    options = {
        "quiet": True,
        "no_warnings": True,
        "format": "bestaudio/best",
        "outtmpl": str(output_base) + ".%(ext)s",
        "noplaylist": True,
        "postprocessors": [
            {
                "key": "FFmpegExtractAudio",
                "preferredcodec": _CODEC_MAP[audio_format],
                "preferredquality": (
                    "0" if audio_format in LOSSLESS_FORMATS
                    else bitrate.rstrip("k")
                ),
            }
        ],
    }
    if cookies_from_browser:
        options["cookiesfrombrowser"] = (cookies_from_browser,)
    try:
        with yt_dlp.YoutubeDL(options) as ydl:
            ydl.download([source.url])
    except Exception as exc:  # yt-dlp raises many error types; surface one clear message.
        raise DownloadError(
            f"Could not download {source.url}: {exc}"
        ) from exc

    expected = output_base.with_suffix("." + audio_format)
    if expected.exists():
        return expected
    # Fall back: pick up whatever the postprocessor produced.
    candidates = sorted(
        output_base.parent.glob(output_base.name + ".*"),
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )
    if candidates:
        return candidates[0]
    raise DownloadError(f"Download finished but no output file was produced for {output_base}")
