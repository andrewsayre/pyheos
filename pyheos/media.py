""" "Define the media module."""

from collections.abc import Sequence
from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any, cast

from pyheos import const
from pyheos.command import HeosCommands
from pyheos.message import HeosMessage


class MediaType(StrEnum):
    """Define the media types."""

    ALBUM = "album"
    ARTIST = "artist"
    CONTAINER = "container"
    DLNA_SERVER = "dlna_server"
    GENRE = "genre"
    HEOS_SERVER = "heos_server"
    HEOS_SERVICE = "heos_service"
    MUSIC_SERVICE = "music_service"
    PLAYLIST = "playlist"
    SONG = "song"
    STATION = "station"


@dataclass(init=False)
class Media:
    """
    Define a base media item.

    Do not instantiate directly. Use either MediaMusicSource or MediaItem.
    """

    source_id: int
    name: str
    type: MediaType
    image_url: str
    _commands: HeosCommands | None = field(repr=False, hash=False, compare=False)


@dataclass
class MediaMusicSource(Media):
    """
    Define a music source.

    A Music Source is a top-level music source, different than other media items returned from browse commands.
    """

    available: bool
    service_username: str | None

    @classmethod
    def from_data(
        cls,
        data: dict[str, Any],
        commands: HeosCommands | None = None,
    ) -> "MediaMusicSource":
        """Create a new instance from the provided data."""
        return cls(
            source_id=int(data[const.ATTR_SOURCE_ID]),
            name=data[const.ATTR_NAME],
            type=MediaType(data[const.ATTR_TYPE]),
            image_url=data[const.ATTR_IMAGE_URL],
            available=data[const.ATTR_AVAILABLE] == const.VALUE_TRUE,
            service_username=data.get(const.ATTR_SERVICE_USER_NAME),
            _commands=commands,
        )

    async def browse(self) -> "BrowseResult":
        """Browse the contents of this source.

        Returns:
            A BrowseResult instance containing the items in this source."""
        if self._commands is None:
            raise ValueError(
                "Class must be initialized with the commands parameter to browse"
            )
        message = await self._commands.browse(self.source_id)
        return BrowseResult.from_data(message, self._commands)


@dataclass
class MediaItem(Media):
    """Define a playable media item."""

    playable: bool
    browsable: bool
    container_id: str | None = None
    media_id: str | None = None
    artist: str | None = None
    album: str | None = None
    album_id: str | None = None

    @classmethod
    def from_data(
        cls,
        data: dict[str, Any],
        source_id: int | None = None,
        container_id: str | None = None,
        commands: HeosCommands | None = None,
    ) -> "MediaItem":
        """Create a new instance from the provided data."""

        # Ensure we have a source_id
        if const.ATTR_SOURCE_ID not in data and not source_id:
            raise ValueError("source_id is required when not present in the data")
        new_source_id = int(data.get(const.ATTR_SOURCE_ID, source_id))
        # Items is browsable if is a media source, or if it is a container
        new_browseable = (
            const.ATTR_SOURCE_ID in data
            or data.get(const.ATTR_CONTAINER) == const.VALUE_YES
        )

        return cls(
            source_id=new_source_id,
            container_id=data.get(const.ATTR_CONTAINER_ID, container_id),
            browsable=new_browseable,
            name=data[const.ATTR_NAME],
            type=MediaType(data[const.ATTR_TYPE]),
            image_url=data[const.ATTR_IMAGE_URL],
            playable=data.get(const.ATTR_PLAYABLE) == const.VALUE_YES,
            media_id=data.get(const.ATTR_MEDIA_ID),
            artist=data.get(const.ATTR_ARTIST),
            album=data.get(const.ATTR_ALBUM),
            album_id=data.get(const.ATTR_ALBUM_ID),
            _commands=commands,
        )

    async def browse(
        self,
        range_start: int | None = None,
        range_end: int | None = None,
    ) -> "BrowseResult":
        """Browse the contents of the current media item (source or container).

        Args:
            range_start: The index of the first item to return. Both range_start and range_end must be provided to return a range of items.
            range_end: The index of the last item to return. Both range_start and range_end must be provided to return a range of items.
        Returns:
            A BrowseResult instance containing the items in this media item (source or container)."""
        if self._commands is None:
            raise ValueError(
                "Class must be initialized with the commands parameter to browse"
            )
        if not self.browsable:
            raise ValueError("Only media sources and containers can be browsed")

        message = await self._commands.browse(
            self.source_id, self.container_id, range_start, range_end
        )
        return BrowseResult.from_data(message, self._commands)


@dataclass
class BrowseResult:
    """Define the result of a browse operation."""

    count: int
    returned: int
    source_id: int
    items: Sequence[MediaItem] = field(repr=False, hash=False, compare=False)
    container_id: str | None = None

    @classmethod
    def from_data(
        cls, message: HeosMessage, commands: HeosCommands | None = None
    ) -> "BrowseResult":
        """Create a new instance from the provided data."""
        source_id = message.get_message_value_int(const.ATTR_SOURCE_ID)
        container_id = message.message.get(const.ATTR_CONTAINER_ID)

        return cls(
            count=message.get_message_value_int(const.ATTR_COUNT),
            returned=message.get_message_value_int(const.ATTR_RETURNED),
            source_id=source_id,
            container_id=container_id,
            items=list(
                [
                    MediaItem.from_data(item, source_id, container_id, commands)
                    for item in cast(Sequence[dict], message.payload)
                ]
            ),
        )
