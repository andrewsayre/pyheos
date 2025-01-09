""" "Define the media module."""

from collections.abc import Sequence
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, Optional, cast

from pyheos import const
from pyheos.message import HeosMessage

if TYPE_CHECKING:
    from . import Heos


@dataclass
class QueueItem:
    """Define an item in the queue."""

    queue_id: int
    song: str
    album: str
    artist: str
    image_url: str
    media_id: str
    album_id: str

    @classmethod
    def from_data(cls, data: dict[str, str]) -> "QueueItem":
        """Create a new instance from the provided data."""
        return cls(
            queue_id=int(data[const.ATTR_QUEUE_ID]),
            song=data[const.ATTR_SONG],
            album=data[const.ATTR_ALBUM],
            artist=data[const.ATTR_ARTIST],
            image_url=data[const.ATTR_IMAGE_URL],
            media_id=data[const.ATTR_MEDIA_ID],
            album_id=data[const.ATTR_ALBUM_ID],
        )


@dataclass(init=False)
class Media:
    """
    Define a base media item.

    Do not instantiate directly. Use either MediaMusicSource or MediaItem.
    """

    source_id: int
    name: str
    type: const.MediaType
    image_url: str = field(repr=False)
    heos: Optional["Heos"] = field(repr=False, hash=False, compare=False)


@dataclass
class MediaMusicSource(Media):
    """
    Define a music source.

    A Music Source is a top-level music source, only returned from get_music_sources.
    """

    available: bool
    service_username: str | None

    @classmethod
    def from_data(
        cls,
        data: dict[str, Any],
        heos: Optional["Heos"] = None,
    ) -> "MediaMusicSource":
        """Create a new instance from the provided data."""
        return cls(
            source_id=int(data[const.ATTR_SOURCE_ID]),
            name=data[const.ATTR_NAME],
            type=const.MediaType(data[const.ATTR_TYPE]),
            image_url=data[const.ATTR_IMAGE_URL],
            available=data[const.ATTR_AVAILABLE] == const.VALUE_TRUE,
            service_username=data.get(const.ATTR_SERVICE_USER_NAME),
            heos=heos,
        )

    def _update_from_data(self, data: dict[str, Any]) -> None:
        """Update the instance with new data."""
        self.source_id = int(data[const.ATTR_SOURCE_ID])
        self.name = data[const.ATTR_NAME]
        self.type = const.MediaType(data[const.ATTR_TYPE])
        self.image_url = data[const.ATTR_IMAGE_URL]
        self.available = data[const.ATTR_AVAILABLE] == const.VALUE_TRUE
        self.service_username = data.get(const.ATTR_SERVICE_USER_NAME)

    def clone(self) -> "MediaMusicSource":
        """Create a new instance from the current instance."""
        return MediaMusicSource(
            source_id=self.source_id,
            name=self.name,
            type=self.type,
            image_url=self.image_url,
            available=self.available,
            service_username=self.service_username,
            heos=self.heos,
        )

    async def refresh(self) -> None:
        """Refresh the instance with the latest data."""
        assert self.heos, "Heos instance not set"
        await self.heos.get_music_source_info(music_source=self, refresh=True)

    async def browse(self) -> "BrowseResult":
        """Browse the contents of this source.

        Returns:
            A BrowseResult instance containing the items in this source."""
        assert self.heos, "Heos instance not set"
        return await self.heos.browse(self.source_id)


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
        heos: Optional["Heos"] = None,
    ) -> "MediaItem":
        """Create a new instance from the provided data."""

        # Ensure we have a source_id
        if const.ATTR_SOURCE_ID not in data and not source_id:
            raise ValueError("'source_id' is required when not present in 'data'")
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
            type=const.MediaType(data[const.ATTR_TYPE]),
            image_url=data[const.ATTR_IMAGE_URL],
            playable=data.get(const.ATTR_PLAYABLE) == const.VALUE_YES,
            media_id=data.get(const.ATTR_MEDIA_ID),
            artist=data.get(const.ATTR_ARTIST),
            album=data.get(const.ATTR_ALBUM),
            album_id=data.get(const.ATTR_ALBUM_ID),
            heos=heos,
        )

    def clone(self) -> "MediaItem":
        return MediaItem(
            source_id=self.source_id,
            name=self.name,
            type=self.type,
            image_url=self.image_url,
            playable=self.playable,
            browsable=self.browsable,
            container_id=self.container_id,
            media_id=self.media_id,
            artist=self.artist,
            album=self.album,
            album_id=self.album_id,
            heos=self.heos,
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
        assert self.heos, "Heos instance not set"
        return await self.heos.browse_media(self, range_start, range_end)

    async def play_media(
        self,
        player_id: int,
        add_criteria: const.AddCriteriaType = const.AddCriteriaType.PLAY_NOW,
    ) -> None:
        """Play this media item on the specified player.

        Args:
            player_id: The id of the player to play on.
        """
        assert self.heos, "Heos instance not set"
        await self.heos.play_media(player_id, self, add_criteria)


@dataclass
class BrowseResult:
    """Define the result of a browse operation."""

    count: int
    returned: int
    source_id: int
    items: Sequence[MediaItem] = field(repr=False, hash=False, compare=False)
    container_id: str | None = None
    heos: Optional["Heos"] = field(repr=False, hash=False, compare=False, default=None)

    @classmethod
    def from_data(
        cls, message: HeosMessage, heos: Optional["Heos"] = None
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
                    MediaItem.from_data(item, source_id, container_id, heos)
                    for item in cast(Sequence[dict], message.payload)
                ]
            ),
            heos=heos,
        )


@dataclass
class ImageMetadata:
    """Define metadata for an image."""

    image_url: str
    width: int

    @staticmethod
    def _from_data(data: dict[str, Any]) -> "ImageMetadata":
        """Create a new instance from the provided data."""
        return ImageMetadata(
            image_url=data[const.ATTR_IMAGE_URL],
            width=int(data[const.ATTR_WIDTH]),
        )


@dataclass
class AlbumMetadata:
    """Define metadata for an album."""

    album_id: str
    images: Sequence[ImageMetadata] = field(repr=False, hash=False, compare=False)

    @staticmethod
    def _from_data(data: dict[str, Any]) -> "AlbumMetadata":
        """Create a new instance from the provided data."""
        return AlbumMetadata(
            album_id=data[const.ATTR_ALBUM_ID],
            images=[
                ImageMetadata._from_data(cast(dict[str, Any], image))
                for image in data[const.ATTR_IMAGES]
            ],
        )


@dataclass
class RetreiveMetadataResult:
    "Define the result of a retrieve metadata operation."

    source_id: int
    container_id: str
    returned: int
    count: int
    metadata: Sequence[AlbumMetadata] = field(repr=False, hash=False, compare=False)

    @staticmethod
    def _from_message(message: HeosMessage) -> "RetreiveMetadataResult":
        "Create a new instance from the provided data."
        return RetreiveMetadataResult(
            source_id=message.get_message_value_int(const.ATTR_SOURCE_ID),
            container_id=message.get_message_value(const.ATTR_CONTAINER_ID),
            returned=message.get_message_value_int(const.ATTR_RETURNED),
            count=message.get_message_value_int(const.ATTR_COUNT),
            metadata=[
                AlbumMetadata._from_data(item)
                for item in cast(Sequence[dict[str, Any]], message.payload)
            ],
        )
