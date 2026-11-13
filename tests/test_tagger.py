import base64
import shutil
import subprocess
from pathlib import Path

import pytest

from stashify import tagger
from stashify.models import Track
from stashify.tagger import tag_file

FFMPEG = shutil.which("ffmpeg")
needs_ffmpeg = pytest.mark.skipif(FFMPEG is None, reason="ffmpeg not installed")

# 1x1 transparent PNG.
PNG_1PX = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+/p9cAAAAASUVORK5CYII="
)


def make_track():
    return Track(
        title="Song",
        artists=["Artist", "Guest"],
        album="Album",
        album_artist="Album Artist",
        track_number=4,
        disc_number=2,
        total_tracks=11,
        duration_ms=300_000,
        release_date="2021-03-02",
        isrc="USABC1234567",
    )


def render_audio(tmp_path: Path, name: str, codec_args: list[str]) -> Path:
    target = tmp_path / name
    sine = "sine=frequency=440:duration=0.3"
    subprocess.run(
        [FFMPEG, "-y", "-f", "lavfi", "-i", sine, *codec_args, str(target)],
        check=True,
        capture_output=True,
    )
    return target


@needs_ffmpeg
def test_tag_mp3_round_trip(tmp_path):
    audio = render_audio(tmp_path, "track.mp3", ["-q:a", "9"])
    tag_file(audio, make_track(), (PNG_1PX, "image/png"), "Some lyrics")

    from mutagen.id3 import ID3

    tags = ID3(audio)
    assert tags["TIT2"].text[0] == "Song"
    assert tags["TPE1"].text[0] == "Artist, Guest"
    assert tags["TPE2"].text[0] == "Album Artist"
    assert tags["TALB"].text[0] == "Album"
    assert tags["TRCK"].text[0] == "4/11"
    assert tags["TPOS"].text[0] == "2"
    assert str(tags["TDRC"].text[0]).startswith("2021")
    assert tags["TSRC"].text[0] == "USABC1234567"
    assert tags["USLT::eng"].text == "Some lyrics"
    assert any(frame.type == 3 for frame in tags.getall("APIC"))


@needs_ffmpeg
def test_tag_flac_round_trip(tmp_path):
    audio = render_audio(tmp_path, "track.flac", ["-c:a", "flac"])
    tag_file(audio, make_track(), (PNG_1PX, "image/png"), "Some lyrics")

    from mutagen.flac import FLAC

    tags = FLAC(audio)
    assert tags["TITLE"] == ["Song"]
    assert tags["ARTIST"] == ["Artist", "Guest"]
    assert tags["ALBUM"] == ["Album"]
    assert tags["ALBUMARTIST"] == ["Album Artist"]
    assert tags["TRACKNUMBER"] == ["4"]
    assert tags["TRACKTOTAL"] == ["11"]
    assert tags["DISCNUMBER"] == ["2"]
    assert tags["DATE"] == ["2021"]
    assert tags["ISRC"] == ["USABC1234567"]
    assert tags["LYRICS"] == ["Some lyrics"]
    assert len(tags.pictures) == 1
    assert tags.pictures[0].mime == "image/png"


@needs_ffmpeg
def test_tag_m4a_round_trip(tmp_path):
    audio = render_audio(tmp_path, "track.m4a", ["-c:a", "aac", "-movflags", "+faststart"])
    tag_file(audio, make_track(), (PNG_1PX, "image/png"), "Some lyrics")

    from mutagen.mp4 import MP4

    tags = MP4(audio)
    assert tags["\xa9nam"] == ["Song"]
    assert tags["\xa9ART"] == ["Artist", "Guest"]
    assert tags["\xa9alb"] == ["Album"]
    assert tags["aART"] == ["Album Artist"]
    assert tags["trkn"] == [(4, 11)]
    assert tags["disk"] == [(2, 0)]
    assert tags["\xa9day"] == ["2021"]
    assert tags["\xa9lyr"] == ["Some lyrics"]
    assert tags["covr"][0].imageformat == 14  # PNG


@needs_ffmpeg
def test_tag_wav_round_trip(tmp_path):
    audio = render_audio(tmp_path, "track.wav", ["-c:a", "pcm_s16le"])
    tag_file(audio, make_track(), None, None)

    from mutagen.wave import WAVE

    tags = WAVE(audio).tags
    assert tags is not None
    assert tags["TIT2"].text[0] == "Song"
    assert tags["TPE1"].text[0] == "Artist, Guest"
    assert tags["TRCK"].text[0] == "4/11"


@needs_ffmpeg
def test_tag_opus_round_trip(tmp_path):
    try:
        audio = render_audio(tmp_path, "track.opus", ["-c:a", "libopus"])
    except subprocess.CalledProcessError:
        pytest.skip("libopus encoder not available")
    tag_file(audio, make_track(), (PNG_1PX, "image/png"), "Some lyrics")

    from mutagen.oggopus import OggOpus

    tags = OggOpus(audio)
    assert tags["TITLE"] == ["Song"]
    assert tags["ARTIST"] == ["Artist", "Guest"]
    assert tags["LYRICS"] == ["Some lyrics"]
    assert "METADATA_BLOCK_PICTURE" in tags


def test_tag_unsupported_container_reports_error(tmp_path):
    from stashify.errors import StashifyError

    target = tmp_path / "track.bin"
    target.write_bytes(b"not audio")
    with pytest.raises(StashifyError):
        tag_file(target, make_track(), None, None)


def test_fetch_cover_rejects_non_image(monkeypatch):
    class FakeResponse:
        status_code = 200
        headers = {"Content-Type": "text/html"}
        content = b"<html></html>"

        def iter_content(self, chunk_size=65536):
            return iter([self.content])

    monkeypatch.setattr(tagger.requests, "get", lambda *a, **k: FakeResponse())
    track = Track(title="Song", cover_url="https://example.com/cover")
    assert tagger.fetch_cover(track) is None


def test_fetch_cover_handles_request_failure(monkeypatch):
    def boom(*args, **kwargs):
        raise tagger.requests.RequestException("nope")

    monkeypatch.setattr(tagger.requests, "get", boom)
    track = Track(title="Song", cover_url="https://example.com/cover")
    assert tagger.fetch_cover(track) is None
