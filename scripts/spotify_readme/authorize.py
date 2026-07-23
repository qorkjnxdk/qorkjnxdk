import argparse
import os
import secrets
import sys
from urllib.parse import parse_qs, urlencode, urlparse

import requests

AUTHORIZE_URL = "https://accounts.spotify.com/authorize"
TOKEN_URL = "https://accounts.spotify.com/api/token"
SCOPES = ("user-read-currently-playing", "user-read-recently-played")


class AuthorizationError(RuntimeError):
    pass


def build_authorization_url(client_id: str, redirect_uri: str, state: str) -> str:
    query = urlencode({
        "client_id": client_id,
        "response_type": "code",
        "redirect_uri": redirect_uri,
        "scope": " ".join(SCOPES),
        "state": state,
    })
    return f"{AUTHORIZE_URL}?{query}"


def extract_authorization_code(callback_or_code: str) -> str:
    value = callback_or_code.strip()
    if "://" not in value:
        if not value:
            raise AuthorizationError("Authorization code is missing")
        return value
    codes = parse_qs(urlparse(value).query).get("code", [])
    if not codes or not codes[0]:
        raise AuthorizationError("Callback URL does not contain an authorization code")
    return codes[0]


def exchange_code(
    client_id: str,
    client_secret: str,
    code: str,
    redirect_uri: str,
    *,
    session: requests.Session | None = None,
    timeout_seconds: float = 10.0,
) -> str:
    http = session or requests.Session()
    try:
        response = http.post(
            TOKEN_URL,
            auth=(client_id, client_secret),
            data={"grant_type": "authorization_code", "code": code, "redirect_uri": redirect_uri},
            timeout=timeout_seconds,
        )
    except requests.RequestException as error:
        raise AuthorizationError("Spotify token exchange failed") from error
    if response.status_code != 200:
        raise AuthorizationError(f"Spotify token exchange failed with status {response.status_code}")
    try:
        payload = response.json()
    except ValueError as error:
        raise AuthorizationError("Spotify returned an invalid token response") from error
    refresh_token = payload.get("refresh_token") if isinstance(payload, dict) else None
    if not isinstance(refresh_token, str) or not refresh_token:
        raise AuthorizationError("Spotify did not return a refresh token")
    return refresh_token


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Obtain a Spotify refresh token locally")
    parser.add_argument("--redirect-uri", default=os.environ.get("SPOTIFY_REDIRECT_URI"))
    args = parser.parse_args(argv)
    client_id = os.environ.get("SPOTIFY_CLIENT_ID")
    client_secret = os.environ.get("SPOTIFY_CLIENT_SECRET")
    if not client_id or not client_secret or not args.redirect_uri:
        print("SPOTIFY_CLIENT_ID, SPOTIFY_CLIENT_SECRET, and a redirect URI are required", file=sys.stderr)
        return 1

    state = secrets.token_urlsafe(24)
    print("Open this URL in your browser and approve access:\n")
    print(build_authorization_url(client_id, args.redirect_uri, state))
    supplied = input("\nPaste the callback URL or authorization code: ").strip()
    try:
        if "://" in supplied:
            callback_state = parse_qs(urlparse(supplied).query).get("state", [None])[0]
            if callback_state != state:
                raise AuthorizationError("Callback state did not match")
        code = extract_authorization_code(supplied)
        refresh_token = exchange_code(client_id, client_secret, code, args.redirect_uri)
    except AuthorizationError as error:
        print(f"Authorization failed: {error}", file=sys.stderr)
        return 1
    print(f"\nRefresh token:\n{refresh_token}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
