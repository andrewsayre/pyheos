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


@dataclass
class Media:
    """Define a base media item."""

    name: str
    type: MediaType
    image_url: str

    source_id: int
    _commands: HeosCommands | None = field(repr=False, hash=False, compare=False)

    @staticmethod
    def from_data(
        data: dict[str, Any],
        commands: HeosCommands | None = None,
        source_id: int = 0,
    ) -> "Media":
        """Create a new instance from the provided data."""

        type = MediaType(data[const.ATTR_TYPE])
        match type:
            case MediaType.ALBUM:
                return MediaAlbum.from_data(data, commands, source_id)
            case MediaType.ARTIST:
                return MediaContainer.from_data(data, commands, source_id)
            case MediaType.CONTAINER:
                return MediaContainer.from_data(data, commands, source_id)
            case MediaType.DLNA_SERVER:
                raise NotImplementedError()
            case MediaType.GENRE:
                return MediaContainer.from_data(data, commands, source_id)
            case MediaType.HEOS_SERVER:
                return MediaSource.from_data(data, commands, source_id)
            case MediaType.HEOS_SERVICE:
                return MediaSource.from_data(data, commands, source_id)
            case MediaType.MUSIC_SERVICE:
                raise NotImplementedError()
            case MediaType.PLAYLIST:
                return MediaContainer.from_data(data, commands, source_id)
            case MediaType.SONG:
                return MediaSong.from_data(data, commands, source_id)
            case MediaType.STATION:
                return MediaItem.from_data(data, commands, source_id)


@dataclass
class MediaPlayable(Media):
    """Define a playable media item."""

    playable: bool


@dataclass
class MediaContainer(MediaPlayable):
    """Define a media container."""

    container_id: str

    @classmethod
    def from_data(
        cls,
        data: dict[str, Any],
        commands: HeosCommands | None = None,
        source_id: int = 0,
    ) -> "MediaContainer":
        """Create a new instance from the provided data."""
        return MediaContainer(
            name=data[const.ATTR_NAME],
            type=MediaType(data[const.ATTR_TYPE]),
            image_url=data[const.ATTR_IMAGE_URL],
            playable=data[const.ATTR_PLAYABLE] == const.VALUE_YES,
            container_id=data[const.ATTR_CONTAINER_ID],
            _commands=commands,
            source_id=source_id,
        )

    async def browse(
        self,
        range_start: int | None = None,
        range_end: int | None = None,
    ) -> "BrowseResult":
        """Browse the contents of the current source."""
        assert self._commands is not None
        message = await self._commands.browse(
            self.source_id, self.container_id, range_start, range_end
        )
        return BrowseResult.from_data(message, self._commands)


@dataclass
class MediaAlbum(MediaContainer):
    artist: str

    @classmethod
    def from_data(
        cls,
        data: dict[str, Any],
        commands: HeosCommands | None = None,
        source_id: int = 0,
    ) -> "MediaAlbum":
        """Create a new instance from the provided data."""
        return cls(
            name=data[const.ATTR_NAME],
            type=MediaType(data[const.ATTR_TYPE]),
            image_url=data[const.ATTR_IMAGE_URL],
            playable=data[const.ATTR_PLAYABLE] == const.VALUE_YES,
            container_id=data[const.ATTR_CONTAINER_ID],
            artist=data[const.ATTR_ARTIST],
            source_id=source_id,
            _commands=commands,
        )


@dataclass
class MediaSource(Media):
    """Define a media source."""

    @classmethod
    def from_data(
        cls,
        data: dict[str, Any],
        commands: HeosCommands | None = None,
        source_id: int = 0,
    ) -> "MediaSource":
        """Create a new instance from the provided data."""
        return cls(
            name=data[const.ATTR_NAME],
            type=MediaType(data[const.ATTR_TYPE]),
            image_url=data[const.ATTR_IMAGE_URL],
            source_id=int(data[const.ATTR_SOURCE_ID]),
            _commands=commands,
        )

    async def browse(self) -> "BrowseResult":
        """Browse the contents of the current source."""
        assert self._commands is not None
        message = await self._commands.browse(self.source_id)
        return BrowseResult.from_data(message, self._commands)


@dataclass
class MediaMusicSource(MediaSource):
    """Define a music source."""

    available: bool
    service_username: str | None

    @classmethod
    def from_data(
        cls,
        data: dict[str, Any],
        commands: HeosCommands | None = None,
        source_id: int = 0,
    ) -> "MediaMusicSource":
        """Create a new instance from the provided data."""
        return cls(
            name=data[const.ATTR_NAME],
            type=MediaType(data[const.ATTR_TYPE]),
            image_url=data[const.ATTR_IMAGE_URL],
            source_id=int(data[const.ATTR_SOURCE_ID]),
            available=data[const.ATTR_AVAILABLE] == const.VALUE_TRUE,
            service_username=data.get(const.ATTR_SERVICE_USER_NAME),
            _commands=commands,
        )


@dataclass
class MediaItem(MediaPlayable):
    """Define a playable media item."""

    media_id: str

    @classmethod
    def from_data(
        cls,
        data: dict[str, Any],
        commands: HeosCommands | None = None,
        source_id: int = 0,
    ) -> "MediaItem":
        """Create a new instance from the provided data."""
        return cls(
            name=data[const.ATTR_NAME],
            type=MediaType(data[const.ATTR_TYPE]),
            image_url=data[const.ATTR_IMAGE_URL],
            playable=data[const.ATTR_PLAYABLE] == const.VALUE_YES,
            media_id=data[const.ATTR_MEDIA_ID],
            source_id=source_id,
            _commands=commands,
        )


@dataclass
class MediaSong(MediaItem):
    """Define a song media item."""

    artist: str
    album: str
    album_id: str

    @classmethod
    def from_data(
        cls,
        data: dict[str, Any],
        commands: HeosCommands | None = None,
        source_id: int = 0,
    ) -> "MediaSong":
        """Create a new instance from the provided data."""
        return cls(
            name=data[const.ATTR_NAME],
            type=MediaType(data[const.ATTR_TYPE]),
            image_url=data[const.ATTR_IMAGE_URL],
            playable=data[const.ATTR_PLAYABLE] == const.VALUE_YES,
            media_id=data[const.ATTR_MEDIA_ID],
            artist=data[const.ATTR_ARTIST],
            album=data[const.ATTR_ALBUM],
            album_id=data[const.ATTR_ALBUM_ID],
            source_id=source_id,
            _commands=commands,
        )


@dataclass
class BrowseResult:
    """Define the result of a browse operation."""

    count: int
    returned: int
    source_id: int
    items: Sequence[Media]

    @classmethod
    def from_data(
        cls, message: HeosMessage, commands: HeosCommands | None = None
    ) -> "BrowseResult":
        """Create a new instance from the provided data."""
        source_id = message.get_message_value_int(const.ATTR_SOURCE_ID)
        return cls(
            count=message.get_message_value_int(const.ATTR_COUNT),
            returned=message.get_message_value_int(const.ATTR_RETURNED),
            source_id=source_id,
            items=list(
                [
                    Media.from_data(item, commands, source_id)
                    for item in cast(Sequence[dict], message.payload)
                ]
            ),
        )
