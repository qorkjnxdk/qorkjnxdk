from unittest.mock import Mock

import pytest
import requests

from scripts.spotify_readme.client import (
    SpotifyAPIError,
    SpotifyAuthenticationError,
    SpotifyClient,
    SpotifyRateLimitError,
)


def response(status: int, payload: object = None, headers: dict[str, str] | None = None) -> Mock:
    result = Mock(status_code=status, headers=headers or {})
    result.json.return_value = payload
    return result


@pytest.fixture
def session() -> Mock:
    return Mock()


@pytest.fixture
def client(session: Mock) -> SpotifyClient:
    return SpotifyClient("client", "secret", "refresh", session=session)


def test_refreshes_access_token(client: SpotifyClient, session: Mock) -> None:
    session.post.return_value = response(200, {"access_token": "access"})

    assert client.refresh_access_token() == "access"
    assert session.post.call_args.kwargs["timeout"] == 10.0
    assert session.post.call_args.kwargs["data"]["grant_type"] == "refresh_token"


def test_invalid_refresh_token_raises_safe_authentication_error(client: SpotifyClient, session: Mock) -> None:
    session.post.return_value = response(400, {"error_description": "contains-secret"})

    with pytest.raises(SpotifyAuthenticationError, match="credentials") as caught:
        client.refresh_access_token()

    assert "contains-secret" not in str(caught.value)


def test_parses_current_track(client: SpotifyClient, session: Mock) -> None:
    session.get.return_value = response(200, {
        "currently_playing_type": "track",
        "item": {"name": "Song", "artists": [{"name": "One"}, {"name": "Two"}],
                 "external_urls": {"spotify": "track-url"}},
    })

    result = client.get_current_track("access")

    assert result is not None
    assert (result.name, result.artists, result.spotify_url) == ("Song", ("One", "Two"), "track-url")


@pytest.mark.parametrize("status,payload", [(204, None), (200, {"item": None}), (200, {"currently_playing_type": "episode", "item": {}})])
def test_current_track_returns_none_for_valid_empty_or_non_track_response(
    client: SpotifyClient, session: Mock, status: int, payload: object
) -> None:
    session.get.return_value = response(status, payload)

    assert client.get_current_track("access") is None


def test_recent_tracks_parse_deduplicate_and_ignore_invalid_items(client: SpotifyClient, session: Mock) -> None:
    item = {"name": "Song", "type": "track", "artists": [{"name": "Artist"}], "external_urls": {"spotify": "url"}}
    session.get.return_value = response(200, {"items": [{"track": item}, {"track": item}, {"track": {"type": "episode"}}, {}]})

    result = client.get_recent_tracks("access")

    assert len(result) == 1
    assert result[0].spotify_url == "url"
    assert session.get.call_args.kwargs["params"] == {"limit": 20}


def test_missing_optional_track_fields_are_ignored_without_crashing(client: SpotifyClient, session: Mock) -> None:
    session.get.return_value = response(200, {"items": [{"track": {}}, {"track": None}]})

    assert client.get_recent_tracks("access") == []


def test_rate_limit_parses_retry_after(client: SpotifyClient, session: Mock) -> None:
    session.get.return_value = response(429, {}, {"Retry-After": "7"})

    with pytest.raises(SpotifyRateLimitError) as caught:
        client.get_current_track("access")

    assert caught.value.retry_after_seconds == 7


def test_generic_non_success_raises_safe_api_error(client: SpotifyClient, session: Mock) -> None:
    session.get.return_value = response(500, {"secret": "body"})

    with pytest.raises(SpotifyAPIError) as caught:
        client.get_recent_tracks("access")

    assert "body" not in str(caught.value)


def test_request_timeout_raises_safe_api_error(client: SpotifyClient, session: Mock) -> None:
    session.get.side_effect = requests.Timeout("token-value")

    with pytest.raises(SpotifyAPIError, match="timed out") as caught:
        client.get_current_track("access")

    assert "token-value" not in str(caught.value)
