""" "Define the media module."""

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any

from pyheos import const
from pyheos.command import HeosCommands


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
    type: str
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
    ) -> list[Media]:
        """Browse the contents of the current source."""
        assert self._commands is not None
        items = await self._commands.browse(
            self.source_id, self.container_id, range_start, range_end
        )
        return [Media.from_data(item, self._commands, self.source_id) for item in items]


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

    async def browse(self) -> list[Media]:
        """Browse the contents of the current source."""
        assert self._commands is not None
        items = await self._commands.browse(self.source_id)
        return [Media.from_data(item, self._commands, self.source_id) for item in items]


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
