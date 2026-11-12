"""Data model for a single track of music.

A Track is the unit everything else in Stashify works on: metadata is
collected from Spotify, audio is matched and downloaded for each track,
and the file is tagged with the same information.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field


@dataclass
class Track:
    title: str
    artists: list[str] = field(default_factory=list)
    album: str = ""
    album_artist: str = ""
    track_number: int = 0
    disc_number: int = 1
    total_tracks: int = 0
    duration_ms: int = 0
    release_date: str = ""
    isrc: str = ""
    cover_url: str = ""
    genres: list[str] = field(default_factory=list)
    spotify_url: str = ""
    explicit: bool = False

    @property
    def artist(self) -> str:
        """Primary artist, used for display and file naming."""
        return self.artists[0] if self.artists else "Unknown Artist"

    @property
    def artists_text(self) -> str:
        return ", ".join(self.artists) if self.artists else "Unknown Artist"

    @property
    def duration_text(self) -> str:
        minutes, seconds = divmod(int(self.duration_ms) // 1000, 60)
        return f"{minutes}:{seconds:02d}"

    def display(self) -> str:
        return f"{self.artists_text} - {self.title}"

    def search_query(self) -> str:
        """Query string used to look the track up on YouTube."""
        return f"{self.artists_text} - {self.title}"

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> Track:
        if not isinstance(data, dict):
            raise ValueError("Track data must be a mapping")
        known = {f for f in cls.__dataclass_fields__}  # type: ignore[attr-defined]
        values = {k: v for k, v in data.items() if k in known}
        if not values.get("title"):
            raise ValueError("Track data is missing a title")
        return cls(**values)
