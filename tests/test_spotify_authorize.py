from unittest.mock import Mock
from urllib.parse import parse_qs, urlparse

import pytest

from scripts.spotify_readme.authorize import (
    SCOPES,
    AuthorizationError,
    build_authorization_url,
    extract_authorization_code,
    exchange_code,
)


def test_authorization_url_requests_exact_scopes() -> None:
    url = build_authorization_url("client", "http://127.0.0.1:8080/callback", "state")
    query = parse_qs(urlparse(url).query)

    assert query["scope"] == [" ".join(SCOPES)]
    assert SCOPES == ("user-read-currently-playing", "user-read-recently-played")
    assert query["state"] == ["state"]


def test_extracts_code_from_callback_or_accepts_direct_code() -> None:
    assert extract_authorization_code("http://localhost/callback?code=abc&state=x") == "abc"
    assert extract_authorization_code("direct-code") == "direct-code"


def test_exchange_code_returns_refresh_token_without_exposing_response() -> None:
    session = Mock()
    session.post.return_value = Mock(status_code=200)
    session.post.return_value.json.return_value = {"refresh_token": "refresh"}

    assert exchange_code("client", "secret", "code", "http://localhost", session=session) == "refresh"


def test_exchange_code_failure_is_safe() -> None:
    session = Mock()
    session.post.return_value = Mock(status_code=400)
    session.post.return_value.json.return_value = {"error": "secret-body"}

    with pytest.raises(AuthorizationError) as caught:
        exchange_code("client", "secret", "code", "http://localhost", session=session)

    assert "secret-body" not in str(caught.value)
