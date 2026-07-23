from typing import Any

import requests

from .models import Track

TOKEN_URL = "https://accounts.spotify.com/api/token"
CURRENT_URL = "https://api.spotify.com/v1/me/player/currently-playing"
RECENT_URL = "https://api.spotify.com/v1/me/player/recently-played"


class SpotifyAuthenticationError(RuntimeError):
    pass


class SpotifyAPIError(RuntimeError):
    pass


class SpotifyRateLimitError(SpotifyAPIError):
    def __init__(self, retry_after_seconds: int | None):
        self.retry_after_seconds = retry_after_seconds
        super().__init__("Spotify API rate limit exceeded")


class SpotifyClient:
    def __init__(
        self,
        client_id: str,
        client_secret: str,
        refresh_token: str,
        timeout_seconds: float = 10.0,
        *,
        session: requests.Session | None = None,
    ) -> None:
        self._client_id = client_id
        self._client_secret = client_secret
        self._refresh_token = refresh_token
        self._timeout_seconds = timeout_seconds
        self._session = session or requests.Session()

    def refresh_access_token(self) -> str:
        try:
            response = self._session.post(
                TOKEN_URL,
                auth=(self._client_id, self._client_secret),
                data={"grant_type": "refresh_token", "refresh_token": self._refresh_token},
                timeout=self._timeout_seconds,
            )
        except requests.Timeout as error:
            raise SpotifyAuthenticationError("Spotify authentication timed out") from error
        except requests.RequestException as error:
            raise SpotifyAuthenticationError("Spotify authentication request failed") from error

        if response.status_code in (400, 401):
            raise SpotifyAuthenticationError("Spotify credentials are invalid or expired")
        self._raise_api_error(response)
        payload = self._json_object(response)
        access_token = payload.get("access_token")
        if not isinstance(access_token, str) or not access_token:
            raise SpotifyAuthenticationError("Spotify token response was invalid")
        return access_token

    def get_current_track(self, access_token: str) -> Track | None:
        response = self._get(CURRENT_URL, access_token)
        if response.status_code == 204:
            return None
        self._raise_api_error(response)
        payload = self._json_object(response)
        if payload.get("currently_playing_type") not in (None, "track"):
            return None
        return self._parse_track(payload.get("item"))

    def get_recent_tracks(self, access_token: str, limit: int = 5) -> list[Track]:
        response = self._get(RECENT_URL, access_token, params={"limit": 20})
        self._raise_api_error(response)
        payload = self._json_object(response)
        items = payload.get("items")
        if not isinstance(items, list):
            return []

        tracks: list[Track] = []
        seen_urls: set[str] = set()
        for entry in items:
            raw_track = entry.get("track") if isinstance(entry, dict) else None
            track = self._parse_track(raw_track)
            if track is None or track.spotify_url in seen_urls:
                continue
            seen_urls.add(track.spotify_url)
            tracks.append(track)
            if len(tracks) >= max(0, min(limit, 5)):
                break
        return tracks

    def _get(self, url: str, access_token: str, **kwargs: Any) -> requests.Response:
        try:
            return self._session.get(
                url,
                headers={"Authorization": f"Bearer {access_token}"},
                timeout=self._timeout_seconds,
                **kwargs,
            )
        except requests.Timeout as error:
            raise SpotifyAPIError("Spotify API request timed out") from error
        except requests.RequestException as error:
            raise SpotifyAPIError("Spotify API request failed") from error

    @staticmethod
    def _json_object(response: requests.Response) -> dict[str, Any]:
        try:
            payload = response.json()
        except (ValueError, requests.JSONDecodeError) as error:
            raise SpotifyAPIError("Spotify returned an invalid response") from error
        if not isinstance(payload, dict):
            raise SpotifyAPIError("Spotify returned an invalid response")
        return payload

    @staticmethod
    def _raise_api_error(response: requests.Response) -> None:
        if 200 <= response.status_code < 300:
            return
        if response.status_code == 401:
            raise SpotifyAuthenticationError("Spotify access token was rejected")
        if response.status_code == 429:
            retry_after: int | None = None
            try:
                retry_after = int(response.headers.get("Retry-After", ""))
            except (TypeError, ValueError):
                pass
            raise SpotifyRateLimitError(retry_after)
        raise SpotifyAPIError(f"Spotify API request failed with status {response.status_code}")

    @staticmethod
    def _parse_track(raw: object) -> Track | None:
        if not isinstance(raw, dict) or raw.get("type", "track") != "track":
            return None
        name = raw.get("name")
        url = raw.get("external_urls")
        spotify_url = url.get("spotify") if isinstance(url, dict) else None
        raw_artists = raw.get("artists")
        if not isinstance(name, str) or not name or not isinstance(spotify_url, str) or not spotify_url:
            return None
        if not isinstance(raw_artists, list):
            return None
        artists = tuple(
            artist["name"]
            for artist in raw_artists
            if isinstance(artist, dict) and isinstance(artist.get("name"), str) and artist["name"]
        )
        if not artists:
            return None
        return Track(
            name=name,
            artists=artists,
            spotify_url=spotify_url,
            album_image_url=SpotifyClient._parse_album_image_url(raw),
        )

    @staticmethod
    def _parse_album_image_url(raw_track: dict[str, Any]) -> str | None:
        album = raw_track.get("album")
        images = album.get("images") if isinstance(album, dict) else None
        if not isinstance(images, list):
            return None

        valid_images: list[tuple[str, int | None]] = []
        for image in images:
            if not isinstance(image, dict):
                continue
            url = image.get("url")
            width = image.get("width")
            if not isinstance(url, str) or not url:
                continue
            valid_width = width if isinstance(width, int) and not isinstance(width, bool) else None
            valid_images.append((url, valid_width))

        sized = [(url, width) for url, width in valid_images if width is not None and width >= 64]
        if sized:
            return min(sized, key=lambda image: image[1])[0]
        return valid_images[-1][0] if valid_images else None
