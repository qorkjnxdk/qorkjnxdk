import argparse
import os
import sys
from pathlib import Path

from .client import SpotifyClient
from .readme import update_readme_file
from .renderer import render_spotify_section

REQUIRED_ENVIRONMENT = (
    "SPOTIFY_CLIENT_ID",
    "SPOTIFY_CLIENT_SECRET",
    "SPOTIFY_REFRESH_TOKEN",
)


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Update Spotify activity in a profile README")
    parser.add_argument("--readme-path", type=Path, default=Path("README.md"))
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    missing = [name for name in REQUIRED_ENVIRONMENT if not os.environ.get(name)]
    if missing:
        print(f"Missing required environment variables: {', '.join(missing)}", file=sys.stderr)
        return 1

    try:
        client = SpotifyClient(
            os.environ["SPOTIFY_CLIENT_ID"],
            os.environ["SPOTIFY_CLIENT_SECRET"],
            os.environ["SPOTIFY_REFRESH_TOKEN"],
        )
        access_token = client.refresh_access_token()
        current_track = client.get_current_track(access_token)
        recent_tracks = [] if current_track is not None else client.get_recent_tracks(access_token)
        section = render_spotify_section(current_track, recent_tracks)
        changed = update_readme_file(args.readme_path, section)
    except (RuntimeError, OSError, ValueError) as error:
        print(f"Spotify README update failed: {error}", file=sys.stderr)
        return 1

    print("README updated" if changed else "README already up to date")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
