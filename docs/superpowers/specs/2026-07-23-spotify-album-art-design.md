# Spotify Album Artwork Design

## Goal

Add compact, linked album artwork to the existing Spotify README section without adding API calls, weakening the text fallback, or changing the updater workflow.

## Data Model and Parsing

`Track` gains `album_image_url: str | None = None`. The default preserves existing callers and tests. `SpotifyClient` reads the existing `track.album.images` array returned by both currently-playing and recently-played endpoints. It selects the smallest valid image whose width is at least 64 pixels; if dimensions are missing, it uses the last valid URL because Spotify orders album images widest first. Missing, empty, or malformed image data produces `None` and never discards an otherwise valid track.

No additional endpoint, scope, secret, dependency, or network request is introduced.

## Rendering

The section keeps the existing headings and track text. Tracks with artwork render as compact HTML tables because GitHub Markdown does not reliably align an image and multiline text in a normal list:

- Currently playing: one row with a linked 64×64 original artwork image and the linked track/artist text.
- Recently played: one row per track with a linked 48×48 original artwork image, its list number, and the linked track/artist text.
- Missing artwork: the existing Markdown line/list item renders unchanged.

Each image links to the track on Spotify, includes escaped descriptive alt text, preserves its aspect ratio, and is not cropped, overlaid, proxied, cached, or committed. The existing “Spotify” heading provides service attribution, while each artwork and track links back to Spotify.

## Safety and Compatibility

Only URLs with an `https` scheme and a non-empty host are rendered as images. Track and artist escaping, recent-track deduplication, the five-track maximum, marker replacement, idempotence, and empty-state behavior remain unchanged. If Spotify omits artwork or returns malformed image metadata, the updater succeeds with text-only output.

## Testing

Tests are written before implementation and cover:

- Immutable model compatibility with and without artwork.
- Client parsing for current and recent artwork.
- Selection from multiple image sizes.
- Missing and malformed artwork fallback.
- Linked 64×64 current artwork.
- Linked 48×48 recent artwork.
- Safe URL and HTML-alt escaping.
- Mixed recent rows with and without artwork.
- Existing renderer, client, README, CLI, authorization, and workflow behavior.

Final verification runs the complete test suite, Python compilation, diff checks, a tracked-secret scan, and a local render/idempotence demonstration.
