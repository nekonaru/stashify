
from stashify.models import Track
from stashify.output import release_year, render_template, safe_segment, write_m3u
from stashify.sources import score_candidate


def make_track(**kwargs):
    defaults = dict(title="Song", artists=["Artist"], album="Album", duration_ms=200_000)
    defaults.update(kwargs)
    return Track(**defaults)


def test_safe_segment_strips_illegal_characters():
    assert safe_segment('a<b>c:d"e/f\\g|h?i*j') == "abcdefghij"
    assert safe_segment("  spaced   out  ") == "spaced out"
    assert safe_segment("trailing...") == "trailing"
    assert safe_segment("") == ""


def test_render_template_basic():
    track = make_track()
    assert render_template("{artist} - {title}", track) == "Artist - Song"
    assert (
        render_template("{album}/{track_number} {title}", make_track(track_number=3))
        == "Album/3 Song"
    )


def test_render_template_empty_falls_back():
    track = make_track()
    assert render_template("{bogus}", track) == "Artist - Song"


def test_render_template_uses_unknown_tokens_as_empty():
    track = make_track()
    assert render_template("{bogus} {title}", track) == "Song"


def test_write_m3u_relative_paths(tmp_path):
    out_dir = tmp_path / "music"
    out_dir.mkdir()
    def make(name, duration, artist="Artist"):
        path = out_dir / "sub" / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(b"x")
        return Track(
            title=name[:-4],
            artists=[artist],
            duration_ms=duration,
            spotify_url=f"https://open.spotify.com/track/{name[:8].ljust(22, 'a')}",
        ), path

    t1, p1 = make("first.mp3", 185000, "A")
    t2, p2 = make("second.mp3", 240000, "B")
    m3u = write_m3u([(t1, p1), (t2, p2)], out_dir)

    content = m3u.read_text(encoding="utf-8")
    assert "#EXTM3U" in content
    assert "#EXTINF:185" in content
    assert "#EXTINF:240" in content
    assert "A - first" in content
    assert "B - second" in content
    assert "sub/first.mp3" in content
    assert "sub/second.mp3" in content
    assert m3u.name == "stashify.m3u"


def test_release_year():
    assert release_year(make_track(release_date="2021-03-02")) == "2021"
    assert release_year(make_track(release_date="")) == ""
    assert release_year(make_track(release_date="abcd")) == ""


def test_score_candidate_rewards_close_duration():
    track = make_track(duration_ms=200_000, title="Hello Song")
    close = score_candidate(track, "Artist - Hello Song (Official Audio)", 201)
    far = score_candidate(track, "Artist - Hello Song (Official Audio)", 500)
    assert close > far


def test_score_candidate_penalizes_unwanted_versions():
    track = make_track(duration_ms=200_000, title="Hello Song")
    live = score_candidate(track, "Artist - Hello Song (Live at Venue)", 201)
    studio = score_candidate(track, "Artist - Hello Song", 201)
    assert studio > live


def test_score_candidate_keeps_requested_genre_of_version():
    track = make_track(duration_ms=200_000, title="Hello Song (Acoustic)")
    acoustic = score_candidate(track, "Artist - Hello Song (Acoustic)", 201)
    assert acoustic > 0
