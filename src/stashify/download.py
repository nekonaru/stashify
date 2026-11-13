"""Download audio with yt-dlp and convert it with FFmpeg."""

from __future__ import annotations

import re
import shutil
from pathlib import Path

import yt_dlp

from .errors import DownloadError
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


def download_audio(
    source: Source,
    output_base: Path,
    audio_format: str = "mp3",
    bitrate: str = "192k",
) -> Path:
    """Download source audio and convert to audio_format.

    output_base is the target path without extension. Returns the final path.
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
