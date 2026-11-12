from stashify.models import Track


def test_track_display_and_query():
    track = Track(title="Song", artists=["A", "B"])
    assert track.display() == "A, B - Song"
    assert track.search_query() == "A, B - Song"
    assert track.artist == "A"
    assert track.artists_text == "A, B"


def test_track_unknown_artist_defaults():
    track = Track(title="Song")
    assert track.artist == "Unknown Artist"
    assert track.artists_text == "Unknown Artist"


def test_duration_text():
    assert Track(title="x", duration_ms=185_000).duration_text == "3:05"
    assert Track(title="x", duration_ms=0).duration_text == "0:00"


def test_to_from_dict_round_trip():
    track = Track(
        title="Song",
        artists=["A"],
        album="Album",
        album_artist="A",
        track_number=3,
        disc_number=2,
        total_tracks=12,
        duration_ms=200_000,
        release_date="2020-05-01",
        isrc="USABC1234567",
        cover_url="https://example.com/cover.jpg",
        spotify_url="https://open.spotify.com/track/abc",
        explicit=True,
    )
    restored = Track.from_dict(track.to_dict())
    assert restored == track


def test_from_dict_ignores_unknown_keys():
    track = Track.from_dict({"title": "Song", "unknown": "value"})
    assert track.title == "Song"


def test_from_dict_requires_title():
    import pytest

    with pytest.raises(ValueError):
        Track.from_dict({"album": "x"})
