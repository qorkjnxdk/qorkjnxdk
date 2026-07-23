from dataclasses import dataclass


@dataclass(frozen=True)
class Track:
    name: str
    artists: tuple[str, ...]
    spotify_url: str
    album_image_url: str | None = None
