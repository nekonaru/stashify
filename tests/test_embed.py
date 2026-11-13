import json

import pytest

from stashify.embed import (
    _NEXT_DATA_RE,
    EmbedResolver,
    _largest_image,
    _split_artists,
    _spotify_url_from_uri,
)
from stashify.errors import StashifyError

TRACK_ENTITY = {
    "type": "track",
    "name": "Never Gonna Give You Up",
    "id": "4uLU6hMCjMI75M1A2tKUQC",
    "title": "Never Gonna Give You Up",
    "artists": [{"name": "Rick Astley", "uri": "spotify:artist:0gxyHStUsqpMadRV0Di1Qt"}],
    "releaseDate": {"isoString": "1987-11-12T00:00:00Z"},
    "duration": 213573,
    "isExplicit": False,
    "visualIdentity": {
        "image": [
            {"url": "cover-300.jpg", "maxHeight": 300, "maxWidth": 300},
            {"url": "cover-640.jpg", "maxHeight": 640, "maxWidth": 640},
        ]
    },
}

ALBUM_ENTITY = {
    "type": "album",
    "name": "Global Warming",
    "subtitle": "Pitbull",
    "visualIdentity": {
        "image": [{"url": "album-640.jpg", "maxHeight": 640, "maxWidth": 640}]
    },
    "trackList": [
        {
            "uri": f"spotify:track:{'a' * 22}",
            "title": "Song One",
            "subtitle": "Pitbull",
            "duration": 100000,
            "isExplicit": False,
            "isPlayable": True,
        },
        {
            "uri": f"spotify:track:{'b' * 22}",
            "title": "Song Two (feat. Guest)",
            "subtitle": "Pitbull, Guest",
            "duration": 200000,
            "isExplicit": True,
            "isPlayable": True,
        },
        {
            "uri": f"spotify:track:{'c' * 22}",
            "title": "Region Locked",
            "subtitle": "Pitbull",
            "duration": 300000,
            "isExplicit": False,
            "isPlayable": False,
        },
    ],
}


def fake_entity(resolver, entity, monkeypatch):
    monkeypatch.setattr(resolver, "_entity", lambda kind, sid: entity)


def test_fetch_track(monkeypatch):
    resolver = EmbedResolver(detailed=False)
    fake_entity(resolver, TRACK_ENTITY, monkeypatch)
    tracks = resolver.fetch_tracks("https://open.spotify.com/track/4uLU6hMCjMI75M1A2tKUQC")
    assert len(tracks) == 1
    track = tracks[0]
    assert track.title == "Never Gonna Give You Up"
    assert track.artists == ["Rick Astley"]
    assert track.duration_ms == 213573
    assert track.release_date == "1987-11-12"
    assert track.cover_url == "cover-640.jpg"
    assert track.spotify_url == "https://open.spotify.com/track/4uLU6hMCjMI75M1A2tKUQC"


def test_fetch_album_order_and_metadata(monkeypatch):
    resolver = EmbedResolver(detailed=False)
    fake_entity(resolver, ALBUM_ENTITY, monkeypatch)
    tracks = resolver.fetch_tracks("https://open.spotify.com/album/4aawyAB9vmqN3uQ7FjRGTy")
    assert [t.title for t in tracks] == ["Song One", "Song Two (feat. Guest)"]
    assert tracks[0].track_number == 1
    assert tracks[1].track_number == 2
    assert tracks[0].album == "Global Warming"
    assert tracks[0].album_artist == "Pitbull"
    assert tracks[0].total_tracks == 2
    assert tracks[0].cover_url == "album-640.jpg"
    assert tracks[1].artists == ["Pitbull", "Guest"]
    assert tracks[1].explicit is True


def test_fetch_playlist(monkeypatch):
    resolver = EmbedResolver(detailed=False)
    fake_entity(resolver, ALBUM_ENTITY, monkeypatch)
    tracks = resolver.fetch_tracks("https://open.spotify.com/playlist/37i9dQZF1DXcBWIGoYBM5M")
    assert [t.title for t in tracks] == ["Song One", "Song Two (feat. Guest)"]
    assert tracks[0].track_number == 0
    assert tracks[0].album == ""


def test_detailed_enrich_falls_back(monkeypatch):
    resolver = EmbedResolver(detailed=True)

    def failing(kind, sid):
        raise StashifyError("boom")

    monkeypatch.setattr(resolver, "_entity", failing)
    tracks = resolver._enrich([resolver._track_from_entry(ALBUM_ENTITY["trackList"][0])])
    assert tracks[0].title == "Song One"


def test_split_artists():
    assert _split_artists("Ashe") == ["Ashe"]
    assert _split_artists("Pitbull, Sensato") == ["Pitbull", "Sensato"]
    assert _split_artists("") == ["Unknown Artist"]


def test_spotify_url_from_uri():
    assert _spotify_url_from_uri("spotify:track:4uLU6hMCjMI75M1A2tKUQC") == (
        "https://open.spotify.com/track/4uLU6hMCjMI75M1A2tKUQC"
    )
    assert _spotify_url_from_uri("") == ""


def test_largest_image():
    assert _largest_image(TRACK_ENTITY) == "cover-640.jpg"
    assert _largest_image({}) == ""


def test_next_data_regex():
    html = '<html><script id="__NEXT_DATA__" type="application/json">{"a": 1}</script></html>'
    match = _NEXT_DATA_RE.search(html)
    assert match is not None
    assert json.loads(match.group(1)) == {"a": 1}


def test_entity_missing_data_raises(monkeypatch):
    resolver = EmbedResolver(detailed=False)

    class FakeResponse:
        status_code = 200

        def iter_content(self, chunk_size=65536):
            yield (
                b'<script id="__NEXT_DATA__" type="application/json">'
                b'{"props":{"pageProps":{"status": 404}}}</script>'
            )

    class FakeSession:
        def get(self, *args, **kwargs):
            return FakeResponse()

    monkeypatch.setattr(resolver, "_session", lambda: FakeSession())
    with pytest.raises(StashifyError, match="could not be resolved"):
        resolver.fetch_tracks("https://open.spotify.com/playlist/37i9dQZF1DXcBWIGoYBM5M")
