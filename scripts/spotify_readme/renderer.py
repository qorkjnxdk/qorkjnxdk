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


def _artwork_row(track: Track, size: int, prefix: str = "") -> str | None:
    artwork_url = _safe_artwork_url(track)
    if artwork_url is None:
        return None
    track_url = html.escape(track.spotify_url, quote=True)
    image_url = html.escape(artwork_url, quote=True)
    alt = html.escape(f"Album artwork for {track.name}", quote=True)
    name = html.escape(track.name)
    artists = ", ".join(html.escape(artist) for artist in track.artists)
    return (
        '<table><tr>'
        f'<td><a href="{track_url}"><img src="{image_url}" width="{size}" height="{size}" '
        f'alt="{alt}" /></a></td>'
        f'<td>{prefix}<a href="{track_url}">{name}</a> — {artists}</td>'
        '</tr></table>'
    )


def render_spotify_section(
    current_track: Track | None,
    recent_tracks: list[Track],
) -> str:
    lines = [START_MARKER, "### 🎧 Spotify", ""]

    if current_track is not None:
        current_row = _artwork_row(current_track, 64)
        lines.extend(["**Now playing**", "", current_row or _track_line(current_track)])
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
            lines.extend(["**Recently played**", ""])
            for index, track in enumerate(unique_tracks, start=1):
                artwork_row = _artwork_row(track, 48, prefix=f"{index}. ")
                lines.append(artwork_row or f"{index}. {_track_line(track)}")
        else:
            lines.append("No recent Spotify activity available.")

    lines.append(END_MARKER)
    return "\n".join(lines) + "\n"
