import pytest

from stashify.download import validate_bitrate
from stashify.errors import DownloadError


@pytest.mark.parametrize(
    "bitrate",
    ["128k", "192k", "320k", "192", "128K", " 96k "],
)
def test_validate_bitrate_accepts(bitrate):
    assert validate_bitrate(bitrate) in {"128k", "192k", "320k", "192", "96k"}


@pytest.mark.parametrize(
    "bitrate",
    ["", "banana", "k", "1k9", "128kk", "--audio-bitrate", "0x20"],
)
def test_validate_bitrate_rejects(bitrate):
    with pytest.raises(DownloadError):
        validate_bitrate(bitrate)
