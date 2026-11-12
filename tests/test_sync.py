import base64
import json

import pytest

from stashify.sync import (
    load_state,
    plan_sync,
    remove_entries,
    save_state,
    state_entry,
    track_key,
)
from stashify.models import Track


def make_track(title="Song", artist="Artist", url="https://open.spotify.com/track/4uLU6hMCjMI75M1A2tKUQC"):
    return Track(title=title, artists=[artist], spotify_url=url)


def test_track_key_prefers_spotify_url():
    assert track_key(make_track()) == "https://open.spotify.com/track/4uLU6hMCjMI75M1A2tKUQC"
    fallback = Track(title="Song", artists=["Artist"], album="Album", track_number=1)
    assert track_key(fallback) == "Artist-Album-Song-1"


def test_state_round_trip(tmp_path):
    state_path = tmp_path / "stashify.sync.json"
    state = load_state(state_path)
    assert state["entries"] == []
    state["entries"].append({"key": "k", "path": "a.mp3"})
    save_state(state_path, state)
    loaded = load_state(state_path)
    assert loaded["entries"] == [{"key": "k", "path": "a.mp3"}]


def test_load_state_rejects_garbage(tmp_path):
    state_path = tmp_path / "stashify.sync.json"
    state_path.write_text("not json", encoding="utf-8")
    with pytest.raises(Exception):
        load_state(state_path)


def test_plan_sync_finds_missing_and_removed():
    current = [make_track("Keep", url="url-keep"), make_track("New", url="url-new")]
    state = {
        "entries": [
            {"key": "url-keep", "path": "keep.mp3"},
            {"key": "url-old", "path": "old.mp3"},
        ]
    }
    missing, removed = plan_sync(state, current)
    assert [t.title for t in missing] == ["New"]
    assert [e["key"] for e in removed] == ["url-old"]


def test_remove_entries_stays_inside_out_dir(tmp_path):
    out_dir = tmp_path / "music"
    out_dir.mkdir()
    inside = out_dir / "inside.mp3"
    inside.write_bytes(b"x")
    outside = tmp_path / "outside.txt"
    outside.write_bytes(b"keep me")

    removed = [
        {"key": "a", "path": "inside.mp3"},
        {"key": "b", "path": "../outside.txt"},
    ]
    deleted = remove_entries(removed, out_dir)
    assert str(inside) in deleted
    assert not inside.exists()
    assert outside.exists()


def test_state_entry_relative_path(tmp_path):
    out_dir = tmp_path / "music"
    out_dir.mkdir()
    target = out_dir / "sub" / "song.mp3"
    target.parent.mkdir(parents=True)
    target.write_bytes(b"x")
    entry = state_entry(make_track(), target, out_dir)
    assert entry["path"].replace("\\", "/") == "sub/song.mp3"
