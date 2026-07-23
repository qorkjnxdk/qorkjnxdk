# Spotify Album Artwork Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Render compact, linked Spotify album artwork for current and recent tracks with a safe text-only fallback.

**Architecture:** Extend the immutable `Track` boundary with an optional artwork URL, parse it from the album data already returned by Spotify, and render it through small HTML tables. Keep the HTTP flow, scopes, marker replacement, and workflow unchanged.

**Tech Stack:** Python 3.12, `requests`, `pytest`, GitHub-flavored Markdown/HTML

## Global Constraints

- Make no additional Spotify API calls and request no additional scopes.
- Render only valid HTTPS artwork URLs with non-empty hosts.
- Preserve original artwork without cropping, overlays, proxying, caching, or committing images.
- Link every artwork image to its Spotify track.
- Preserve text-only fallback, deduplication, five-track maximum, marker safety, and idempotence.

---

### Task 1: Parse Optional Album Artwork

**Files:**
- Modify: `scripts/spotify_readme/models.py`
- Modify: `scripts/spotify_readme/client.py`
- Modify: `tests/test_spotify_client.py`

**Interfaces:**
- Produces: `Track.album_image_url: str | None = None`.
- Produces: client parsing that selects the smallest valid image at least 64 pixels wide, otherwise the last valid URL in Spotify's widest-first array.

- [ ] **Step 1: Write failing client tests**

Add tests constructing current and recent track payloads with `album.images`. Assert selection of the 64-or-larger candidate, `None` for missing/malformed images, and preservation of valid tracks when artwork is absent.

- [ ] **Step 2: Run tests and verify RED**

Run: `python -m pytest tests/test_spotify_client.py -v`
Expected: failures because `Track` has no `album_image_url` and the client does not parse images.

- [ ] **Step 3: Implement the minimal model and parser change**

Add `album_image_url: str | None = None` after existing required fields. Add a private `_parse_album_image_url(raw: dict[str, object]) -> str | None` helper and pass its result into `Track` without changing track validity rules.

- [ ] **Step 4: Verify GREEN and commit**

Run: `python -m pytest tests/test_spotify_client.py -v` and `python -m pytest -q`.

Run: `git add scripts/spotify_readme/models.py scripts/spotify_readme/client.py tests/test_spotify_client.py && git commit -m "feat: parse Spotify album artwork"`

### Task 2: Render Compact Linked Artwork

**Files:**
- Modify: `scripts/spotify_readme/renderer.py`
- Modify: `tests/test_spotify_renderer.py`

**Interfaces:**
- Consumes: `Track.album_image_url`.
- Produces: 64×64 current artwork and 48×48 recent artwork linked to `Track.spotify_url`.

- [ ] **Step 1: Write failing renderer tests**

Add current and recent artwork assertions for linked `<img>` elements, exact dimensions, escaped alt text, mixed artwork/text-only recent tracks, rejection of HTTP or hostless image URLs, and unchanged output when artwork is `None`.

- [ ] **Step 2: Run tests and verify RED**

Run: `python -m pytest tests/test_spotify_renderer.py -v`
Expected: failures because renderer output contains no images.

- [ ] **Step 3: Implement minimal safe HTML rendering**

Validate artwork with `urllib.parse.urlparse`, escape HTML attributes with `html.escape(..., quote=True)`, and build compact table rows. Use the existing escaped Markdown track line in the text cell and retain the current Markdown-only path for tracks without artwork.

- [ ] **Step 4: Verify GREEN and commit**

Run: `python -m pytest tests/test_spotify_renderer.py -v` and `python -m pytest -q`.

Run: `git add scripts/spotify_readme/renderer.py tests/test_spotify_renderer.py && git commit -m "feat: render Spotify album artwork"`

### Task 3: Final Verification

**Files:**
- Review all changes relative to `main`.

- [ ] **Step 1: Run complete automated verification**

Run: `python -m pytest -v`, `python -m compileall -q scripts`, `git diff --check main...HEAD`, and `git status --short`.
Expected: all tests pass, compilation succeeds, no whitespace errors, and a clean worktree.

- [ ] **Step 2: Perform a local render demonstration**

Render current and recent tracks with valid, missing, and malformed artwork. Assert the correct dimensions, Spotify links, text fallback, exactly one marker pair, and identical repeated output.

- [ ] **Step 3: Review security and scope**

Confirm no image files or credentials are tracked, no new dependency/scope/API request exists, and README replacement tests still prove content outside markers is preserved.
