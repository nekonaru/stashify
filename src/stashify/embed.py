"""Metadata from Spotify's public embed pages.

The embed pages served at open.spotify.com/embed/... are public HTML pages
meant to be loaded by any visitor's browser. Each page embeds a JSON document
with the entity metadata (title, artists, duration, cover art, the track list
of an album, playlist or artist). Stashify parses that document instead of the
official Web API, so no account, login or developer app is required.

Limitations, honestly:
- Private or unavailable entities cannot be resolved (embed shows a not-found page).
- Fields like ISRC, album name (for playlist items), track numbers and disc
  numbers are not available. Album track numbers are derived from the order.
- The embed format is not a documented public contract and can change.
"""

from __future__ import annotations

import json
import re
import threading
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass

import requests

from .errors import StashifyError
from .models import Track
from .spotify import parse_spotify_url

EMBED_BASE = "https://open.spotify.com/embed"
EMBED_TIMEOUT = 20
MAX_EMBED_BYTES = 8 * 1024 * 1024
USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/131.0.0.0 Safari/537.36"
)

_NEXT_DATA_RE = re.compile(
    r'<script id="__NEXT_DATA__" type="application/json">(.*?)</script>',
    re.S,
)


@dataclass
class EmbedResolver:
    """Resolve public Spotify links into Track objects via embed pages."""

    detailed: bool = True
    timeout: int = EMBED_TIMEOUT

    def __post_init__(self) -> None:
        self._local = threading.local()

    def _session(self) -> requests.Session:
        session = getattr(self._local, "session", None)
        if session is None:
            session = requests.Session()
            self._local.session = session
        return session

    # Public interface ------------------------------------------------------

    def fetch_tracks(self, url: str) -> list[Track]:
        kind, spotify_id = parse_spotify_url(url)
        entity = self._entity(kind, spotify_id)
        if kind == "track":
            return [self._track_from_entity(entity)]
        if kind == "album":
            entity_title = _clean_str(entity.get("name"))
            album_artist = _clean_str(entity.get("subtitle"))
            cover = _largest_image(entity)
            entries = _track_list(entity)
            tracks = []
            for index, entry in enumerate(entries, start=1):
                track = self._track_from_entry(entry)
                track.album = entity_title
                track.album_artist = album_artist or track.artist
                track.track_number = index
                track.disc_number = 1
                track.total_tracks = len(entries)
                track.cover_url = cover or track.cover_url
                tracks.append(track)
            if self.detailed:
                tracks = self._enrich(tracks)
            return tracks
        if kind in ("playlist", "artist"):
            cover = _largest_image(entity) if kind == "playlist" else ""
            entries = _track_list(entity)
            tracks = [self._track_from_entry(entry) for entry in entries]
            if self.detailed:
                tracks = self._enrich(tracks)
            if kind == "playlist":
                for track in tracks:
                    if not track.cover_url:
                        track.cover_url = cover
            return tracks
        raise StashifyError(f"Unsupported Spotify link kind: {kind!r}")

    # Internals ------------------------------------------------------------

    def _entity(self, kind: str, spotify_id: str) -> dict:
        try:
            response = self._session().get(
                f"{EMBED_BASE}/{kind}/{spotify_id}",
                headers={"User-Agent": USER_AGENT},
                timeout=self.timeout,
                stream=True,
            )
        except requests.RequestException as exc:
            raise StashifyError(f"Could not reach Spotify embed pages: {exc}") from exc

        content = b""
        limit = MAX_EMBED_BYTES
        for chunk in response.iter_content(chunk_size=64 * 1024):
            limit -= len(chunk)
            if limit < 0:
                raise StashifyError("Spotify embed page is unexpectedly large.")
            content += chunk
        if response.status_code != 200:
            raise StashifyError(
                f"Spotify embed request failed ({response.status_code}). "
                "The link is probably private or does not exist."
            )
        match = _NEXT_DATA_RE.search(content.decode("utf-8", errors="replace"))
        if not match:
            raise StashifyError(
                "Spotify embed page has an unexpected format. "
                "The embed format may have changed."
            )
        try:
            payload = json.loads(match.group(1))
        except json.JSONDecodeError as exc:
            raise StashifyError("Spotify embed page contains invalid JSON.") from exc
        except RecursionError as exc:
            raise StashifyError("Spotify embed page JSON is too deeply nested.") from exc
        entity = (
            ((payload.get("props") or {}).get("pageProps") or {})
            .get("state", {})
            .get("data", {})
            .get("entity")
        )
        if not isinstance(entity, dict):
            status = (payload.get("props") or {}).get("pageProps", {}).get("status")
            detail = f" (status: {status})" if status else ""
            raise StashifyError(
                f"This {kind} link could not be resolved{detail}. "
                "It may be private, unavailable or removed."
            )
        return entity

    def _track_from_entity(self, entity: dict) -> Track:
        artists = [
            _clean_str(a.get("name"))
            for a in entity.get("artists") or []
            if _clean_str(a.get("name"))
        ]
        if not artists:
            subtitle = _clean_str(entity.get("subtitle"))
            artists = _split_artists(subtitle)
        release = ""
        raw_date = entity.get("releaseDate") or {}
        if isinstance(raw_date, dict):
            release = str(raw_date.get("isoString") or "")[:10]
        cover = _largest_image(entity)
        return Track(
            title=_clean_str(entity.get("name") or entity.get("title")),
            artists=artists,
            duration_ms=int(entity.get("duration") or 0),
            release_date=release,
            cover_url=cover,
            spotify_url=_spotify_url(entity),
            explicit=bool(entity.get("isExplicit") or False),
        )

    def _track_from_entry(self, entry: dict) -> Track:
        uri = _clean_str(entry.get("uri"))
        artists = _split_artists(_clean_str(entry.get("subtitle")))
        explicit = bool(entry.get("isExplicit") or False)
        return Track(
            title=_clean_str(entry.get("title")),
            artists=artists,
            duration_ms=int(entry.get("duration") or 0),
            spotify_url=_spotify_url_from_uri(uri),
            explicit=explicit,
        )

    def _enrich(self, tracks: list[Track]) -> list[Track]:
        """Fill cover art, release year and proper artists via per-track embeds.

        Runs four lookups in parallel; on any failure the basic entry data is
        kept.
        """

        def fetch(index: int, track: Track) -> tuple[int, Track]:
            track_id = _id_from_spotify_url(track.spotify_url)
            if not track_id:
                return index, track
            try:
                entity = self._entity("track", track_id)
            except StashifyError:
                return index, track
            full = self._track_from_entity(entity)
            if full.artists:
                track.artists = full.artists
            if full.release_date and not track.release_date:
                track.release_date = full.release_date
            if full.cover_url:
                track.cover_url = full.cover_url
            return index, track

        if len(tracks) > 1:
            with ThreadPoolExecutor(max_workers=4) as pool:
                return [track for _, track in sorted(pool.map(fetch, range(len(tracks)), tracks))]
        return [fetch(0, tracks[0])[1]]


def _clean_str(value) -> str:
    if not isinstance(value, str):
        return ""
    return value.strip()


def _split_artists(subtitle: str) -> list[str]:
    parts = [part.strip() for part in (subtitle or "").split(",")]
    parts = [part for part in parts if part]
    return parts or ["Unknown Artist"]


def _track_list(entity: dict) -> list[dict]:
    entries = entity.get("trackList") or []
    result = []
    for entry in entries:
        if not isinstance(entry, dict):
            continue
        if entry.get("isPlayable") is False:
            continue
        if _clean_str(entry.get("uri")) and _clean_str(entry.get("title")):
            result.append(entry)
    return result


def _largest_image(entity: dict) -> str:
    images = (entity.get("visualIdentity") or {}).get("image") or []
    if not images:
        return ""

    def area(image: dict) -> int:
        return int(image.get("maxWidth") or 0) * int(image.get("maxHeight") or 0)

    return _clean_str(max(images, key=area).get("url"))


def _spotify_url(entity: dict) -> str:
    kind = entity.get("type") or "track"
    entity_id = _clean_str(entity.get("id"))
    if entity_id:
        return f"https://open.spotify.com/{kind}/{entity_id}"
    return _clean_str(entity.get("uri"))


def _spotify_url_from_uri(uri: str) -> str:
    match = re.match(r"^spotify:(?P<kind>[a-z]+):(?P<id>[A-Za-z0-9]{22})$", uri or "")
    if match:
        return f"https://open.spotify.com/{match.group('kind')}/{match.group('id')}"
    return uri or ""


def _id_from_spotify_url(url: str) -> str:
    match = re.search(r"(?:track/|spotify:track:)([A-Za-z0-9]{22})", url or "")
    return match.group(1) if match else ""
