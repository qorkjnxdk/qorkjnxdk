from pathlib import Path

import pytest

from scripts.spotify_readme.readme import (
    END_MARKER,
    START_MARKER,
    ReadmeMarkerError,
    replace_spotify_section,
    update_readme_file,
)


GENERATED = f"{START_MARKER}\nnew\n{END_MARKER}\n"


def test_replaces_only_marked_section_and_preserves_surrounding_content() -> None:
    original = f"before\n{START_MARKER}\nold\n{END_MARKER}\nafter\n"

    assert replace_spotify_section(original, GENERATED) == "before\n" + GENERATED + "after\n"


def test_identical_section_returns_unchanged_content() -> None:
    original = "before\n" + GENERATED + "after\n"

    assert replace_spotify_section(original, GENERATED) == original


@pytest.mark.parametrize(
    "content",
    [
        f"text\n{END_MARKER}\n",
        f"text\n{START_MARKER}\n",
        f"{START_MARKER}\na\n{START_MARKER}\n{END_MARKER}\n",
        f"{START_MARKER}\n{END_MARKER}\n{END_MARKER}\n",
        f"{END_MARKER}\n{START_MARKER}\n",
    ],
)
def test_rejects_missing_duplicate_or_reversed_markers(content: str) -> None:
    with pytest.raises(ReadmeMarkerError):
        replace_spotify_section(content, GENERATED)


def test_update_readme_file_returns_true_after_change(tmp_path: Path) -> None:
    readme = tmp_path / "README.md"
    readme.write_text(f"{START_MARKER}\nold\n{END_MARKER}\n", encoding="utf-8")

    assert update_readme_file(readme, GENERATED) is True
    assert readme.read_text(encoding="utf-8") == GENERATED


def test_update_readme_file_returns_false_without_rewriting(tmp_path: Path) -> None:
    readme = tmp_path / "README.md"
    readme.write_text(GENERATED, encoding="utf-8")
    before = readme.stat().st_mtime_ns

    assert update_readme_file(readme, GENERATED) is False
    assert readme.stat().st_mtime_ns == before
