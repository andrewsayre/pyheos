"""Define the player module."""

import asyncio
from collections.abc import Sequence
from dataclasses import dataclass, field
from datetime import datetime
from typing import TYPE_CHECKING, Any, Optional, cast

from pyheos.dispatch import DisconnectType, EventCallbackType, callback_wrapper
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

    def update_from_message(self, message: HeosMessage) -> None:
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

    def on_event(self, event: HeosMessage, all_progress_events: bool) -> bool:
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


@dataclass
class HeosPlayer:
    """Define a HEOS player."""

    name: str = field(repr=True, hash=False, compare=False)
    player_id: int = field(repr=True, hash=True, compare=True)
    model: str = field(repr=True, hash=False, compare=False)
    serial: str | None = field(repr=False, hash=False, compare=False)
    version: str = field(repr=True, hash=False, compare=False)
    ip_address: str = field(repr=True, hash=False, compare=False)
    network: str = field(repr=False, hash=False, compare=False)
    line_out: int = field(repr=False, hash=False, compare=False)
    state: const.PlayState | None = field(
        repr=True, hash=False, compare=False, default=None
    )
    volume: int = field(repr=False, hash=False, compare=False, default=0)
    is_muted: bool = field(repr=False, hash=False, compare=False, default=False)
    repeat: const.RepeatType = field(
        repr=False, hash=False, compare=False, default=const.RepeatType.OFF
    )
    shuffle: bool = field(repr=False, hash=False, compare=False, default=False)
    playback_error: str | None = field(
        repr=False, hash=False, compare=False, default=None
    )
    now_playing_media: HeosNowPlayingMedia = field(default_factory=HeosNowPlayingMedia)
    available: bool = field(repr=False, hash=False, compare=False, default=True)
    heos: Optional["Heos"] = field(repr=False, hash=False, compare=False, default=None)

    @classmethod
    def from_data(
        cls,
        data: dict[str, Any],
        heos: Optional["Heos"] = None,
    ) -> "HeosPlayer":
        """Create a new instance from the provided data."""
        return cls(
            name=data[const.ATTR_NAME],
            player_id=int(data[const.ATTR_PLAYER_ID]),
            model=data[const.ATTR_MODEL],
            serial=data.get(const.ATTR_SERIAL),
            version=data[const.ATTR_VERSION],
            ip_address=data[const.ATTR_IP_ADDRESS],
            network=data[const.ATTR_NETWORK],
            line_out=int(data[const.ATTR_LINE_OUT]),
            heos=heos,
        )

    def update_from_data(self, data: dict[str, Any]) -> None:
        """Update the attributes from the supplied data."""
        self.name = data[const.ATTR_NAME]
        self.player_id = int(data[const.ATTR_PLAYER_ID])
        self.model = data[const.ATTR_MODEL]
        self.serial = data.get(const.ATTR_SERIAL)
        self.version = data[const.ATTR_VERSION]
        self.ip_address = data[const.ATTR_IP_ADDRESS]
        self.network = data[const.ATTR_NETWORK]
        self.line_out = int(data[const.ATTR_LINE_OUT])

    async def on_event(self, event: HeosMessage, all_progress_events: bool) -> bool:
        """Updates the player based on the received HEOS event.

        This is an internal method invoked by the Heos class and is not intended for direct use.

        Returns:
            True if the player event changed state, other wise False."""
        if event.command == const.EVENT_PLAYER_NOW_PLAYING_PROGRESS:
            return self.now_playing_media.on_event(event, all_progress_events)
        if event.command == const.EVENT_PLAYER_STATE_CHANGED:
            self.state = const.PlayState(event.get_message_value(const.ATTR_STATE))
            if self.state == const.PlayState.PLAY:
                self.now_playing_media.clear_progress()
        elif event.command == const.EVENT_PLAYER_NOW_PLAYING_CHANGED:
            await self.refresh_now_playing_media()
        elif event.command == const.EVENT_PLAYER_VOLUME_CHANGED:
            self.volume = event.get_message_value_int(const.ATTR_LEVEL)
            self.is_muted = event.get_message_value(const.ATTR_MUTE) == const.VALUE_ON
        elif event.command == const.EVENT_REPEAT_MODE_CHANGED:
            self.repeat = const.RepeatType(event.get_message_value(const.ATTR_REPEAT))
        elif event.command == const.EVENT_SHUFFLE_MODE_CHANGED:
            self.shuffle = event.get_message_value(const.ATTR_SHUFFLE) == const.VALUE_ON
        elif event.command == const.EVENT_PLAYER_PLAYBACK_ERROR:
            self.playback_error = event.get_message_value(const.ATTR_ERROR)
        return True

    def add_on_player_event(self, callback: EventCallbackType) -> DisconnectType:
        """Connect a callback to be invoked when connected.

        Args:
            callback: The callback to be invoked.
        Returns:
            A function that disconnects the callback."""
        assert self.heos, "Heos instance not set"
        # Use lambda to yield player_id since the value can change
        return self.heos.dispatcher.connect(
            const.SIGNAL_PLAYER_EVENT,
            callback_wrapper(callback, {0: lambda: self.player_id}),
        )

    async def refresh(self) -> None:
        """Pull current state."""
        assert self.heos, "Heos instance not set"
        await asyncio.gather(
            self.refresh_state(),
            self.refresh_now_playing_media(),
            self.refresh_volume(),
            self.refresh_mute(),
            self.refresh_play_mode(),
        )

    async def refresh_state(self) -> None:
        """Refresh the now playing state."""
        assert self.heos, "Heos instance not set"
        self.state = await self.heos.player_get_play_state(self.player_id)

    async def refresh_now_playing_media(self) -> None:
        """Pull the latest now playing media."""
        assert self.heos, "Heos instance not set"
        await self.heos.get_now_playing_media(self.player_id, self.now_playing_media)

    async def refresh_volume(self) -> None:
        """Pull the latest volume."""
        assert self.heos, "Heos instance not set"
        self.volume = await self.heos.player_get_volume(self.player_id)

    async def refresh_mute(self) -> None:
        """Pull the latest mute status."""
        assert self.heos, "Heos instance not set"
        self.is_muted = await self.heos.player_get_mute(self.player_id)

    async def refresh_play_mode(self) -> None:
        """Pull the latest play mode."""
        assert self.heos, "Heos instance not set"
        play_mode = await self.heos.player_get_play_mode(self.player_id)
        self.repeat = play_mode.repeat
        self.shuffle = play_mode.shuffle

    async def set_state(self, state: const.PlayState) -> None:
        """Set the state of the player."""
        assert self.heos, "Heos instance not set"
        await self.heos.player_set_play_state(self.player_id, state)

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
        assert self.heos, "Heos instance not set"
        await self.heos.player_set_volume(self.player_id, level)

    async def set_mute(self, state: bool) -> None:
        """Set the mute state."""
        assert self.heos, "Heos instance not set"
        await self.heos.player_set_mute(self.player_id, state)

    async def mute(self) -> None:
        """Set mute state."""
        await self.set_mute(True)

    async def unmute(self) -> None:
        """Clear mute state."""
        await self.set_mute(False)

    async def volume_up(self, step: int = const.DEFAULT_STEP) -> None:
        """Raise the volume."""
        assert self.heos, "Heos instance not set"
        await self.heos.player_volume_up(self.player_id, step)

    async def volume_down(self, step: int = const.DEFAULT_STEP) -> None:
        """Raise the volume."""
        assert self.heos, "Heos instance not set"
        await self.heos.player_volume_down(self.player_id, step)

    async def toggle_mute(self) -> None:
        """Toggle mute state."""
        assert self.heos, "Heos instance not set"
        await self.heos.player_toggle_mute(self.player_id)

    async def set_play_mode(self, repeat: const.RepeatType, shuffle: bool) -> None:
        """Set the play mode of the player."""
        assert self.heos, "Heos instance not set"
        await self.heos.player_set_play_mode(self.player_id, repeat, shuffle)

    async def clear_queue(self) -> None:
        """Clear the queue of the player."""
        assert self.heos, "Heos instance not set"
        await self.heos.player_clear_queue(self.player_id)

    async def play_next(self) -> None:
        """Clear the queue of the player."""
        assert self.heos, "Heos instance not set"
        await self.heos.player_play_next(self.player_id)

    async def play_previous(self) -> None:
        """Clear the queue of the player."""
        assert self.heos, "Heos instance not set"
        await self.heos.player_play_previous(self.player_id)

    async def play_input_source(
        self, input_name: str, source_player_id: int | None = None
    ) -> None:
        """Play the specified input."""
        assert self.heos, "Heos instance not set"
        await self.heos.play_input_source(self.player_id, input_name, source_player_id)

    async def play_preset_station(self, index: int) -> None:
        """Play the favorite by 1-based index."""
        assert self.heos, "Heos instance not set"
        await self.heos.play_preset_station(self.player_id, index)

    async def play_url(self, url: str) -> None:
        """Play the specified URL."""
        assert self.heos, "Heos instance not set"
        await self.heos.play_url(self.player_id, url)

    async def play_quick_select(self, quick_select_id: int) -> None:
        """Play the specified quick select."""
        assert self.heos, "Heos instance not set"
        await self.heos.player_play_quick_select(self.player_id, quick_select_id)

    async def add_to_queue(
        self,
        source_id: int,
        container_id: str,
        media_id: str | None = None,
        add_criteria: const.AddCriteriaType = const.AddCriteriaType.PLAY_NOW,
    ) -> None:
        """Add the specified source to the queue."""
        assert self.heos, "Heos instance not set"
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
        assert self.heos, "Heos instance not set"
        await self.heos.play_media(self.player_id, media, add_criteria)

    async def set_quick_select(self, quick_select_id: int) -> None:
        """Set the specified quick select to the current source."""
        assert self.heos, "Heos instance not set"
        await self.heos.player_set_quick_select(self.player_id, quick_select_id)

    async def get_quick_selects(self) -> dict[int, str]:
        """Get a list of quick selects."""
        assert self.heos, "Heos instance not set"
        return await self.heos.get_player_quick_selects(self.player_id)
