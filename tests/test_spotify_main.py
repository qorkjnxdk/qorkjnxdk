from pathlib import Path
from unittest.mock import Mock

import pytest

from scripts.spotify_readme import main as main_module
from scripts.spotify_readme.models import Track


SECRETS = {
    "SPOTIFY_CLIENT_ID": "client-sentinel",
    "SPOTIFY_CLIENT_SECRET": "secret-sentinel",
    "SPOTIFY_REFRESH_TOKEN": "refresh-sentinel",
}


def configure(monkeypatch: pytest.MonkeyPatch) -> None:
    for name, value in SECRETS.items():
        monkeypatch.setenv(name, value)


def readme(tmp_path: Path) -> Path:
    path = tmp_path / "PROFILE.md"
    path.write_text("before\n<!-- SPOTIFY:START -->\nold\n<!-- SPOTIFY:END -->\nafter\n", encoding="utf-8")
    return path


def test_reports_missing_environment_variable_names_only(monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
    for name in SECRETS:
        monkeypatch.delenv(name, raising=False)

    assert main_module.main([]) == 1
    output = capsys.readouterr().err
    assert "SPOTIFY_CLIENT_ID" in output
    assert "SPOTIFY_CLIENT_SECRET" in output
    assert "SPOTIFY_REFRESH_TOKEN" in output


def test_current_track_flow_skips_recent_and_updates_readme(monkeypatch: pytest.MonkeyPatch, tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    configure(monkeypatch)
    path = readme(tmp_path)
    client = Mock()
    client.refresh_access_token.return_value = "access"
    client.get_current_track.return_value = Track("Current", ("Artist",), "url")
    monkeypatch.setattr(main_module, "SpotifyClient", Mock(return_value=client))

    assert main_module.main(["--readme-path", str(path)]) == 0
    assert "README updated" in capsys.readouterr().out
    client.get_recent_tracks.assert_not_called()
    assert "Current" in path.read_text(encoding="utf-8")


def test_falls_back_to_recent_tracks_and_reports_noop(monkeypatch: pytest.MonkeyPatch, tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    configure(monkeypatch)
    path = readme(tmp_path)
    client = Mock()
    client.refresh_access_token.return_value = "access"
    client.get_current_track.return_value = None
    client.get_recent_tracks.return_value = []
    monkeypatch.setattr(main_module, "SpotifyClient", Mock(return_value=client))

    assert main_module.main(["--readme-path", str(path)]) == 0
    assert main_module.main(["--readme-path", str(path)]) == 0
    assert "README already up to date" in capsys.readouterr().out
    client.get_recent_tracks.assert_called_with("access")


def test_safe_error_does_not_print_credentials(monkeypatch: pytest.MonkeyPatch, tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    configure(monkeypatch)
    client = Mock()
    client.refresh_access_token.side_effect = RuntimeError("safe failure")
    monkeypatch.setattr(main_module, "SpotifyClient", Mock(return_value=client))

    assert main_module.main(["--readme-path", str(readme(tmp_path))]) == 1
    output = capsys.readouterr().err
    assert "safe failure" in output
    assert all(value not in output for value in SECRETS.values())
