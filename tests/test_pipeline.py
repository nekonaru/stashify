from stashify.models import Track
from stashify.pipeline import TrackOptions, process_tracks, summarize
from stashify.sources import Source


def fake_source(track):
    return Source(
        url=f"https://www.youtube.com/watch?v={abs(hash(track.title)) % (10**8)}",
        title=f"{track.title} (Official Audio)",
        duration_seconds=200,
    )


def _patch_network(monkeypatch, tmp_path):
    def fake_download(source, output_base, audio_format, bitrate):
        path = output_base.with_suffix("." + audio_format)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(b"audio")
        return path

    monkeypatch.setattr("stashify.pipeline.find_source", fake_source)
    monkeypatch.setattr("stashify.pipeline.download_audio", fake_download)
    monkeypatch.setattr("stashify.pipeline.fetch_lyrics", lambda track: None)
    monkeypatch.setattr("stashify.pipeline.tag_file", lambda *a, **k: None)


def test_sequential_pipeline(tmp_path, monkeypatch):
    _patch_network(monkeypatch, tmp_path)
    tracks = [Track(title=f"Song {i}", artists=["Artist"]) for i in range(4)]
    options = TrackOptions(
        out_dir=tmp_path,
        template="{title}",
        audio_format="mp3",
        bitrate="192k",
        jobs=1,
        embed_cover=False,
        embed_lyrics=False,
    )
    results = process_tracks(tracks, options, progress=lambda m: None)
    assert [r.status for r in results] == ["downloaded"] * 4
    assert [r.track.title for r in results] == [f"Song {i}" for i in range(4)]
    assert len(list(tmp_path.glob("*.mp3"))) == 4


def test_parallel_pipeline_returns_order(tmp_path, monkeypatch):
    _patch_network(monkeypatch, tmp_path)
    tracks = [Track(title=f"Song {i}", artists=["Artist"]) for i in range(6)]
    options = TrackOptions(
        out_dir=tmp_path,
        template="{title}",
        audio_format="mp3",
        bitrate="192k",
        jobs=3,
        embed_cover=False,
        embed_lyrics=False,
    )
    results = process_tracks(tracks, options, progress=lambda m: None)
    assert [r.track.title for r in results] == [f"Song {i}" for i in range(6)]
    assert all(r.status == "downloaded" for r in results)
    assert len(list(tmp_path.glob("*.mp3"))) == 6


def test_parallel_pipeline_no_clobber(tmp_path, monkeypatch):
    _patch_network(monkeypatch, tmp_path)
    tracks = [Track(title="Same", artists=["Artist"]) for _ in range(3)]
    options = TrackOptions(
        out_dir=tmp_path,
        template="{title}",
        audio_format="mp3",
        bitrate="192k",
        jobs=3,
        embed_cover=False,
        embed_lyrics=False,
    )
    results = process_tracks(tracks, options, progress=lambda m: None)
    counts = summarize(results)
    assert counts["downloaded"] == 1
    assert counts["skipped"] == 2
    assert len(list(tmp_path.glob("*.mp3"))) == 1
