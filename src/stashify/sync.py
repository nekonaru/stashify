"""State files for keeping a local directory in sync with a playlist.

The state file is plain JSON. It records which tracks were downloaded into
which paths, so a later `stashify sync` can add new songs and remove files
that disappeared from the playlist, without touching anything else the user
put in the folder.
"""

from __future__ import annotations

import json
from pathlib import Path

from .errors import StashifyError
from .models import Track

STATE_VERSION = 1


def track_key(track: Track) -> str:
    if track.spotify_url:
        return track.spotify_url
    return f"{track.artist}-{track.album}-{track.title}-{track.track_number}"


def load_state(path: Path) -> dict:
    path = Path(path)
    if not path.exists():
        return {"version": STATE_VERSION, "url": "", "entries": []}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise StashifyError(f"Could not read state file {path}: {exc}") from exc
    if not isinstance(data, dict) or not isinstance(data.get("entries", []), list):
        raise StashifyError(f"State file {path} is not a Stashify state file.")
    data.setdefault("version", STATE_VERSION)
    data.setdefault("url", "")
    data.setdefault("entries", [])
    return data


def save_state(path: Path, state: dict) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(state, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )


def plan_sync(state: dict, current: list[Track]) -> tuple[list[Track], list[dict]]:
    """Return (tracks to download, entries to remove)."""
    current_keys = {track_key(t) for t in current}
    existing = {entry.get("key"): entry for entry in state.get("entries", [])}
    missing = [t for t in current if track_key(t) not in existing]
    removed = [entry for key, entry in existing.items() if key not in current_keys]
    return missing, removed


def remove_entries(removed: list[dict], out_dir: Path) -> list[str]:
    """Delete files referenced by removed entries, confined to out_dir."""
    out_dir = Path(out_dir).resolve()
    deleted: list[str] = []
    for entry in removed:
        rel = entry.get("path")
        if not rel:
            continue
        candidate = (out_dir / rel).resolve()
        try:
            candidate.relative_to(out_dir)
        except ValueError:
            continue  # Never delete outside the output directory.
        try:
            candidate.unlink()
            deleted.append(str(candidate))
        except OSError:
            continue
    return deleted


def state_entry(track: Track, path: Path, out_dir: Path) -> dict:
    try:
        rel = Path(path).resolve().relative_to(Path(out_dir).resolve())
    except ValueError:
        rel = Path(path)
    return {
        "key": track_key(track),
        "path": str(rel),
        "title": track.title,
        "artist": track.artist,
    }
