"""Client for the official Spotify Web API.

Uses the client credentials flow. The user supplies their own client id and
secret, created in a Spotify developer app. No internal or undocumented
endpoints are used.
"""

from __future__ import annotations

import os
import re
import time
from dataclasses import dataclass

import requests

from .errors import SpotifyApiError, SpotifyAuthError, StashifyError
from .models import Track

TOKEN_URL = "https://accounts.spotify.com/api/token"
API_BASE = "https://api.spotify.com/v1"
DEFAULT_TIMEOUT = 15
MAX_RETRIES = 3

_ID_RE = re.compile(r"^[A-Za-z0-9]{22}$")
_KINDS = ("track", "album", "playlist", "artist")

_URL_RE = re.compile(
    r"^(?:(?:https?://)?(?:www\.)?open\.spotify\.com/)?(?P<kind>track|album|playlist|artist)/(?P<id>[A-Za-z0-9]{22})(?:[/?#].*)?$"
)
_URI_RE = re.compile(
    r"^spotify:(?P<kind>track|album|playlist|artist):(?P<id>[A-Za-z0-9]{22})$"
)


def parse_spotify_url(text: str) -> tuple[str, str]:
    """Extract (kind, id) from a Spotify URL or URI.

    Accepts open.spotify.com URLs, spotify: URIs, and bare "kind:id" pairs.
    Rejects anything else so user input can never reach a path unchecked.
    """
    text = (text or "").strip()
    for pattern in (_URL_RE, _URI_RE):
        match = pattern.match(text)
        if match:
            return match.group("kind"), match.group("id")
    match = re.match(r"^(?P<kind>track|album|playlist|artist):(?P<id>[A-Za-z0-9]{22})$", text)
    if match:
        return match.group("kind"), match.group("id")
    raise StashifyError(
        f"Not a recognized Spotify link: {text!r}. "
        "Expected a track, album, playlist or artist URL."
    )


def client_credentials_from_env() -> tuple[str, str]:
    client_id = os.environ.get("SPOTIFY_CLIENT_ID", "").strip()
    client_secret = os.environ.get("SPOTIFY_CLIENT_SECRET", "").strip()
    if not client_id or not client_secret:
        raise StashifyError(
            "Spotify credentials are not set. Create an app at "
            "https://developer.spotify.com/dashboard and set SPOTIFY_CLIENT_ID "
            "and SPOTIFY_CLIENT_SECRET, or pass --client-id and --client-secret."
        )
    return client_id, client_secret


@dataclass
class SpotifyClient:
    client_id: str
    client_secret: str
    timeout: int = DEFAULT_TIMEOUT
    market: str = "US"

    def __post_init__(self) -> None:
        self._session = requests.Session()
        self._token: str | None = None
        self._token_expires_at: float = 0.0

    def _token_now(self) -> str:
        if self._token and time.time() < self._token_expires_at - 30:
            return self._token
        response = self._session.post(
            TOKEN_URL,
            data={"grant_type": "client_credentials"},
            auth=(self.client_id, self.client_secret),
            timeout=self.timeout,
        )
        if response.status_code != 200:
            raise SpotifyAuthError(
                "Could not get a Spotify access token. Check that SPOTIFY_CLIENT_ID "
                "and SPOTIFY_CLIENT_SECRET are correct and that the app is enabled."
            )
        payload = response.json()
        token = payload.get("access_token")
        if not token:
            raise SpotifyAuthError("Spotify returned an empty access token.")
        self._token = token
        self._token_expires_at = time.time() + float(payload.get("expires_in", 3600))
        return token

    def _get(self, path: str, params: dict | None = None) -> dict:
        url = f"{API_BASE}{path}"
        headers = {"Authorization": f"Bearer {self._token_now()}"}
        attempts = 0
        while True:
            attempts += 1
            try:
                response = self._session.get(
                    url, params=params, headers=headers, timeout=self.timeout
                )
            except requests.RequestException as exc:
                raise SpotifyApiError(f"Could not reach Spotify: {exc}") from exc

            if response.status_code == 401 and attempts <= MAX_RETRIES:
                self._token = None
                headers["Authorization"] = f"Bearer {self._token_now()}"
                continue
            if response.status_code == 429 and attempts <= MAX_RETRIES:
                retry_after = response.headers.get("Retry-After")
                try:
                    delay = min(float(retry_after), 10.0) if retry_after else 1.0
                except ValueError:
                    delay = 1.0
                time.sleep(delay)
                continue
            if response.status_code >= 500 and attempts <= MAX_RETRIES:
                time.sleep(0.5 * attempts)
                continue
            if response.status_code != 200:
                message = _error_message(response)
                raise SpotifyApiError(
                    f"Spotify request failed ({response.status_code}): {message}"
                )
            try:
                return response.json()
            except ValueError as exc:
                raise SpotifyApiError("Spotify returned an unreadable response.") from exc

    def _get_paged(self, path: str, params: dict | None = None) -> list[dict]:
        params = dict(params or {})
        params.setdefault("limit", 100)
        params.setdefault("offset", 0)
        items: list[dict] = []
        url = path
        page = 0
        while url:
            page += 1
            if page > 100:
                raise SpotifyApiError("Spotify pagination exceeded the safety limit.")
            data = self._get(url, params)
            items.extend(data.get("items", []))
            next_url = data.get("next")
            if next_url:
                # next is absolute; _get only accepts paths, so strip the base.
                url = next_url.replace(API_BASE, "", 1)
                params = {}
            else:
                url = ""
        return items

    # Public API -----------------------------------------------------------

    def fetch_tracks(self, url: str) -> list[Track]:
        kind, spotify_id = parse_spotify_url(url)
        if kind == "track":
            return [self.track_from_api(self._get(f"/tracks/{spotify_id}"))]
        if kind == "album":
            return self._album_tracks(spotify_id)
        if kind == "playlist":
            return self._playlist_tracks(spotify_id)
        if kind == "artist":
            return self._artist_tracks(spotify_id)
        raise StashifyError(f"Unsupported Spotify link kind: {kind!r}")

    def track_from_api(self, data: dict) -> Track:
        album = data.get("album") or {}
        external_ids = data.get("external_ids") or {}
        artists = [a.get("name", "") for a in data.get("artists") or [] if a.get("name")]
        album_artists = [
            a.get("name", "") for a in album.get("artists") or [] if a.get("name")
        ]
        images = album.get("images") or []
        cover = _largest_image(images)
        return Track(
            title=data.get("name", ""),
            artists=artists,
            album=album.get("name", ""),
            album_artist=album_artists[0] if album_artists else "",
            track_number=int(data.get("track_number") or 0),
            disc_number=int(data.get("disc_number") or 1),
            total_tracks=int(album.get("total_tracks") or 0),
            duration_ms=int(data.get("duration_ms") or 0),
            release_date=str(album.get("release_date") or ""),
            isrc=str(external_ids.get("isrc") or ""),
            cover_url=cover,
            spotify_url=(data.get("external_urls") or {}).get("spotify", ""),
            explicit=bool(data.get("explicit") or False),
        )

    def _album_tracks(self, album_id: str) -> list[Track]:
        album = self._get(f"/albums/{album_id}")
        tracks_data = self._get_paged(f"/albums/{album_id}/tracks")
        images = (album or {}).get("images") or []
        cover = _largest_image(images)
        album_artists = [
            a.get("name", "") for a in album.get("artists") or [] if a.get("name")
        ]
        album_artist = album_artists[0] if album_artists else ""
        total_tracks = int(album.get("total_tracks") or len(tracks_data))
        release_date = str(album.get("release_date") or "")
        tracks: list[Track] = []
        for item in tracks_data:
            track = self.track_from_api(
                {
                    **item,
                    "album": {
                        "name": album.get("name", ""),
                        "artists": album.get("artists") or [],
                        "images": images,
                        "total_tracks": total_tracks,
                        "release_date": release_date,
                    },
                }
            )
            track.cover_url = cover
            track.album_artist = album_artist
            tracks.append(track)
        return tracks

    def _playlist_tracks(self, playlist_id: str) -> list[Track]:
        items = self._get_paged(
            f"/playlists/{playlist_id}/tracks",
            {"market": self.market, "fields": "items(track(name,artists,album(name,artists,images,total_tracks,release_date),track_number,disc_number,duration_ms,isrc,external_ids,external_urls,explicit,is_local)),next"},
        )
        tracks: list[Track] = []
        for item in items:
            data = (item or {}).get("track") or {}
            if not data or data.get("is_local"):
                continue
            tracks.append(self.track_from_api(data))
        return tracks

    def _artist_tracks(self, artist_id: str) -> list[Track]:
        data = self._get(
            f"/artists/{artist_id}/top-tracks", {"market": self.market}
        )
        return [self.track_from_api(t) for t in data.get("tracks") or []]


def _largest_image(images: list[dict]) -> str:
    if not images:
        return ""

    def area(image: dict) -> int:
        return int(image.get("width") or 0) * int(image.get("height") or 0)

    return str(max(images, key=area).get("url") or "")


def _error_message(response: requests.Response) -> str:
    try:
        payload = response.json()
    except ValueError:
        return "no details"
    error = payload.get("error") if isinstance(payload, dict) else None
    if isinstance(error, dict):
        message = error.get("message") or error.get("error_description")
        if message:
            return str(message)
    if isinstance(error, str):
        return error
    return "no details"
