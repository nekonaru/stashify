"""Error types used across Stashify."""


class StashifyError(Exception):
    """A user-facing failure with a clear message."""


class SpotifyAuthError(StashifyError):
    """Authentication or authorization with Spotify failed."""


class SpotifyApiError(StashifyError):
    """A call to the Spotify Web API failed."""


class SourceNotFoundError(StashifyError):
    """No suitable audio source could be found for a track."""


class DownloadError(StashifyError):
    """Downloading or converting a track failed."""
