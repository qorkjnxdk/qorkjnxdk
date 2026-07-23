# Spotify README Integration Design

## Goal

Add a deliberately small, production-quality Python integration that updates only a marked Spotify section in the GitHub profile README. It will show the current track when one is playing, otherwise up to five unique recent tracks, and it will leave the README unchanged when Spotify access fails.

## Architecture

The implementation is a Python 3.12 package under `scripts/spotify_readme`. `SpotifyClient` owns all Spotify HTTP and response parsing, returning immutable `Track` values rather than raw response dictionaries. Pure rendering and README-replacement functions remain independent of HTTP, environment variables, and Git so they are straightforward to test.

The package uses `requests` directly instead of a Spotify SDK. This keeps the runtime dependency set small and makes authentication, status handling, timeouts, and safe exceptions explicit.

## Components

- `models.py` defines the frozen `Track` data class.
- `client.py` exchanges a refresh token, calls the currently-playing and recently-played endpoints, filters non-track items, safely handles missing optional fields, and maps failures to concise domain exceptions.
- `renderer.py` escapes Markdown-sensitive track and artist text and renders exactly one marker-bounded section with one trailing newline.
- `readme.py` validates that each marker occurs exactly once and in the correct order, replaces only the inclusive marker range, and avoids rewriting an unchanged file.
- `main.py` validates environment configuration, orchestrates Spotify access and rendering, updates the selected README path, and emits only safe status or error messages.
- `.github/workflows/update-spotify.yml` runs hourly at minute 17 and on demand, supplies repository secrets to the CLI, and stages only `README.md` when committing.

## Data Flow

1. GitHub Actions checks out the profile repository and installs Python 3.12 runtime dependencies.
2. The CLI reads `SPOTIFY_CLIENT_ID`, `SPOTIFY_CLIENT_SECRET`, and `SPOTIFY_REFRESH_TOKEN` from the environment.
3. The client exchanges the refresh token for a short-lived access token using the Spotify Accounts API.
4. The client requests the currently playing item. A `204`, missing item, or non-track item is treated as no current track.
5. Only when no track is currently playing, the client requests 20 recent records and returns up to five unique tracks in first-seen order.
6. The renderer produces current, recent, or empty-state Markdown.
7. The README updater validates and replaces only the Spotify marker range. It performs no write when the result is identical.
8. The workflow checks the README diff, stages only `README.md`, and commits with the GitHub Actions bot identity only when content changed.

## Error Handling and Security

Every HTTP request has an explicit timeout. Invalid or expired credentials raise `SpotifyAuthenticationError`; HTTP 429 raises `SpotifyRateLimitError` with a parsed optional retry delay; timeouts and other Spotify failures raise concise `SpotifyAPIError` messages. Exceptions never include credentials, access tokens, or complete response bodies.

Missing, duplicate, or reversed README markers raise `ReadmeMarkerError`. The CLI exits non-zero for configuration, Spotify, marker, or filesystem failures, so an operational failure cannot replace valid README content with misleading data. A valid empty Spotify response is rendered as the documented empty state.

Secrets exist only in environment variables and GitHub Actions repository secrets. `.env` is ignored, `.env.example` contains blank placeholders, and the workflow uses its built-in `GITHUB_TOKEN` rather than a personal token.

## README Placement

The Spotify section will be added after “Currently Working On,” preserving every existing profile section. Its initial contents will use the empty-state rendering so the markers and production renderer share one format.

## Testing

Tests use `pytest` and mocked `requests.Session` calls; they never contact Spotify. Development proceeds test-first in these independently committed slices:

1. Add and protect README markers.
2. Define `Track` and cover current, recent, escaping, deduplication, maximum-count, empty-state, and newline rendering behavior.
3. Cover marker validation, byte-preserving replacement, idempotence, and file-write behavior.
4. Cover token refresh, current/recent parsing, missing fields, deduplication, authentication, rate limiting, generic failures, and timeouts.
5. Cover CLI configuration and orchestration before implementing the entry point.
6. Add and validate the scheduled/manual workflow.
7. Add environment and one-time authorization setup documentation.

Final verification runs the complete pytest suite, Python compilation, whitespace checks, secret scans, workflow inspection, and an idempotence check. Real Spotify account operation remains a user setup step because no credentials are stored or requested during development.
