"""SoundCloud fallback behavior tests for the source matcher."""

import pytest

from stashify import sources
from stashify.errors import SourceNotFoundError
from stashify.models import Track
from stashify.sources import find_source


def make_track(duration_ms=213000, artists=None, title="Never Gonna Give You Up"):
    return Track(
        title=title,
        artists=artists or ["Rick Astley"],
        duration_ms=duration_ms,
    )


def entry(vid, title, duration):
    return {
        "id": vid,
        "url": f"https://www.youtube.com/watch?v={vid}",
        "title": title,
        "duration": duration,
        "channel": "someone",
    }


class FakeSearch:
    """Patch _search prefix routes to scripted entry lists."""

    def __init__(self, mapping):
        self.mapping = mapping

    def __call__(self, prefix, query, options, cookies_from_browser):
        return self.mapping.get(prefix, [])


def test_soundcloud_used_when_youtube_empty(monkeypatch):
    monkeypatch.setattr(sources, "_youtube_entries", lambda q, c=None, n=None: [])
    monkeypatch.setattr(
        sources,
        "_soundcloud_entries",
        lambda q, c=None, n=None: [
            {
                "id": "sc1",
                "url": "https://soundcloud.com/user/track",
                "title": "Rick Astley - Never Gonna Give You Up",
                "duration": 213,
                "channel": "user",
            }
        ],
    )
    source = find_source(make_track())
    assert source.provider == "soundcloud"
    assert source.url == "https://soundcloud.com/user/track"


def test_soundcloud_30s_preview_rejected(monkeypatch):
    monkeypatch.setattr(sources, "_youtube_entries", lambda q, c=None, n=None: [])
    monkeypatch.setattr(
        sources,
        "_soundcloud_entries",
        lambda q, c=None, n=None: [
            {
                "id": "sc1",
                "url": "https://soundcloud.com/user/track",
                "title": "Rick Astley - Never Gonna Give You Up Preview",
                "duration": 30.0,
                "channel": "user",
            }
        ],
    )
    with pytest.raises(SourceNotFoundError, match="previews"):
        find_source(make_track())


def test_youtube_allowed_with_slow_result(monkeypatch):
    monkeypatch.setattr(
        sources,
        "_youtube_entries",
        lambda q, c=None, n=None: [
            {
                "id": "v1",
                "url": "https://www.youtube.com/watch?v=v1",
                "title": "Never Gonna Give You Up",
                "duration": 213,
                "channel": "official",
            }
        ],
    )
    # Fallback must NOT be consulted when the YouTube result is acceptable.
    monkeypatch.setattr(
        sources,
        "_soundcloud_entries",
        lambda q, c=None, n=None: (
            (_ for _ in ()).throw(AssertionError("should not search SoundCloud"))
        ),
    )
    source = find_source(make_track())
    assert source.provider == "youtube"


def test_low_score_youtube_falls_back_to_soundcloud(monkeypatch):
    # YouTube returns only a bad match (much too long); SoundCloud returns the right one.
    monkeypatch.setattr(
        sources,
        "_youtube_entries",
        lambda q, c=None, n=None: [
            {
                "id": "v1",
                "url": "https://www.youtube.com/watch?v=v1",
                "title": "Never Gonna Give You Up 10 hour loop",
                "duration": 36000,
                "channel": "loops",
            }
        ],
    )
    monkeypatch.setattr(
        sources,
        "_soundcloud_entries",
        lambda q, c=None, n=None: [
            {
                "id": "sc1",
                "url": "https://soundcloud.com/user/track",
                "title": "Rick Astley - Never Gonna Give You Up",
                "duration": 212,
                "channel": "user",
            }
        ],
    )
    source = find_source(make_track())
    assert source.provider == "soundcloud"
    assert source.duration_seconds == 212


def test_youtube_search_failure_falls_back(monkeypatch):
    def boom(q, c=None):
        from stashify.errors import SourceNotFoundError

        raise SourceNotFoundError("YouTube is blocked")

    monkeypatch.setattr(sources, "_youtube_entries", boom)
    monkeypatch.setattr(
        sources,
        "_soundcloud_entries",
        lambda q, c=None, n=None: [
            {
                "id": "sc1",
                "url": "https://soundcloud.com/user/track",
                "title": "Rick Astley - Never Gonna Give You Up",
                "duration": 212,
                "channel": "user",
            }
        ],
    )
    source = find_source(make_track())
    assert source.provider == "soundcloud"
