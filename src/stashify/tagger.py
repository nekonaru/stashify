"""Write Spotify metadata into audio files.

Supported containers: MP3, M4A, FLAC, OGG/Opus and WAV (ID3). Cover art and
plain-text lyrics are embedded when available.
"""

from __future__ import annotations

import base64
import re
from pathlib import Path

import requests
from mutagen import File as MutagenFile
from mutagen.flac import FLAC, Picture
from mutagen.mp4 import MP4, MP4Cover
from mutagen.oggopus import OggOpus

from .errors import StashifyError
from .models import Track

COVER_TIMEOUT = 15
MAX_COVER_BYTES = 20 * 1024 * 1024
_MIME_BY_SUFFIX = {"jpg": "image/jpeg", "jpeg": "image/jpeg", "png": "image/png"}


def fetch_cover(track: Track) -> tuple[bytes, str] | None:
    if not track.cover_url:
        return None
    try:
        response = requests.get(track.cover_url, timeout=COVER_TIMEOUT, stream=True)
    except requests.RequestException:
        return None
    if response.status_code != 200:
        return None
    content_type = (response.headers.get("Content-Type") or "").split(";")[0].strip().lower()
    if content_type and not content_type.startswith("image/"):
        return None
    chunks: list[bytes] = []
    size = 0
    for chunk in response.iter_content(chunk_size=64 * 1024):
        size += len(chunk)
        if size > MAX_COVER_BYTES:
            return None
        chunks.append(chunk)
    data = b"".join(chunks)
    if not data:
        return None
    mime = content_type if content_type.startswith("image/") else _mime_guess(data)
    return data, mime


def _mime_guess(data: bytes) -> str:
    if data.startswith(b"\x89PNG"):
        return "image/png"
    return "image/jpeg"


def tag_file(path: Path, track: Track, cover: tuple[bytes, str] | None, lyrics: str | None) -> None:
    path = Path(path)
    suffix = path.suffix.lower()
    if suffix == ".mp3":
        _tag_id3(path, track, cover, lyrics)
    elif suffix == ".m4a":
        _tag_mp4(path, track, cover, lyrics)
    elif suffix == ".flac":
        _tag_flac(path, track, cover, lyrics)
    elif suffix == ".opus":
        _tag_opus(path, track, cover, lyrics)
    elif suffix == ".wav":
        _tag_id3(path, track, cover, lyrics)
    else:
        # Fall back to whatever mutagen detects, and fail clearly if nothing does.
        audio = MutagenFile(path)
        if audio is None:
            raise StashifyError(f"Unsupported audio container: {path.suffix}")
        _assign_simple(audio, track, lyrics)


# ID3 (MP3, WAV) ----------------------------------------------------------

def _id3_frames(track: Track, lyrics: str | None) -> dict:
    frames: dict = {}
    frames["TIT2"] = track.title
    frames["TPE1"] = track.artists_text
    frames["TPE2"] = track.album_artist or track.artist
    frames["TALB"] = track.album
    if track.track_number:
        frames["TRCK"] = (
            f"{track.track_number}/{track.total_tracks}"
            if track.total_tracks
            else str(track.track_number)
        )
    if track.disc_number:
        frames["TPOS"] = str(track.disc_number)
    year = _release_year(track.release_date)
    if year:
        frames["TDRC"] = year
    if track.isrc:
        frames["TSRC"] = track.isrc
    if lyrics:
        frames["USLT"] = lyrics
    return frames


def _tag_id3(path: Path, track: Track, cover: tuple[bytes, str] | None, lyrics: str | None) -> None:
    from mutagen.id3 import APIC, ID3, TIT2, TPE1, TPE2, TALB, TRCK, TPOS, TDRC, TSRC, USLT

    audio = MP3_or_WAVE(path)
    try:
        audio.add_tags()
    except Exception:
        pass  # Tags already exist.

    tags = audio.tags
    frames = _id3_frames(track, lyrics)
    for key, value in frames.items():
        if key == "TIT2":
            tags.delall("TIT2"); tags.add(TIT2(encoding=3, text=value))
        elif key == "TPE1":
            tags.delall("TPE1"); tags.add(TPE1(encoding=3, text=value))
        elif key == "TPE2":
            tags.delall("TPE2"); tags.add(TPE2(encoding=3, text=value))
        elif key == "TALB":
            tags.delall("TALB"); tags.add(TALB(encoding=3, text=value))
        elif key == "TRCK":
            tags.delall("TRCK"); tags.add(TRCK(encoding=3, text=value))
        elif key == "TPOS":
            tags.delall("TPOS"); tags.add(TPOS(encoding=3, text=value))
        elif key == "TDRC":
            tags.delall("TDRC"); tags.add(TDRC(encoding=3, text=value))
        elif key == "TSRC":
            tags.delall("TSRC"); tags.add(TSRC(encoding=3, text=value))
        elif key == "USLT":
            tags.delall("USLT")
            tags.add(USLT(encoding=3, lang="eng", desc="", text=value))

    if cover is not None:
        data, mime = cover
        tags.delall("APIC")
        tags.add(APIC(encoding=3, mime=mime, type=3, desc="Cover", data=data))
    audio.save()


def MP3_or_WAVE(path: Path):
    from mutagen.id3 import ID3
    from mutagen.mp3 import MP3
    from mutagen.wave import WAVE

    if path.suffix.lower() == ".wav":
        return WAVE(str(path))
    return MP3(str(path), ID3=ID3)


# M4A ---------------------------------------------------------------------

def _tag_mp4(path: Path, track: Track, cover: tuple[bytes, str] | None, lyrics: str | None) -> None:
    audio = MP4(str(path))
    audio["\xa9nam"] = [track.title]
    audio["\xa9ART"] = list(track.artists) or [track.artist]
    audio["\xa9alb"] = [track.album]
    audio["aART"] = [track.album_artist or track.artist]
    if track.track_number:
        audio["trkn"] = [(track.track_number, track.total_tracks or 0)]
    if track.disc_number:
        audio["disk"] = [(track.disc_number, 0)]
    year = _release_year(track.release_date)
    if year:
        audio["\xa9day"] = [year]
    if track.isrc:
        audio["----:com.apple.iTunes:ISRC"] = [track.isrc.encode("utf-8")]
    if lyrics:
        audio["\xa9lyr"] = [lyrics]
    if cover is not None:
        data, mime = cover
        fmt = MP4Cover.FORMAT_PNG if mime == "image/png" else MP4Cover.FORMAT_JPEG
        audio["covr"] = [MP4Cover(data, imageformat=fmt)]
    audio.save()


# FLAC --------------------------------------------------------------------

def _vorbis_common(audio, track: Track, lyrics: str | None) -> None:
    audio["TITLE"] = [track.title]
    audio["ARTIST"] = list(track.artists) or [track.artist]
    audio["ALBUM"] = [track.album]
    audio["ALBUMARTIST"] = [track.album_artist or track.artist]
    if track.track_number:
        audio["TRACKNUMBER"] = [str(track.track_number)]
        if track.total_tracks:
            audio["TRACKTOTAL"] = [str(track.total_tracks)]
    audio["DISCNUMBER"] = [str(track.disc_number or 1)]
    year = _release_year(track.release_date)
    if year:
        audio["DATE"] = [year]
    if track.isrc:
        audio["ISRC"] = [track.isrc]
    if lyrics:
        audio["LYRICS"] = [lyrics]


def _make_picture(cover: tuple[bytes, str]) -> Picture:
    data, mime = cover
    picture = Picture()
    picture.type = 3
    picture.mime = mime
    picture.desc = "Cover"
    picture.data = data
    return picture


def _tag_flac(path: Path, track: Track, cover: tuple[bytes, str] | None, lyrics: str | None) -> None:
    audio = FLAC(str(path))
    _vorbis_common(audio, track, lyrics)
    if cover is not None:
        audio.clear_pictures()
        audio.add_picture(_make_picture(cover))
    audio.save()


# OGG / Opus ----------------------------------------------------------------

def _tag_opus(path: Path, track: Track, cover: tuple[bytes, str] | None, lyrics: str | None) -> None:
    audio = OggOpus(str(path))
    _vorbis_common(audio, track, lyrics)
    if cover is not None:
        encoded = base64.b64encode(_make_picture(cover).write()).decode("ascii")
        audio["METADATA_BLOCK_PICTURE"] = [encoded]
    audio.save()


# Helpers -------------------------------------------------------------------

def _assign_simple(audio, track: Track, lyrics: str | None) -> None:
    """Best-effort tagging for containers without a dedicated path."""
    try:
        audio["TIT2"] = track.title
    except Exception:
        pass
    audio.save()


def _release_year(release_date: str) -> str:
    match = re.match(r"^(\d{4})", release_date or "")
    return match.group(1) if match else ""
