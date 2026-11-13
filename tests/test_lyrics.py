import requests  # noqa: F401  (requests.exceptions used via monkeypatch)

from stashify import lyrics
from stashify.models import Track


def _track():
    return Track(
        title="Never Gonna Give You Up",
        artists=["Rick Astley"],
        album="Whenever You Need Somebody",
        duration_ms=213573,
    )


def test_lrclib_success(monkeypatch):
    def fake_get(url, params=None, timeout=None, headers=None):
        class Resp:
            status_code = 200
            content = b'{"plainLyrics": "Never gonna give you up"}'
            def json(self):
                return {"plainLyrics": "We're no strangers to love"}

        assert "lrclib.net" in url
        assert params["artist_name"] == "Rick Astley"
        return Resp()

    monkeypatch.setattr(lyrics.requests, "get", fake_get)
    assert lyrics.fetch_lyrics(_track()) == "We're no strangers to love"


def test_lrclib_404_falls_back_to_ovh(monkeypatch):
    calls = {}

    def fake_get(url, params=None, timeout=None, headers=None):
        class Resp:
            def __init__(self, status, body):
                self.status_code = status
                self.content = body
            def json(self):
                return {"lyrics": "fallback lyrics"}

        calls["count"] = calls.get("count", 0) + 1
        if "lrclib.net" in url:
            return Resp(404, b"Not Found")
        calls["ovh"] = True
        return Resp(200, b'{"lyrics": "fallback lyrics"}')

    monkeypatch.setattr(lyrics.requests, "get", fake_get)
    assert lyrics.fetch_lyrics(_track()) == "fallback lyrics"
    assert calls["ovh"] is True


def test_lrclib_error_returns_fallback_none(monkeypatch):
    def fake_get(url, params=None, timeout=None, headers=None):
        class Resp:
            status_code = 500
            content = b"server error"
            def json(self):
                raise ValueError("bad json")

        return Resp()

    monkeypatch.setattr(lyrics.requests, "get", fake_get)
    assert lyrics.fetch_lyrics(_track()) is None


def test_lrclib_instrumental_does_not_fall_back(monkeypatch):
    calls = {}

    def fake_get(url, params=None, timeout=None, headers=None):
        class Resp:
            status_code = 200
            content = b'{"instrumental": true}'

            def json(self):
                return {"instrumental": True}

        calls["count"] = calls.get("count", 0) + 1
        return Resp()

    monkeypatch.setattr(lyrics.requests, "get", fake_get)
    assert lyrics.fetch_lyrics(_track()) is None
    assert calls["count"] == 1
