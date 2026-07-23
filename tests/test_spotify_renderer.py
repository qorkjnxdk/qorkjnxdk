from scripts.spotify_readme.models import Track
from scripts.spotify_readme.renderer import escape_markdown, render_spotify_section


def track(name: str, url: str = "https://open.spotify.com/track/1", *artists: str) -> Track:
    return Track(name=name, artists=artists or ("Artist",), spotify_url=url)


def test_renders_current_track_in_preference_to_recent_tracks() -> None:
    result = render_spotify_section(track("Now"), [track("Old")])

    assert "### Listening To" in result
    assert "Now playing" not in result
    assert "Recently played" not in result
    assert '<a href="https://open.spotify.com/track/1">Now</a><br>Artist' in result
    assert result.count("<table>") == 1
    assert ">01<" not in result
    assert "Old" not in result


def test_renders_recent_tracks_with_multiple_artists() -> None:
    result = render_spotify_section(
        None,
        [track("Duet", "https://open.spotify.com/track/2", "One", "Two")],
    )

    assert "### Listening To" in result
    assert "Recently played" not in result
    assert ">01<" in result
    assert '<a href="https://open.spotify.com/track/2">Duet</a><br>One, Two' in result
    assert result.count("<table>") == 1


def test_escapes_markdown_sensitive_track_and_artist_text() -> None:
    result = render_spotify_section(
        track("A [track] *name*", "https://open.spotify.com/track/3", "An_Artist"),
        [],
    )

    assert "A [track] *name*" in result
    assert "An_Artist" in result
    assert escape_markdown(r"a\b") == r"a\\b"


def test_deduplicates_recent_tracks_and_limits_to_five() -> None:
    tracks = [track(f"Track {index}", f"url-{index}") for index in range(1, 7)]
    tracks.insert(1, track("Duplicate", "url-1"))

    result = render_spotify_section(None, tracks)

    assert "Duplicate" not in result
    assert "Track 5" in result
    assert "Track 6" not in result
    assert result.count(">01<") == 1
    assert result.count(">05<") == 1
    assert result.count("<table>") == 1


def test_renders_empty_state() -> None:
    result = render_spotify_section(None, [])

    assert "### Listening To" in result
    assert "No recent Spotify activity available." in result
    assert "Now playing" not in result
    assert "Recently played" not in result


def test_result_has_exactly_one_trailing_newline() -> None:
    assert render_spotify_section(None, []).endswith("\n")
    assert not render_spotify_section(None, []).endswith("\n\n")
    assert render_spotify_section(None, []).count("<!-- SPOTIFY:START -->") == 1
    assert render_spotify_section(None, []).count("<!-- SPOTIFY:END -->") == 1


def test_renders_linked_current_album_art_at_64_pixels_with_safe_alt_text() -> None:
    current = Track(
        name='A <Song> "Live"',
        artists=("Artist",),
        spotify_url="https://open.spotify.com/track/current",
        album_image_url="https://i.scdn.co/image/current",
    )

    result = render_spotify_section(current, [])

    assert '<a href="https://open.spotify.com/track/current">' in result
    assert 'src="https://i.scdn.co/image/current"' in result
    assert 'width="64" height="64"' in result
    assert 'alt="Album artwork for A &lt;Song&gt; &quot;Live&quot;"' in result
    assert result.count("<table>") == 1
    assert ">01<" not in result


def test_renders_recent_album_art_at_48_pixels_and_keeps_text_fallback() -> None:
    with_art = Track(
        name="With Art",
        artists=("Artist",),
        spotify_url="https://open.spotify.com/track/with-art",
        album_image_url="https://i.scdn.co/image/recent",
    )
    without_art = track("Without Art", "https://open.spotify.com/track/without-art")

    result = render_spotify_section(None, [with_art, without_art])

    assert 'src="https://i.scdn.co/image/recent"' in result
    assert 'width="48" height="48"' in result
    assert ">01<" in result and ">02<" in result
    assert '<td></td><td><a href="https://open.spotify.com/track/without-art">Without Art</a><br>Artist</td>' in result
    assert result.count("<table>") == 1


def test_does_not_render_unsafe_album_art_url() -> None:
    current = Track(
        name="Unsafe",
        artists=("Artist",),
        spotify_url="https://open.spotify.com/track/unsafe",
        album_image_url="http://example.com/image.jpg",
    )

    result = render_spotify_section(current, [])

    assert "<img" not in result
    assert '<td></td><td><a href="https://open.spotify.com/track/unsafe">Unsafe</a><br>Artist</td>' in result


def test_uses_listening_to_as_the_only_visible_heading() -> None:
    result = render_spotify_section(None, [track("Song")])

    assert result.count("### Listening To") == 1
    assert "### 🎧 Spotify" not in result
    assert "**Now playing**" not in result
    assert "**Recently played**" not in result
