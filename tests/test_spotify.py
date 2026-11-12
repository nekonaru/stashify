import pytest

from stashify.errors import StashifyError
from stashify.spotify import (
    SpotifyClient,
    _largest_image,
    parse_spotify_url,
)

TRACK_ID = "4uLU6hMCjMI75M1A2tKUQC"


@pytest.mark.parametrize(
    "text,kind,track_id",
    [
        (f"https://open.spotify.com/track/{TRACK_ID}", "track", TRACK_ID),
        (f"https://open.spotify.com/track/{TRACK_ID}?si=abc123", "track", TRACK_ID),
        ("open.spotify.com/album/6akBpx67T2PzY6OKfiHvMd", "album", "6akBpx67T2PzY6OKfiHvMd"),
        ("spotify:playlist:37i9dQZF1DXcBWIGoYBM5M", "playlist", "37i9dQZF1DXcBWIGoYBM5M"),
        ("spotify:artist:0LyfQWJT6XpnA4y2r7E5Aa", "artist", "0LyfQWJT6XpnA4y2r7E5Aa"),
        (f"track:{TRACK_ID}", "track", TRACK_ID),
    ],
)
def test_parse_spotify_url(text, kind, track_id):
    assert parse_spotify_url(text) == (kind, track_id)


@pytest.mark.parametrize(
    "text",
    [
        "",
        "https://example.com/track/4uLU6hMCjMI75M1A2tKUQC",
        "https://open.spotify.com/track/short",
        "spotify:user:someone",
        "https://open.spotify.com/genre/whatever",
        "4uLU6hMCjMI75M1A2tKUQC",
        "../../etc/passwd",
    ],
)
def test_parse_spotify_url_rejects_bad_input(text):
    with pytest.raises(StashifyError):
        parse_spotify_url(text)


def _client():
    return SpotifyClient(client_id="id", client_secret="secret")


def test_track_from_api_basic():
    client = _client()
    payload = {
        "name": "Song",
        "artists": [{"name": "Artist"}, {"name": "Guest"}],
        "album": {
            "name": "Album",
            "artists": [{"name": "Album Artist"}],
            "images": [
                {"url": "small.jpg", "width": 64, "height": 64},
                {"url": "big.jpg", "width": 640, "height": 640},
            ],
            "total_tracks": 10,
            "release_date": "2021-03-02",
        },
        "track_number": 4,
        "disc_number": 1,
        "duration_ms": 215_000,
        "external_ids": {"isrc": "USABC1234567"},
        "external_urls": {"spotify": "https://open.spotify.com/track/x"},
        "explicit": True,
    }
    track = client.track_from_api(payload)
    assert track.title == "Song"
    assert track.artists == ["Artist", "Guest"]
    assert track.album == "Album"
    assert track.album_artist == "Album Artist"
    assert track.cover_url == "big.jpg"
    assert track.isrc == "USABC1234567"
    assert track.total_tracks == 10
    assert track.explicit is True


def test_largest_image():
    assert _largest_image([]) == ""
    assert _largest_image([{"url": "a", "width": 1, "height": 1}]) == "a"


def test_get_paged_follows_next(monkeypatch):
    client = _client()
    pages = [
        {"items": [{"n": 1}], "next": "https://api.spotify.com/v1/thing?offset=1"},
        {"items": [{"n": 2}], "next": None},
    ]
    calls = []

    def fake_get(path, params=None):
        calls.append((path, params))
        return pages[len(calls) - 1]

    monkeypatch.setattr(client, "_get", fake_get)
    items = client._get_paged("/thing")
    assert items == [{"n": 1}, {"n": 2}]
    assert calls[1][0] == "/thing?offset=1"
