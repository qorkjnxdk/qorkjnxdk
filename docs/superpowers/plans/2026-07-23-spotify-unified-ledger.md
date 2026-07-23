# Spotify Unified Ledger Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Render current or recent Spotify activity as one clean “Listening To” ledger that matches the approved preview.

**Architecture:** Change only the pure renderer and renderer tests. Build one HTML table for all recent tracks, retain safe artwork and text escaping, and leave Spotify API, CLI, README replacement, workflow, dependencies, and secrets unchanged.

**Tech Stack:** Python 3.12, pytest, GitHub-flavored Markdown with safe inline HTML

## Global Constraints

- Use `### Listening To` as the only visible heading.
- Render no “Spotify,” “Now playing,” or “Recently played” label.
- Use one table for recent tracks, two-digit indices, 48×48 artwork, and title/artist line separation.
- Use one row without an index and 64×64 artwork for a current track.
- Keep text visible when artwork is missing or unsafe.
- Preserve five-track maximum, deduplication, escaping, marker safety, and idempotence.
- Add no API calls, scopes, dependencies, external assets, or fabricated content.

---

### Task 1: Specify the Unified Ledger

**Files:**
- Modify: `tests/test_spotify_renderer.py`

**Interfaces:**
- Consumes: `Track` and `render_spotify_section(current_track, recent_tracks)`.
- Produces: behavioral expectations for the new heading and table structure.

- [ ] **Step 1: Replace layout-specific assertions with the approved behavior**

Add tests asserting:

```python
assert "### Listening To" in result
assert "Spotify" not in visible_result
assert "Now playing" not in result
assert "Recently played" not in result
assert result.count("<table>") == 1
assert ">01<" in result and ">05<" in result
assert 'width="48" height="48"' in result
assert "<br>" in result
```

Also cover a current row without an index, a mixed recent list with an empty artwork cell, unsafe artwork fallback, the empty state, deduplication, five-track maximum, escaping, markers, and exactly one trailing newline.

- [ ] **Step 2: Run renderer tests and verify RED**

Run: `python -m pytest tests/test_spotify_renderer.py -v`

Expected: failures showing the old Spotify/subheading copy, separate table per artwork row, ordinary list indices, and single-line title/artist text.

### Task 2: Implement and Verify the Unified Ledger

**Files:**
- Modify: `scripts/spotify_readme/renderer.py`
- Test: `tests/test_spotify_renderer.py`

**Interfaces:**
- Produces: `render_spotify_section(current_track: Track | None, recent_tracks: list[Track]) -> str` with unchanged signature.

- [ ] **Step 1: Implement focused rendering helpers**

Keep `_safe_artwork_url`. Replace per-row tables with helpers that return:

```python
def _artwork_cell(track: Track, size: int) -> str:
    ...

def _track_text_cell(track: Track, prefix: str = "") -> str:
    ...

def _ledger_row(track: Track, size: int, index: int | None) -> str:
    ...
```

The index cell contains `01` through `05`; the artwork cell contains a linked image or is empty; the text cell contains a linked HTML-escaped title, `<br>`, and HTML-escaped artists.

- [ ] **Step 2: Assemble one table**

Use:

```python
lines = [START_MARKER, "### Listening To", ""]
```

For current activity, append one table containing one 64×64 row without an index. For recent activity, append one table containing all 48×48 indexed rows. For empty activity, append the existing empty-state sentence.

- [ ] **Step 3: Run targeted and complete verification**

Run: `python -m pytest tests/test_spotify_renderer.py -v`

Expected: all renderer tests pass.

Run: `python -m pytest -v` and `python -m compileall -q scripts`

Expected: all project tests pass and compilation succeeds.

- [ ] **Step 4: Commit**

Run:

```bash
git add scripts/spotify_readme/renderer.py tests/test_spotify_renderer.py
git commit -m "feat: refine Spotify listening layout"
```

### Task 3: Merge and Publish

**Files:**
- Review all branch changes relative to `main`.

- [ ] **Step 1: Verify scope and generated output**

Run `git diff --check main...HEAD`, inspect the full diff, and render the five real tracks from the approved preview. Confirm one heading, one table, two-digit indices, linked artwork, title/artist separation, and identical repeated output.

- [ ] **Step 2: Merge into latest main**

Fetch and fast-forward `main`, merge `codex/spotify-layout`, and rerun the complete tests on the merged result.

- [ ] **Step 3: Push main**

Run `git push origin main` only after merged verification succeeds. Preserve any unrelated user files and remove the feature worktree/branch after the push is confirmed.
