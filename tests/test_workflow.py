from pathlib import Path


def test_workflow_has_required_triggers_permissions_secrets_and_safe_commit() -> None:
    workflow = Path(".github/workflows/update-spotify.yml").read_text(encoding="utf-8")

    required = [
        "name: Update Spotify activity",
        "workflow_dispatch:",
        'cron: "17 * * * *"',
        "contents: write",
        "group: update-spotify-readme",
        "cancel-in-progress: true",
        "actions/checkout@v6",
        "actions/setup-python@v6",
        'python-version: "3.12"',
        "SPOTIFY_CLIENT_ID: ${{ secrets.SPOTIFY_CLIENT_ID }}",
        "SPOTIFY_CLIENT_SECRET: ${{ secrets.SPOTIFY_CLIENT_SECRET }}",
        "SPOTIFY_REFRESH_TOKEN: ${{ secrets.SPOTIFY_REFRESH_TOKEN }}",
        "python -m scripts.spotify_readme.main --readme-path README.md",
        'git config user.name "github-actions[bot]"',
        'git add README.md',
        'git commit -m "chore: update Spotify activity"',
    ]
    for value in required:
        assert value in workflow

    assert "git add ." not in workflow
    assert "git add -A" not in workflow
