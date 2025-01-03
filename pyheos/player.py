"""Define the player module."""

import asyncio
from collections.abc import Sequence
from dataclasses import dataclass, field
from datetime import datetime
from typing import TYPE_CHECKING, Any, cast

from pyheos.media import MediaItem
from pyheos.message import HeosMessage

from . import const

if TYPE_CHECKING:
    from .heos import Heos


@dataclass
class HeosNowPlayingMedia:
    """Define now playing media information."""

    type: str | None = None
    song: str | None = None
    station: str | None = None
    album: str | None = None
    artist: str | None = None
    image_url: str | None = None
    album_id: str | None = None
    media_id: str | None = None
    queue_id: int | None = None
    source_id: int | None = None
    current_position: int | None = None
    current_position_updated: datetime | None = None
    duration: int | None = None
    supported_controls: Sequence[str] = field(
        default_factory=lambda: const.CONTROLS_ALL, init=False
    )

    def __post_init__(self, *args: Any, **kwargs: Any) -> None:
        """Pst initialize the now playing media."""
        self._update_supported_controls()

    def update_from_data(self, message: HeosMessage) -> None:
        """Update the current instance from another instance."""
        data = cast(dict[str, Any], message.payload)
        self.type = data.get(const.ATTR_TYPE)
        self.song = data.get(const.ATTR_SONG)
        self.station = data.get(const.ATTR_STATION)
        self.album = data.get(const.ATTR_ALBUM)
        self.artist = data.get(const.ATTR_ARTIST)
        self.image_url = data.get(const.ATTR_IMAGE_URL)
        self.album_id = data.get(const.ATTR_ALBUM_ID)
        self.media_id = data.get(const.ATTR_MEDIA_ID)
        self.queue_id = self.get_optional_int(data.get(const.ATTR_QUEUE_ID))
        self.source_id = self.get_optional_int(data.get(const.ATTR_SOURCE_ID))
        self._update_supported_controls()
        self.clear_progress()

    @classmethod
    def from_data(cls, message: HeosMessage) -> "HeosNowPlayingMedia":
        """Create a new instance from the provided data."""
        data = cast(dict[str, Any], message.payload)
        return cls(
            type=data.get(const.ATTR_TYPE),
            song=data.get(const.ATTR_SONG),
            station=data.get(const.ATTR_STATION),
            album=data.get(const.ATTR_ALBUM),
            artist=data.get(const.ATTR_ARTIST),
            image_url=data.get(const.ATTR_IMAGE_URL),
            album_id=data.get(const.ATTR_ALBUM_ID),
            media_id=data.get(const.ATTR_MEDIA_ID),
            queue_id=cls.get_optional_int(data.get(const.ATTR_QUEUE_ID)),
            source_id=cls.get_optional_int(data.get(const.ATTR_SOURCE_ID)),
        )

    @staticmethod
    def get_optional_int(value: Any) -> int | None:
        try:
            return int(str(value))
        except (TypeError, ValueError):
            return None

    def _update_supported_controls(self) -> None:
        """Updates the supported controls based on the source and type."""
        new_supported_controls = (
            const.CONTROLS_ALL if self.source_id is not None else []
        )
        if self.source_id is not None and self.type is not None:
            if controls := const.SOURCE_CONTROLS.get(self.source_id):
                new_supported_controls = controls.get(
                    const.MediaType(self.type), const.CONTROLS_ALL
                )
        self.supported_controls = new_supported_controls

    def event_update_progress(
        self, event: HeosMessage, all_progress_events: bool
    ) -> bool:
        """Update the position/duration from an event."""
        if all_progress_events or self.current_position is None:
            self.current_position = event.get_message_value_int(
                const.ATTR_CURRENT_POSITION
            )
            self.current_position_updated = datetime.now()
            self.duration = event.get_message_value_int(const.ATTR_DURATION)
            return True
        return False

    def clear_progress(self) -> None:
        """Clear the current position."""
        self.current_position = None
        self.current_position_updated = None
        self.duration = None


@dataclass
class PlayMode:
    """Define the play mode options for a player."""

    repeat: const.RepeatType
    shuffle: bool

    @classmethod
    def from_data(cls, data: HeosMessage) -> "PlayMode":
        """Create a new instance from the provided data."""
        return cls(
            repeat=const.RepeatType(data.get_message_value(const.ATTR_REPEAT)),
            shuffle=data.get_message_value(const.ATTR_SHUFFLE) == const.VALUE_ON,
        )


class HeosPlayer:
    """Define a HEOS player."""

    def __init__(self, heos: "Heos", data: dict[str, Any]) -> None:
        """Initialize a player with the data."""
        self._heos = heos

        self._name: str = str(data[const.ATTR_NAME])
        self._player_id: int = int(data[const.ATTR_PLAYER_ID])
        self._model: str = data[const.ATTR_MODEL]
        self._version: str = data[const.ATTR_VERSION]
        self._ip_address: str = data[const.ATTR_IP_ADDRESS]
        self._network: str = data[const.ATTR_NETWORK]
        self._line_out: int = data[const.ATTR_LINE_OUT]

        self._state: const.PlayState | None = None
        self._volume: int | None = None
        self._is_muted: bool | None = None
        self._repeat: const.RepeatType = const.RepeatType.OFF
        self._shuffle: bool = False
        self._playback_error: str | None = None
        self._now_playing_media: HeosNowPlayingMedia = HeosNowPlayingMedia()
        self._available: bool = True

    def __str__(self) -> str:
        """Get a user-readable representation of the player."""
        return f"{{{self._name} ({self._model})}}"

    def __repr__(self) -> str:
        """Get a debug representation of the player."""
        return f"{{{self.name} ({self._model}) with id {self._player_id} at {self._ip_address}}}"

    def set_available(self, available: bool) -> None:
        """Mark player removed after a change event."""
        self._available = available

    def from_data(self, data: dict[str, Any]) -> None:
        """Update the attributes from the supplied data."""
        self._name = str(data[const.ATTR_NAME])
        self._model = data[const.ATTR_MODEL]
        self._version = data[const.ATTR_VERSION]
        self._ip_address = data[const.ATTR_IP_ADDRESS]
        self._network = data[const.ATTR_NETWORK]
        self._line_out = data[const.ATTR_LINE_OUT]

    async def refresh(self) -> None:
        """Pull current state."""
        await asyncio.gather(
            self.refresh_state(),
            self.refresh_now_playing_media(),
            self.refresh_volume(),
            self.refresh_mute(),
            self.refresh_play_mode(),
        )

    async def refresh_state(self) -> None:
        """Refresh the now playing state."""
        self._state = await self.heos.player_get_play_state(self._player_id)

    async def refresh_now_playing_media(self) -> None:
        """Pull the latest now playing media."""
        await self.heos.get_now_playing_media(self._player_id, self._now_playing_media)

    async def refresh_volume(self) -> None:
        """Pull the latest volume."""
        self._volume = await self.heos.player_get_volume(self._player_id)

    async def refresh_mute(self) -> None:
        """Pull the latest mute status."""
        self._is_muted = await self.heos.player_get_mute(self._player_id)

    async def refresh_play_mode(self) -> None:
        """Pull the latest play mode."""
        play_mode = await self.heos.player_get_play_mode(self._player_id)
        self._repeat = play_mode.repeat
        self._shuffle = play_mode.shuffle

    async def set_state(self, state: const.PlayState) -> None:
        """Set the state of the player."""
        await self.heos.player_set_play_state(self._player_id, state)

    async def play(self) -> None:
        """Set the start to play."""
        await self.set_state(const.PlayState.PLAY)

    async def pause(self) -> None:
        """Set the start to pause."""
        await self.set_state(const.PlayState.PAUSE)

    async def stop(self) -> None:
        """Set the start to stop."""
        await self.set_state(const.PlayState.STOP)

    async def set_volume(self, level: int) -> None:
        """Set the volume level."""
        await self.heos.player_set_volume(self._player_id, level)

    async def set_mute(self, state: bool) -> None:
        """Set the mute state."""
        await self.heos.player_set_mute(self._player_id, state)

    async def mute(self) -> None:
        """Set mute state."""
        await self.set_mute(True)

    async def unmute(self) -> None:
        """Clear mute state."""
        await self.set_mute(False)

    async def volume_up(self, step: int = const.DEFAULT_STEP) -> None:
        """Raise the volume."""
        await self.heos.player_volume_up(self._player_id, step)

    async def volume_down(self, step: int = const.DEFAULT_STEP) -> None:
        """Raise the volume."""
        await self.heos.player_volume_down(self._player_id, step)

    async def toggle_mute(self) -> None:
        """Toggle mute state."""
        await self.heos.player_toggle_mute(self._player_id)

    async def set_play_mode(self, repeat: const.RepeatType, shuffle: bool) -> None:
        """Set the play mode of the player."""
        await self.heos.player_set_play_mode(self._player_id, repeat, shuffle)

    async def clear_queue(self) -> None:
        """Clear the queue of the player."""
        await self.heos.player_clear_queue(self._player_id)

    async def play_next(self) -> None:
        """Clear the queue of the player."""
        await self.heos.player_play_next(self._player_id)

    async def play_previous(self) -> None:
        """Clear the queue of the player."""
        await self.heos.player_play_previous(self._player_id)

    async def play_input_source(
        self, input_name: str, source_player_id: int | None = None
    ) -> None:
        """Play the specified input."""
        await self.heos.play_input_source(self.player_id, input_name, source_player_id)

    async def play_preset_station(self, index: int) -> None:
        """Play the favorite by 1-based index."""
        await self.heos.play_preset_station(self.player_id, index)

    async def play_url(self, url: str) -> None:
        """Play the specified URL."""
        await self.heos.play_url(self.player_id, url)

    async def play_quick_select(self, quick_select_id: int) -> None:
        """Play the specified quick select."""
        await self.heos.player_play_quick_select(self._player_id, quick_select_id)

    async def add_to_queue(
        self,
        source_id: int,
        container_id: str,
        media_id: str | None = None,
        add_criteria: const.AddCriteriaType = const.AddCriteriaType.PLAY_NOW,
    ) -> None:
        """Add the specified source to the queue."""
        await self.heos.add_to_queue(
            self.player_id, source_id, container_id, media_id, add_criteria
        )

    async def play_media(
        self,
        media: MediaItem,
        add_criteria: const.AddCriteriaType = const.AddCriteriaType.PLAY_NOW,
    ) -> None:
        """Play the specified media.

        Args:
            media: The media item to play.
            add_criteria: Determines how containers or tracks are added to the queue. The default is AddCriteriaType.PLAY_NOW.
        """
        await self.heos.play_media(self.player_id, media, add_criteria)

    async def set_quick_select(self, quick_select_id: int) -> None:
        """Set the specified quick select to the current source."""
        await self.heos.player_set_quick_select(self._player_id, quick_select_id)

    async def get_quick_selects(self) -> dict[int, str]:
        """Get a list of quick selects."""
        return await self.heos.get_player_quick_selects(self._player_id)

    async def event_update(self, event: HeosMessage, all_progress_events: bool) -> bool:
        """Return True if player update event changed state."""
        if event.command == const.EVENT_PLAYER_NOW_PLAYING_PROGRESS:
            return self._now_playing_media.event_update_progress(
                event, all_progress_events
            )
        if event.command == const.EVENT_PLAYER_STATE_CHANGED:
            self._state = const.PlayState(event.get_message_value(const.ATTR_STATE))
            if self._state == const.PlayState.PLAY:
                self._now_playing_media.clear_progress()
        elif event.command == const.EVENT_PLAYER_NOW_PLAYING_CHANGED:
            await self.refresh_now_playing_media()
        elif event.command == const.EVENT_PLAYER_VOLUME_CHANGED:
            self._volume = event.get_message_value_int(const.ATTR_LEVEL)
            self._is_muted = event.get_message_value(const.ATTR_MUTE) == const.VALUE_ON
        elif event.command == const.EVENT_REPEAT_MODE_CHANGED:
            self._repeat = const.RepeatType(event.get_message_value(const.ATTR_REPEAT))
        elif event.command == const.EVENT_SHUFFLE_MODE_CHANGED:
            self._shuffle = (
                event.get_message_value(const.ATTR_SHUFFLE) == const.VALUE_ON
            )
        elif event.command == const.EVENT_PLAYER_PLAYBACK_ERROR:
            self._playback_error = event.get_message_value(const.ATTR_ERROR)
        return True

    @property
    def name(self) -> str:
        """Get the name of the device."""
        return self._name

    @property
    def player_id(self) -> int:
        """Get the unique id of the player."""
        return self._player_id

    @property
    def model(self) -> str:
        """Get the model of the device."""
        return self._model

    @property
    def version(self) -> str:
        """Get the version of the device."""
        return self._version

    @property
    def ip_address(self) -> str:
        """Get the IP Address of the device."""
        return self._ip_address

    @property
    def network(self) -> str:
        """Get the network connection type."""
        return self._network

    @property
    def line_out(self) -> int | None:
        """Get the line out configuration."""
        return self._line_out

    @property
    def state(self) -> str | None:
        """Get the state of the player."""
        return self._state

    @property
    def now_playing_media(self) -> HeosNowPlayingMedia:
        """Get the now playing media information."""
        return self._now_playing_media

    @property
    def volume(self) -> int | None:
        """Get the volume of the player."""
        return self._volume

    @property
    def is_muted(self) -> bool | None:
        """Get whether the device is muted or not."""
        return self._is_muted

    @property
    def repeat(self) -> const.RepeatType:
        """Get the repeat mode."""
        return self._repeat

    @property
    def shuffle(self) -> bool:
        """Get if shuffle is active."""
        return self._shuffle

    @property
    def available(self) -> bool:
        """Return True if this player is available."""
        return self._available and self._heos.connection_state == const.STATE_CONNECTED

    @property
    def playback_error(self) -> str | None:
        """Get the last playback error."""
        return self._playback_error

    @property
    def heos(self) -> "Heos":
        """Get the heos instance attached to this player."""
        return self._heos
