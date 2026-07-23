from pathlib import Path

START_MARKER = "<!-- SPOTIFY:START -->"
END_MARKER = "<!-- SPOTIFY:END -->"


class ReadmeMarkerError(ValueError):
    pass


def replace_spotify_section(
    readme_content: str,
    generated_section: str,
) -> str:
    if readme_content.count(START_MARKER) != 1:
        raise ReadmeMarkerError("README must contain exactly one Spotify start marker")
    if readme_content.count(END_MARKER) != 1:
        raise ReadmeMarkerError("README must contain exactly one Spotify end marker")

    start = readme_content.index(START_MARKER)
    end = readme_content.index(END_MARKER)
    if end < start:
        raise ReadmeMarkerError("Spotify end marker appears before start marker")

    suffix_start = end + len(END_MARKER)
    section = generated_section.rstrip("\r\n")
    return readme_content[:start] + section + readme_content[suffix_start:]


def update_readme_file(
    readme_path: Path,
    generated_section: str,
) -> bool:
    original = readme_path.read_text(encoding="utf-8")
    updated = replace_spotify_section(original, generated_section)
    if updated == original:
        return False
    readme_path.write_text(updated, encoding="utf-8", newline="")
    return True
