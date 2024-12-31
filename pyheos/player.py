"""Define the player module."""

import asyncio
from collections.abc import Sequence
from datetime import datetime
from typing import TYPE_CHECKING, Any

from pyheos.media import MediaItem
from pyheos.message import HeosMessage

from . import const

if TYPE_CHECKING:
    from .heos import Heos


class HeosNowPlayingMedia:
    """Define now playing media information."""

    def __init__(self) -> None:
        """Init NowPlayingMedia info."""
        self._type: str | None = None
        self._song: str | None = None
        self._station: str | None = None
        self._album: str | None = None
        self._artist: str | None = None
        self._image_url: str | None = None
        self._album_id: str | None = None
        self._media_id: str | None = None
        self._queue_id: int | None = None
        self._source_id: int | None = None
        self._current_position: int | None = None
        self._current_position_updated: datetime | None = None
        self._duration: int | None = None
        self._supported_controls: Sequence[str] = const.CONTROLS_ALL

    def from_data(self, data: dict) -> None:
        """Update the attributes from the supplied data."""
        self._type = data.get(const.ATTR_TYPE)
        self._song = data.get(const.ATTR_SONG)
        self._station = data.get(const.ATTR_STATION)
        self._album = data.get(const.ATTR_ALBUM)
        self._artist = data.get(const.ATTR_ARTIST)
        self._image_url = data.get(const.ATTR_IMAGE_URL)
        self._album_id = data.get(const.ATTR_ALBUM_ID)
        self._media_id = data.get(const.ATTR_MEDIA_ID)
        try:
            self._queue_id = int(str(data.get(const.ATTR_QUEUE_ID)))
        except (TypeError, ValueError):
            self._queue_id = None
        try:
            self._source_id = int(str(data.get(const.ATTR_SOURCE_ID)))
        except (TypeError, ValueError):
            self._source_id = None

        supported_controls = const.CONTROLS_ALL if self._source_id is not None else []
        if self._source_id is not None and self._type is not None:
            if controls := const.SOURCE_CONTROLS.get(self._source_id):
                supported_controls = controls.get(self._type, const.CONTROLS_ALL)
        self._supported_controls = supported_controls

        self.clear_progress()

    def event_update_progress(
        self, event: HeosMessage, all_progress_events: bool
    ) -> bool:
        """Update the position/duration from an event."""
        if all_progress_events or self._current_position is None:
            self._current_position = event.get_message_value_int(
                const.ATTR_CURRENT_POSITION
            )
            self._current_position_updated = datetime.now()
            self._duration = event.get_message_value_int(const.ATTR_DURATION)
            return True
        return False

    def clear_progress(self) -> None:
        """Clear the current position."""
        self._current_position = None
        self._current_position_updated = None
        self._duration = None

    @property
    def type(self) -> str | None:
        """Get the type of the media playing."""
        return self._type

    @property
    def song(self) -> str | None:
        """Get the song playing."""
        return self._song

    @property
    def station(self) -> str | None:
        """Get the station playing."""
        return self._station

    @property
    def album(self) -> str | None:
        """Get the album playing."""
        return self._album

    @property
    def artist(self) -> str | None:
        """Get the artist playing."""
        return self._artist

    @property
    def image_url(self) -> str | None:
        """Get the image url of the media playing."""
        return self._image_url

    @property
    def album_id(self) -> str | None:
        """Get the id of the playing album."""
        return self._album_id

    @property
    def media_id(self) -> str | None:
        """Get the media id of the playing media."""
        return self._media_id

    @property
    def queue_id(self) -> int | None:
        """Get the queue id of the playing media."""
        return self._queue_id

    @property
    def source_id(self) -> int | None:
        """Get the source id of the playing media."""
        return self._source_id

    @property
    def current_position(self) -> int | None:
        """Get the current position within the playing media."""
        return self._current_position

    @property
    def current_position_updated(self) -> datetime | None:
        """Get the datetime the position was last updated."""
        return self._current_position_updated

    @property
    def duration(self) -> int | None:
        """Get the duration of the current playing media."""
        return self._duration

    @property
    def supported_controls(self) -> Sequence[str]:
        """Get the supported controls given the source."""
        return self._supported_controls


class HeosPlayer:
    """Define a HEOS player."""

    def __init__(self, heos: "Heos", data: dict[str, Any]) -> None:
        """Initialize a player with the data."""
        self._heos = heos
        # pylint: disable=protected-access
        self._commands = heos._commands

        self._name: str = str(data[const.ATTR_NAME])
        self._player_id: int = int(data[const.ATTR_PLAYER_ID])
        self._model: str = data[const.ATTR_MODEL]
        self._version: str = data[const.ATTR_VERSION]
        self._ip_address: str = data[const.ATTR_IP_ADDRESS]
        self._network: str = data[const.ATTR_NETWORK]
        self._line_out: int = data[const.ATTR_LINE_OUT]

        self._state: str | None = None
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
        self._state = await self._commands.get_player_state(self._player_id)

    async def refresh_now_playing_media(self) -> None:
        """Pull the latest now playing media."""
        payload = await self._commands.get_now_playing_state(self._player_id)
        self._now_playing_media.from_data(payload)

    async def refresh_volume(self) -> None:
        """Pull the latest volume."""
        self._volume = await self._commands.get_volume(self._player_id)

    async def refresh_mute(self) -> None:
        """Pull the latest mute status."""
        self._is_muted = await self._commands.get_mute(self._player_id)

    async def refresh_play_mode(self) -> None:
        """Pull the latest play mode."""
        self._repeat, self._shuffle = await self._commands.get_play_mode(
            self._player_id
        )

    async def set_state(self, state: str) -> None:
        """Set the state of the player."""
        await self._commands.set_player_state(self._player_id, state)

    async def play(self) -> None:
        """Set the start to play."""
        await self.set_state(const.PLAY_STATE_PLAY)

    async def pause(self) -> None:
        """Set the start to pause."""
        await self.set_state(const.PLAY_STATE_PAUSE)

    async def stop(self) -> None:
        """Set the start to stop."""
        await self.set_state(const.PLAY_STATE_STOP)

    async def set_volume(self, level: int) -> None:
        """Set the volume level."""
        await self._commands.set_volume(self._player_id, level)

    async def set_mute(self, state: bool) -> None:
        """Set the mute state."""
        await self._commands.set_mute(self._player_id, state)

    async def mute(self) -> None:
        """Set mute state."""
        await self.set_mute(True)

    async def unmute(self) -> None:
        """Clear mute state."""
        await self.set_mute(False)

    async def volume_up(self, step: int = const.DEFAULT_STEP) -> None:
        """Raise the volume."""
        await self._commands.volume_up(self._player_id, step)

    async def volume_down(self, step: int = const.DEFAULT_STEP) -> None:
        """Raise the volume."""
        await self._commands.volume_down(self._player_id, step)

    async def toggle_mute(self) -> None:
        """Toggle mute state."""
        await self._commands.toggle_mute(self._player_id)

    async def set_play_mode(self, repeat: const.RepeatType, shuffle: bool) -> None:
        """Set the play mode of the player."""
        await self._commands.set_play_mode(self._player_id, repeat, shuffle)

    async def clear_queue(self) -> None:
        """Clear the queue of the player."""
        await self._commands.clear_queue(self._player_id)

    async def play_next(self) -> None:
        """Clear the queue of the player."""
        await self._commands.play_next(self._player_id)

    async def play_previous(self) -> None:
        """Clear the queue of the player."""
        await self._commands.play_previous(self._player_id)

    async def play_input(
        self, input_name: str, *, source_player_id: int | None = None
    ) -> None:
        """Play the specified input."""
        await self._commands.play_input(
            self._player_id, input_name, source_player_id=source_player_id
        )

    async def play_input_source(self, input_source: MediaItem) -> None:
        """Play the specified input source."""
        if not input_source.media_id:
            raise ValueError(f"Media '{input_source}' is not playable")
        await self.play_input(
            input_source.media_id, source_player_id=input_source.source_id
        )

    async def play_favorite(self, preset: int) -> None:
        """Play the favorite by 1-based index."""
        await self._commands.play_preset(self._player_id, preset)

    async def play_url(self, url: str) -> None:
        """Play the specified URL."""
        await self._commands.play_stream(self._player_id, url)

    async def play_quick_select(self, quick_select_id: int) -> None:
        """Play the specified quick select."""
        await self._commands.play_quick_select(self._player_id, quick_select_id)

    async def add_to_queue(
        self, media: MediaItem, add_queue_option: const.AddCriteriaType
    ) -> None:
        """Add the specified source to the queue."""
        if not media.playable or media.container_id is None:
            raise ValueError(f"Media '{media}' is not playable")
        await self._commands.add_to_queue(
            self.player_id,
            media.source_id,
            media.container_id,
            add_queue_option,
            media.media_id,
        )

    async def set_quick_select(self, quick_select_id: int) -> None:
        """Set the specified quick select to the current source."""
        await self._commands.set_quick_select(self._player_id, quick_select_id)

    async def get_quick_selects(self) -> dict[int, str]:
        """Get a list of quick selects."""
        payload = await self._commands.get_quick_selects(self._player_id)
        return {int(data[const.ATTR_ID]): data[const.ATTR_NAME] for data in payload}

    async def event_update(self, event: HeosMessage, all_progress_events: bool) -> bool:
        """Return True if player update event changed state."""
        if event.command == const.EVENT_PLAYER_NOW_PLAYING_PROGRESS:
            return self._now_playing_media.event_update_progress(
                event, all_progress_events
            )
        if event.command == const.EVENT_PLAYER_STATE_CHANGED:
            self._state = event.get_message_value(const.ATTR_STATE)
            if self._state == const.PLAY_STATE_PLAY:
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
