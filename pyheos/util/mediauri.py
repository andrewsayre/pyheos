"""Defines utilities for serializing MediaItem and MediaMusicSource instances to/from URI strings."""

import json
from typing import Any
from urllib.parse import parse_qsl, urlencode, urlparse

from pyheos.media import MediaItem, MediaMusicSource
from pyheos.types import MediaType

BASE_URI = "heos://media"


def is_media_uri(uri: str) -> bool:
    """Check if the provided URI is a valid HEOS media URI.

    Args:
        uri: The URI string to check.
    Returns:
        True if the URI is a valid HEOS media URI, False otherwise.
    """
    return uri.startswith(BASE_URI)


def to_media_uri(media: MediaItem | MediaMusicSource, extra: Any | None = None) -> str:
    """Get URI string that can uniquely identify the media item.

    Args:
        media: The item to get the URI for.
        extra: Additional fields to serialize and include in the URI.
    Returns:
        A URI string that uniquely identifies this media item in the format:
        heos://media/<souce_id>/<type>?fields=values

    """
    base_uri = f"{BASE_URI}/{media.source_id}/{media.type}"
    params: dict[str, Any] = {
        "name": media.name,
        "image_url": media.image_url,
    }
    if isinstance(media, MediaItem):
        params["playable"] = media.playable
        params["browsable"] = media.browsable
        if media.container_id:
            params["container_id"] = media.container_id
        if media.media_id:
            params["media_id"] = media.media_id
        if media.artist:
            params["artist"] = media.artist
        if media.album:
            params["album"] = media.album
        if media.album_id:
            params["album_id"] = media.album_id
    else:
        params["available"] = media.available
        if media.service_username:
            params["service_username"] = media.service_username
    if extra:
        params["extra"] = json.dumps(extra)

    return f"{base_uri}?{urlencode(params)}"


def from_media_uri(
    uri: str,
) -> tuple[MediaItem | MediaMusicSource, Any]:
    """Create a new instance from the provided URI.

    Args:
        uri: The URI string to parse.
    Returns:
        A new MediaMusicSource instance representing the URI string.
    Raises:
        ValueError: If the URI is not a valid HEOS media URI
    """
    if not is_media_uri(uri):
        raise ValueError("uri is not a HEOS media URI")
    parse_result = urlparse(uri)
    path = parse_result.path.removeprefix("/").split("/", 2)
    query = dict(
        parse_qsl(parse_result.query, keep_blank_values=True, strict_parsing=True)
    )
    extra: Any | None = None
    if "extra" in query:
        extra = json.loads(query["extra"])
    if "playable" in query:
        return MediaItem(
            source_id=int(path[0]),
            type=MediaType(path[1]),
            name=query["name"],
            image_url=query["image_url"],
            playable=query["playable"] == "True",
            browsable=query["browsable"] == "True",
            container_id=query.get("container_id"),
            media_id=query.get("media_id"),
            artist=query.get("artist"),
            album=query.get("album"),
            album_id=query.get("album_id"),
            heos=None,
        ), extra
    else:
        return MediaMusicSource(
            source_id=int(path[0]),
            type=MediaType(path[1]),
            name=query["name"],
            image_url=query["image_url"],
            available=query["available"] == "True",
            service_username=query.get("service_username"),
            heos=None,
        ), extra
