import html
import re
from urllib.parse import urlparse

from .models import Track

START_MARKER = "<!-- SPOTIFY:START -->"
END_MARKER = "<!-- SPOTIFY:END -->"
_MARKDOWN_CHARACTER = re.compile(r"([\\`*_{\}\[\]()#+\-.!|>])")


def escape_markdown(text: str) -> str:
    return _MARKDOWN_CHARACTER.sub(r"\\\1", text)


def _track_line(track: Track) -> str:
    name = escape_markdown(track.name)
    artists = ", ".join(escape_markdown(artist) for artist in track.artists)
    return f"[{name}]({track.spotify_url}) — {artists}"


def _safe_artwork_url(track: Track) -> str | None:
    if track.album_image_url is None:
        return None
    parsed = urlparse(track.album_image_url)
    if parsed.scheme != "https" or not parsed.netloc:
        return None
    return track.album_image_url


def _artwork_cell(track: Track, size: int) -> str:
    artwork_url = _safe_artwork_url(track)
    if artwork_url is None:
        return "<td></td>"
    track_url = html.escape(track.spotify_url, quote=True)
    image_url = html.escape(artwork_url, quote=True)
    alt = html.escape(f"Album artwork for {track.name}", quote=True)
    return (
        f'<td><a href="{track_url}"><img src="{image_url}" width="{size}" height="{size}" '
        f'alt="{alt}" /></a></td>'
    )


def _track_text_cell(track: Track) -> str:
    track_url = html.escape(track.spotify_url, quote=True)
    name = html.escape(track.name)
    artists = ", ".join(html.escape(artist) for artist in track.artists)
    return f'<td><a href="{track_url}">{name}</a><br>{artists}</td>'


def _ledger_row(track: Track, size: int, index: int | None) -> str:
    index_cell = f"<td>{index:02d}</td>" if index is not None else ""
    return (
        "<tr>"
        f"{index_cell}{_artwork_cell(track, size)}{_track_text_cell(track)}"
        "</tr>"
    )


def _ledger(rows: list[str]) -> str:
    return "<table>\n" + "\n".join(rows) + "\n</table>"


def render_spotify_section(
    current_track: Track | None,
    recent_tracks: list[Track],
) -> str:
    lines = [START_MARKER, "### Listening To", ""]

    if current_track is not None:
        lines.append(_ledger([_ledger_row(current_track, 64, None)]))
    else:
        unique_tracks: list[Track] = []
        seen_urls: set[str] = set()
        for track in recent_tracks:
            if track.spotify_url in seen_urls:
                continue
            seen_urls.add(track.spotify_url)
            unique_tracks.append(track)
            if len(unique_tracks) == 5:
                break

        if unique_tracks:
            rows = [
                _ledger_row(track, 48, index)
                for index, track in enumerate(unique_tracks, start=1)
            ]
            lines.append(_ledger(rows))
        else:
            lines.append("No recent Spotify activity available.")

    lines.append(END_MARKER)
    return "\n".join(lines) + "\n"
