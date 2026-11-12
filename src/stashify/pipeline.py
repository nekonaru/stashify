"""Shared pipeline: given tracks, find sources, download, tag, write files."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Callable

from .download import download_audio
from .errors import StashifyError
from .lyrics import fetch_lyrics
from .models import Track
from .output import render_template
from .sources import find_source
from .tagger import fetch_cover, tag_file


@dataclass
class TrackOptions:
    out_dir: Path
    template: str
    audio_format: str
    bitrate: str
    overwrite: bool = False
    dry_run: bool = False
    embed_cover: bool = True
    embed_lyrics: bool = True


@dataclass
class TrackResult:
    track: Track
    status: str  # downloaded | skipped | dry-run | failed
    path: Path | None = None
    source_url: str = ""
    detail: str = ""


def target_path(options: TrackOptions, track: Track) -> Path:
    relative = render_template(options.template, track)
    extension = options.audio_format.lower().lstrip(".")
    return Path(options.out_dir).joinpath(*relative.split("/")).with_suffix("." + extension)


def process_tracks(
    tracks: list[Track],
    options: TrackOptions,
    progress: Callable[[str], None] = print,
) -> list[TrackResult]:
    results: list[TrackResult] = []
    cover_cache: dict[str, tuple[bytes, str] | None] = {}
    for index, track in enumerate(tracks, start=1):
        label = track.display()
        prefix = f"[{index}/{len(tracks)}] {label}"
        target = target_path(options, track)
        if target.exists() and not options.overwrite:
            results.append(TrackResult(track, "skipped", target, detail="already exists"))
            progress(f"{prefix} - skipped (exists)")
            continue

        try:
            source = find_source(track)
        except StashifyError as exc:
            results.append(TrackResult(track, "failed", detail=str(exc)))
            progress(f"{prefix} - source not found: {exc}")
            continue

        if options.dry_run:
            results.append(
                TrackResult(track, "dry-run", target, source_url=source.url, detail=source.title)
            )
            progress(f"{prefix} - would download: {source.url}")
            continue

        try:
            path = download_audio(
                source,
                target.with_suffix(""),
                audio_format=options.audio_format,
                bitrate=options.bitrate,
            )
        except StashifyError as exc:
            results.append(TrackResult(track, "failed", source_url=source.url, detail=str(exc)))
            progress(f"{prefix} - download failed: {exc}")
            continue

        cover = None
        if options.embed_cover:
            if track.cover_url not in cover_cache:
                cover_cache[track.cover_url] = fetch_cover(track)
            cover = cover_cache[track.cover_url]

        lyrics = fetch_lyrics(track) if options.embed_lyrics else None
        tag_note = ""
        try:
            tag_file(path, track, cover, lyrics)
        except Exception as exc:  # Keep the audio file; only the tags failed.
            tag_note = f" (tags not written: {exc})"

        results.append(
            TrackResult(track, "downloaded", path, source_url=source.url, detail=tag_note)
        )
        progress(f"{prefix} - saved: {path}{tag_note}")
    return results


def summarize(results: list[TrackResult]) -> dict[str, int]:
    counts = {"downloaded": 0, "skipped": 0, "dry-run": 0, "failed": 0}
    for result in results:
        counts[result.status] = counts.get(result.status, 0) + 1
    return counts
