"""Shared pipeline: given tracks, find sources, download, tag, write files."""

from __future__ import annotations

import threading
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

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
    jobs: int = 1


@dataclass
class TrackResult:
    track: Track
    status: str  # downloaded | skipped | dry-run | failed
    path: Path | None = None
    source_url: str = ""
    detail: str = ""


@dataclass
class _State:
    claimed: set[Path]
    cover_cache: dict[str, tuple[bytes, str] | None]
    claim_lock: threading.Lock
    cover_lock: threading.Lock
    print_lock: threading.Lock

    @classmethod
    def new(cls) -> _State:
        return cls(
            claimed=set(),
            cover_cache={},
            claim_lock=threading.Lock(),
            cover_lock=threading.Lock(),
            print_lock=threading.Lock(),
        )


def target_path(options: TrackOptions, track: Track) -> Path:
    relative = render_template(options.template, track)
    extension = options.audio_format.lower().lstrip(".")
    return Path(options.out_dir).joinpath(*relative.split("/")).with_suffix("." + extension)


def _emit(state: _State, progress: Callable[[str], None], message: str) -> None:
    with state.print_lock:
        progress(message)


def _cover_for(state: _State, track: Track, options: TrackOptions):
    if not options.embed_cover:
        return None
    with state.cover_lock:
        if track.cover_url in state.cover_cache:
            return state.cover_cache[track.cover_url]
    cover = fetch_cover(track)
    with state.cover_lock:
        state.cover_cache.setdefault(track.cover_url, cover)
        return state.cover_cache[track.cover_url]


def _process_one(
    index: int,
    track: Track,
    total: int,
    options: TrackOptions,
    state: _State,
    progress: Callable[[str], None],
) -> TrackResult:
    label = track.display()
    prefix = f"[{index}/{total}] {label}"
    target = target_path(options, track)

    with state.claim_lock:
        is_duplicate = target in state.claimed
        state.claimed.add(target)

    if is_duplicate:
        result = TrackResult(track, "skipped", target, detail="duplicate target in this run")
        _emit(state, progress, f"{prefix} - skipped (duplicate name)")
        return result
    if target.exists() and not options.overwrite:
        result = TrackResult(track, "skipped", target, detail="already exists")
        _emit(state, progress, f"{prefix} - skipped (exists)")
        return result

    try:
        source = find_source(track)
    except StashifyError as exc:
        result = TrackResult(track, "failed", detail=str(exc))
        _emit(state, progress, f"{prefix} - source not found: {exc}")
        return result

    if options.dry_run:
        result = TrackResult(
            track, "dry-run", target, source_url=source.url, detail=source.title
        )
        _emit(state, progress, f"{prefix} - would download: {source.url}")
        return result

    try:
        path = download_audio(
            source,
            target.with_suffix(""),
            audio_format=options.audio_format,
            bitrate=options.bitrate,
        )
    except StashifyError as exc:
        result = TrackResult(track, "failed", source_url=source.url, detail=str(exc))
        _emit(state, progress, f"{prefix} - download failed: {exc}")
        return result

    cover = _cover_for(state, track, options)
    lyrics = fetch_lyrics(track) if options.embed_lyrics else None
    tag_note = ""
    try:
        tag_file(path, track, cover, lyrics)
    except Exception as exc:  # Keep the audio file; only the tags failed.
        tag_note = f" (tags not written: {exc})"

    result = TrackResult(track, "downloaded", path, source_url=source.url, detail=tag_note)
    _emit(state, progress, f"{prefix} - saved: {path}{tag_note}")
    return result


def process_tracks(
    tracks: list[Track],
    options: TrackOptions,
    progress: Callable[[str], None] = print,
) -> list[TrackResult]:
    total = len(tracks)
    state = _State.new()
    jobs = max(1, options.jobs)

    if jobs <= 1:
        return [
            _process_one(index + 1, track, total, options, state, progress)
            for index, track in enumerate(tracks)
        ]

    from concurrent.futures import ThreadPoolExecutor

    results: list[TrackResult | None] = [None] * total
    with ThreadPoolExecutor(max_workers=jobs) as pool:
        futures = {
            pool.submit(_process_one, index + 1, track, total, options, state, progress): index
            for index, track in enumerate(tracks)
        }
        for future, index in futures.items():
            results[index] = future.result()
    return [result for result in results if result is not None]


def summarize(results: list[TrackResult]) -> dict[str, int]:
    counts = {"downloaded": 0, "skipped": 0, "dry-run": 0, "failed": 0}
    for result in results:
        counts[result.status] = counts.get(result.status, 0) + 1
    return counts
