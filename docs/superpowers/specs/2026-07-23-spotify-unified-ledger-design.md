# Spotify Unified Ledger Design

## Purpose

Replace the current stack of individually boxed Spotify tracks with a calmer, denser layout that reads as one intentional section of the GitHub profile.

## Visual Direction

The design uses the **Swiss** anchor from the frontend-design system. GitHub controls the surface, typography, and link color, so the layout commits to the anchor through structure: left alignment, one continuous grid, 1 px hairline rules, asymmetric spacing, and tabular two-digit track indices.

The visible differentiator is the index column. `01` through `05` act as composition elements that create a steady vertical rhythm, rather than appearing as ordinary Markdown list markers.

## Content and Hierarchy

The generated section has one heading:

```md
### Listening To
```

There is no Spotify heading, headphone glyph, “Now playing,” or “Recently played” subheading. Every remaining string names real information: track index, track title, and artist.

## Recent Tracks

All available recent tracks render inside one HTML table:

- One row per track.
- Two-digit index in the first cell.
- Linked 48×48 original album artwork in the second cell when available.
- Linked track title on the first text line and artist names on the second.
- A hairline boundary between rows comes from the single table rather than separate nested tables.
- Up to five unique tracks remain visible in first-seen order.

If artwork is missing or unsafe, the artwork cell remains empty and the track text remains visible in the same ledger.

## Current Track

A current track uses the same ledger vocabulary as recent tracks, but renders as a single row without an index. Its original artwork remains 64×64 to give the live item slightly more presence. No “Now playing” subheading is added.

## Empty State

When Spotify returns no current or recent tracks, the section renders:

```md
### Listening To

No recent Spotify activity available.
```

The marker comments remain unchanged.

## Technical Boundaries

Only `renderer.py` and its tests change. Spotify authentication, HTTP parsing, artwork selection, scopes, workflow scheduling, README marker replacement, dependencies, and secrets remain untouched.

The HTML uses only GitHub-supported table, link, image, and line-break elements with escaped attributes and text. No CSS, JavaScript, SVG generation, external hosting, or fabricated data is introduced.

## Verification

Tests cover the single heading, absence of subheadings, one-table recent layout, two-digit indices, title/artist line separation, linked artwork, missing-artwork rows, current-track layout, empty state, five-track limit, escaping, and exact trailing newline. Final verification includes the full suite, compilation, diff checks, and a real-data render using the five tracks shown in the approved preview.
