import re

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


def render_spotify_section(
    current_track: Track | None,
    recent_tracks: list[Track],
) -> str:
    lines = [START_MARKER, "### 🎧 Spotify", ""]

    if current_track is not None:
        lines.extend(["**Now playing**", "", _track_line(current_track)])
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
            lines.extend(
                f"{index}. {_track_line(track)}"
                for index, track in enumerate(unique_tracks, start=1)
            )
        else:
            lines.append("No recent Spotify activity available.")

    lines.append(END_MARKER)
    return "\n".join(lines) + "\n"
