from scripts.spotify_readme.models import Track
from scripts.spotify_readme.renderer import escape_markdown, render_spotify_section


def track(name: str, url: str = "https://open.spotify.com/track/1", *artists: str) -> Track:
    return Track(name=name, artists=artists or ("Artist",), spotify_url=url)


def test_renders_current_track_in_preference_to_recent_tracks() -> None:
    result = render_spotify_section(track("Now"), [track("Old")])

    assert "**Now playing**" in result
    assert "[Now](https://open.spotify.com/track/1) — Artist" in result
    assert "Old" not in result


def test_renders_recent_tracks_with_multiple_artists() -> None:
    result = render_spotify_section(
        None,
        [track("Duet", "https://open.spotify.com/track/2", "One", "Two")],
    )

    assert "**Recently played**" in result
    assert "1. [Duet](https://open.spotify.com/track/2) — One, Two" in result


def test_escapes_markdown_sensitive_track_and_artist_text() -> None:
    result = render_spotify_section(
        track("A [track] *name*", "https://open.spotify.com/track/3", "An_Artist"),
        [],
    )

    assert r"A \[track\] \*name\*" in result
    assert r"An\_Artist" in result
    assert escape_markdown(r"a\b") == r"a\\b"


def test_deduplicates_recent_tracks_and_limits_to_five() -> None:
    tracks = [track(f"Track {index}", f"url-{index}") for index in range(1, 7)]
    tracks.insert(1, track("Duplicate", "url-1"))

    result = render_spotify_section(None, tracks)

    assert "Duplicate" not in result
    assert "Track 5" in result
    assert "Track 6" not in result
    assert result.count("\n1. ") == 1
    assert result.count("\n5. ") == 1


def test_renders_empty_state() -> None:
    result = render_spotify_section(None, [])

    assert "No recent Spotify activity available." in result
    assert "Now playing" not in result
    assert "Recently played" not in result


def test_result_has_exactly_one_trailing_newline() -> None:
    assert render_spotify_section(None, []).endswith("\n")
    assert not render_spotify_section(None, []).endswith("\n\n")
    assert render_spotify_section(None, []).count("<!-- SPOTIFY:START -->") == 1
    assert render_spotify_section(None, []).count("<!-- SPOTIFY:END -->") == 1
