# Spotify README Integration Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a tested Python updater and GitHub Actions workflow that safely renders Spotify listening activity inside one marked section of the profile README.

**Architecture:** A small `scripts.spotify_readme` package separates immutable data, Spotify HTTP access, Markdown rendering, marker-safe file replacement, and CLI orchestration. GitHub Actions supplies secrets and commits only a changed `README.md`; all Spotify calls are mocked in tests.

**Tech Stack:** Python 3.12, `requests`, `pytest`, GitHub Actions, Spotify Web API

## Global Constraints

- Runtime authentication uses only `SPOTIFY_CLIENT_ID`, `SPOTIFY_CLIENT_SECRET`, and `SPOTIFY_REFRESH_TOKEN`.
- Spotify scopes are exactly `user-read-currently-playing` and `user-read-recently-played`.
- Never log secrets, tokens, complete Spotify response bodies, or account identifiers.
- Never replace README content outside the unique ordered Spotify markers.
- Display no artwork, progress, device, timestamps, podcast episodes, explicit labels, or more than five recent tracks.
- Every HTTP request uses an explicit timeout; tests never contact Spotify.
- Runtime dependencies remain limited to `requests`; development adds `pytest`.

---

### Task 1: Add Spotify README Markers

**Files:**
- Modify: `README.md`

**Interfaces:**
- Produces: one `<!-- SPOTIFY:START -->` / `<!-- SPOTIFY:END -->` range consumed by `readme.py`.

- [ ] **Step 1: Capture the original README and add the empty section after “Currently Working On”**

```md
<!-- SPOTIFY:START -->
### 🎧 Spotify

No recent Spotify activity available.
<!-- SPOTIFY:END -->
```

- [ ] **Step 2: Verify only the append location changed**

Run: `git diff -- README.md` and `git diff --check`
Expected: all original content is preserved and exactly one marker pair is appended.

- [ ] **Step 3: Commit**

Run: `git add README.md && git commit -m "chore: add Spotify README markers"`

### Task 2: Build the Track Model and Renderer

**Files:**
- Create: `scripts/__init__.py`
- Create: `scripts/spotify_readme/__init__.py`
- Create: `scripts/spotify_readme/models.py`
- Create: `scripts/spotify_readme/renderer.py`
- Create: `tests/test_spotify_renderer.py`

**Interfaces:**
- Produces: frozen `Track(name: str, artists: tuple[str, ...], spotify_url: str)`.
- Produces: `escape_markdown(text: str) -> str` and `render_spotify_section(current_track: Track | None, recent_tracks: list[Track]) -> str`.

- [ ] **Step 1: Write renderer tests**

Cover current-track preference; up to five recent unique Spotify URLs in first-seen order; multiple artists joined with `, `; escaping `\\` and Markdown punctuation; empty state; and exactly one trailing newline.

- [ ] **Step 2: Run tests and verify RED**

Run: `python -m pytest tests/test_spotify_renderer.py -v`
Expected: collection fails because `scripts.spotify_readme` does not exist.

- [ ] **Step 3: Implement the immutable model and minimal renderer**

Use a frozen dataclass, a stable URL set for deduplication, list slicing for the maximum, and marker constants matching the README. Escape `\\`, `` ` ``, `*`, `_`, `{}`, `[]`, `()`, `#`, `+`, `-`, `.`, `!`, `|`, and `>` in Spotify-provided labels, while leaving URLs as link destinations.

- [ ] **Step 4: Run tests and verify GREEN**

Run: `python -m pytest tests/test_spotify_renderer.py -v`
Expected: all renderer tests pass.

- [ ] **Step 5: Commit**

Run: `git add scripts tests/test_spotify_renderer.py && git commit -m "feat: render Spotify README activity"`

### Task 3: Build Safe README Replacement

**Files:**
- Create: `scripts/spotify_readme/readme.py`
- Create: `tests/test_readme_update.py`

**Interfaces:**
- Produces: `START_MARKER`, `END_MARKER`, `ReadmeMarkerError`, `replace_spotify_section(readme_content: str, generated_section: str) -> str`, and `update_readme_file(readme_path: pathlib.Path, generated_section: str) -> bool`.

- [ ] **Step 1: Write README tests**

Cover inclusive replacement, unchanged prefix/suffix, identical output, each missing marker, duplicate start/end markers, reversed markers, a `True` file update, and a `False` no-op that preserves modification time.

- [ ] **Step 2: Run tests and verify RED**

Run: `python -m pytest tests/test_readme_update.py -v`
Expected: collection fails because `readme.py` does not exist.

- [ ] **Step 3: Implement strict marker validation and UTF-8 file updates**

Count both markers, validate their indexes, normalize the generated section to exactly one final newline for insertion, retain the original suffix bytes, and call `write_text` only when content differs.

- [ ] **Step 4: Run tests and verify GREEN**

Run: `python -m pytest tests/test_readme_update.py -v`
Expected: all README tests pass.

- [ ] **Step 5: Commit**

Run: `git add scripts/spotify_readme/readme.py tests/test_readme_update.py && git commit -m "feat: update marked README section"`

### Task 4: Build the Spotify HTTP Client

**Files:**
- Create: `scripts/spotify_readme/client.py`
- Create: `tests/test_spotify_client.py`
- Create: `requirements.txt`
- Create: `requirements-dev.txt`

**Interfaces:**
- Consumes: `Track`.
- Produces: `SpotifyAuthenticationError`, `SpotifyAPIError`, `SpotifyRateLimitError(retry_after_seconds: int | None)`, and `SpotifyClient` with the specified constructor and three public methods.

- [ ] **Step 1: Add compatible dependencies and write mocked client tests**

Set `requests>=2.32,<3` in `requirements.txt`; include `-r requirements.txt` and `pytest>=8,<9` in `requirements-dev.txt`. Mock `requests.Session.post/get` responses and timeout exceptions. Cover successful/invalid refresh, current parsing, `204`, missing item, non-track items, recent parsing/deduplication, missing optional fields, `429` with valid and invalid `Retry-After`, other failures, and timeouts.

- [ ] **Step 2: Install dependencies and verify RED**

Run: `python -m pip install -r requirements-dev.txt` then `python -m pytest tests/test_spotify_client.py -v`
Expected: collection fails because `client.py` does not exist.

- [ ] **Step 3: Implement deliberate status handling and safe parsing**

Use HTTP Basic authentication for the token exchange; bearer headers for API calls; a session-owned timeout; request limit `20` for recent activity; safe mapping helpers private to the client module; authentication mapping for token endpoint `400`/`401`; `429` mapping with optional integer delay; and concise safe exception messages for request failures.

- [ ] **Step 4: Run client and full tests**

Run: `python -m pytest tests/test_spotify_client.py -v` then `python -m pytest -v`
Expected: all tests pass without network access.

- [ ] **Step 5: Commit**

Run: `git add requirements*.txt scripts/spotify_readme/client.py tests/test_spotify_client.py && git commit -m "feat: fetch Spotify listening activity"`

### Task 5: Build the CLI

**Files:**
- Create: `scripts/spotify_readme/main.py`
- Create: `tests/test_spotify_main.py`

**Interfaces:**
- Consumes: `SpotifyClient`, `render_spotify_section`, `update_readme_file`.
- Produces: `main(argv: list[str] | None = None) -> int`, runnable with `python -m scripts.spotify_readme.main --readme-path README.md`.

- [ ] **Step 1: Write CLI tests**

Cover missing environment names without values, current-track flow without a recent call, fallback recent flow, updated/no-op summaries, custom README path, safe domain-error output, and unexpected filesystem errors. Patch the client class and updater at module boundaries; assert no supplied secret appears in output.

- [ ] **Step 2: Run tests and verify RED**

Run: `python -m pytest tests/test_spotify_main.py -v`
Expected: collection fails because `main.py` does not exist.

- [ ] **Step 3: Implement argparse orchestration**

Read required environment values after parsing, report missing variable names only, fetch recent tracks only if current is `None`, print the two required success summaries, catch expected runtime/filesystem errors at the entry boundary, and exit via `raise SystemExit(main())`.

- [ ] **Step 4: Run tests and a fully mocked local CLI dry run**

Run: `python -m pytest tests/test_spotify_main.py -v` and then the complete suite. Exercise `main()` against a temporary README with a patched client and confirm only the marker section changes.

- [ ] **Step 5: Commit**

Run: `git add scripts/spotify_readme/main.py tests/test_spotify_main.py && git commit -m "feat: add Spotify README updater CLI"`

### Task 6: Add GitHub Actions Automation

**Files:**
- Create: `.github/workflows/update-spotify.yml`
- Create: `tests/test_workflow.py`

**Interfaces:**
- Consumes: module CLI, `requirements.txt`, three Actions secrets.
- Produces: manual and hourly workflow with `contents: write` and serialized updates.

- [ ] **Step 1: Write a structural workflow test and verify RED**

Read the YAML as text and assert the required name, dispatch trigger, cron `17 * * * *`, write permission, concurrency group, Python `3.12`, three secret references, README-only diff/stage commands, bot identity, and commit message.

Run: `python -m pytest tests/test_workflow.py -v`
Expected: failure because the workflow does not exist.

- [ ] **Step 2: Implement the workflow**

Use `actions/checkout`, `actions/setup-python`, `pip install -r requirements.txt`, the module CLI, `git diff --quiet -- README.md` to detect changes, and a guarded commit step containing exactly `git add README.md` before commit and push.

- [ ] **Step 3: Validate and commit**

Run: `python -m pytest tests/test_workflow.py -v` and inspect the YAML with Python or an available YAML parser.

Run: `git add .github/workflows/update-spotify.yml tests/test_workflow.py && git commit -m "ci: schedule Spotify README updates"`

### Task 7: Add Reproducible Authorization and Setup Documentation

**Files:**
- Create: `.env.example`
- Modify: `.gitignore`
- Create: `scripts/spotify_readme/authorize.py`
- Create: `tests/test_spotify_authorize.py`
- Modify: `README.md`

**Interfaces:**
- Produces: local-only Authorization Code helper accepting `--redirect-uri`, printing an authorization URL, accepting a callback URL or code, exchanging it once, and printing the refresh token without writing it.

- [ ] **Step 1: Write authorization helper tests and verify RED**

Cover exact scopes, URL generation, callback-code extraction, direct-code input, safe token exchange failure, and no credential-file creation.

- [ ] **Step 2: Implement the minimal helper**

Use standard-library URL utilities plus `requests`, require client ID/secret from the environment, accept redirect URI from an argument or `SPOTIFY_REDIRECT_URI`, generate a random state value, and never run from the production workflow.

- [ ] **Step 3: Add environment safety and concise README setup documentation**

Create the three blank placeholders in `.env.example`; extend `.gitignore` with `.env`; document Spotify application creation, local redirect URI, exact scopes, one-time helper use, Actions secrets, manual workflow run, marked-section verification, and reauthorization after revocation/expiry. Keep existing profile content intact.

- [ ] **Step 4: Test and commit**

Run: `python -m pytest tests/test_spotify_authorize.py -v` and `python -m pytest -v`.

Run: `git add .env.example .gitignore README.md scripts/spotify_readme/authorize.py tests/test_spotify_authorize.py && git commit -m "docs: document Spotify integration setup"`

### Task 8: Final Verification

**Files:**
- Review all files changed since `main`.

- [ ] **Step 1: Run the full automated suite and syntax compilation**

Run: `python -m pytest -v` and `python -m compileall scripts`
Expected: zero failures and successful compilation.

- [ ] **Step 2: Verify repository hygiene and requirements**

Run: `git status --short`, `git diff --check main...HEAD`, `git diff --stat main...HEAD`, `git diff main...HEAD`, and a tracked-file secret/name scan.
Expected: clean worktree, no whitespace errors, no credentials, only scoped files, and unchanged unrelated README content.

- [ ] **Step 3: Perform manual behavioral verification**

Render twice and compare exact output; run `update_readme_file` twice against a temporary README and verify the second call returns `False`; inspect the workflow to confirm only `README.md` is staged; exercise safe error output with sentinel credentials and confirm no sentinel value appears.

- [ ] **Step 4: Report completion accurately**

List files created/modified, commands executed, results, manual checks, and the remaining Spotify/GitHub setup. Explicitly state that real-account operation was not tested unless valid credentials were actually supplied.
