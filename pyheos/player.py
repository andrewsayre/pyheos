"""Define the player module."""
import asyncio
from datetime import datetime
from typing import Optional, Sequence

from . import const
from .response import HeosResponse
from .source import InputSource


class HeosNowPlayingMedia:
    """Define now playing media information."""

    def __init__(self):
        """Init NowPlayingMedia info."""
        self._type = None  # type: str
        self._song = None  # type: str
        self._station = None  # type: str
        self._album = None  # type: str
        self._artist = None  # type: str
        self._image_url = None  # type: str
        self._album_id = None  # type: str
        self._media_id = None  # type: str
        self._queue_id = None  # type: int
        self._source_id = None  # type: int
        self._current_position = None  # type: int
        self._current_position_updated = None  # type: datetime
        self._duration = None  # type: int
        self._supported_controls = const.CONTROLS_ALL  # type: Sequence[str]

    def from_data(self, data: dict):
        """Update the attributes from the supplied data."""
        self._type = data['type']
        self._song = data['song']
        self._station = data.get('station')
        self._album = data['album']
        self._artist = data['artist']
        self._image_url = data['image_url']
        self._album_id = data['album_id']
        self._media_id = data['mid']
        self._queue_id = int(data['qid'])
        self._source_id = int(data['sid'])

        supported_controls = const.CONTROLS_ALL
        controls = const.SOURCE_CONTROLS.get(self._source_id)
        if controls:
            supported_controls = controls.get(self._type, supported_controls)
        self._supported_controls = supported_controls

        self.clear_progress()

    def event_update_progress(
            self, event: HeosResponse, all_progress_events: bool) -> bool:
        """Update the position/duration from an event."""
        if all_progress_events or self._current_position is None:
            self._current_position = int(event.get_message('cur_pos'))
            self._current_position_updated = datetime.utcnow()
            self._duration = int(event.get_message('duration'))
            return True
        return False

    def clear_progress(self):
        """Clear the current position."""
        self._current_position = None
        self._current_position_updated = None
        self._duration = None

    @property
    def type(self) -> str:
        """Get the type of the media playing."""
        return self._type

    @property
    def song(self) -> str:
        """Get the song playing."""
        return self._song

    @property
    def station(self) -> str:
        """Get the station playing."""
        return self._station

    @property
    def album(self) -> str:
        """Get the album playing."""
        return self._album

    @property
    def artist(self) -> str:
        """Get the artist playing."""
        return self._artist

    @property
    def image_url(self) -> str:
        """Get the image url of the media playing."""
        return self._image_url

    @property
    def album_id(self) -> str:
        """Get the id of the playing album."""
        return self._album_id

    @property
    def media_id(self) -> str:
        """Get the media id of the playing media."""
        return self._media_id

    @property
    def queue_id(self) -> int:
        """Get the queue id of the playing media."""
        return self._queue_id

    @property
    def source_id(self) -> int:
        """Get the source id of the playing media."""
        return self._source_id

    @property
    def current_position(self) -> int:
        """Get the current position within the playing media."""
        return self._current_position

    @property
    def current_position_updated(self) -> datetime:
        """Get the datetime the position was last updated."""
        return self._current_position_updated

    @property
    def duration(self):
        """Get the duration of the current playing media."""
        return self._duration

    @property
    def supported_controls(self):
        """Get the supported controls given the source."""
        return self._supported_controls


class HeosPlayer:
    """Define a HEOS player."""

    def __init__(self, heos, data: Optional[dict] = None):
        """Initialize a player with the data."""
        self._heos = heos
        # pylint: disable=protected-access
        self._commands = heos._connection.commands
        self._name = None       # type: str
        self._player_id = None  # type: int
        self._model = None  # type: str
        self._version = None  # type: str
        self._ip_address = None  # type: str
        self._network = None  # type: str
        self._line_out = None  # type: int
        if data:
            self.from_data(data)
        self._state = None  # type: None
        self._volume = None  # type: int
        self._is_muted = None  # type: bool
        self._repeat = None  # type: str
        self._shuffle = None  # type: bool
        self._playback_error = None  # type: str
        self._now_playing_media = HeosNowPlayingMedia()
        self._available = True  # type: bool

    def __str__(self):
        """Get a user-readable representation of the player."""
        return "{{{} ({})}}".format(self._name, self._model)

    def __repr__(self):
        """Get a debug representation of the player."""
        return "{{{} ({}) with id {} at {}}}".format(
            self.name, self._model, self._player_id, self._ip_address)

    def from_data(self, data: dict):
        """Update the attributes from the supplied data."""
        self._name = data['name']
        self._player_id = int(data['pid'])
        self._model = data['model']
        self._version = data.get('version')
        self._ip_address = data['ip']
        self._network = data['network']
        self._line_out = int(data['lineout'])

    def set_available(self, available):
        """Mark player removed after a change event."""
        self._available = available

    async def refresh(self):
        """Pull current state."""
        await asyncio.gather(self.refresh_state(),
                             self.refresh_now_playing_media(),
                             self.refresh_volume(),
                             self.refresh_mute(),
                             self.refresh_play_mode())

    async def refresh_state(self):
        """Refresh the now playing state."""
        self._state = await self._commands.get_player_state(self._player_id)

    async def refresh_now_playing_media(self):
        """Pull the latest now playing media."""
        payload = await self._commands.get_now_playing_state(self._player_id)
        self._now_playing_media.from_data(payload)

    async def refresh_volume(self):
        """Pull the latest volume."""
        self._volume = await self._commands.get_volume(self._player_id)

    async def refresh_mute(self):
        """Pull the latest mute status."""
        self._is_muted = await self._commands.get_mute(self._player_id)

    async def refresh_play_mode(self):
        """Pull the latest play mode."""
        self._repeat, self._shuffle = \
            await self._commands.get_play_mode(self._player_id)

    async def set_state(self, state: str):
        """Set the state of the player."""
        await self._commands.set_player_state(self._player_id, state)

    async def play(self):
        """Set the start to play."""
        await self.set_state(const.PLAY_STATE_PLAY)

    async def pause(self):
        """Set the start to pause."""
        await self.set_state(const.PLAY_STATE_PAUSE)

    async def stop(self):
        """Set the start to stop."""
        await self.set_state(const.PLAY_STATE_STOP)

    async def set_volume(self, level: int):
        """Set the volume level."""
        await self._commands.set_volume(self._player_id, level)

    async def set_mute(self, state: bool):
        """Set the mute state."""
        await self._commands.set_mute(self._player_id, state)

    async def mute(self):
        """Set mute state."""
        await self.set_mute(True)

    async def unmute(self):
        """Clear mute state."""
        await self.set_mute(False)

    async def volume_up(self, step: int = const.DEFAULT_STEP):
        """Raise the volume."""
        await self._commands.volume_up(self._player_id, step)

    async def volume_down(self, step: int = const.DEFAULT_STEP):
        """Raise the volume."""
        await self._commands.volume_down(self._player_id, step)

    async def toggle_mute(self):
        """Toggle mute state."""
        await self._commands.toggle_mute(self._player_id)

    async def set_play_mode(self, repeat: str, shuffle: bool):
        """Set the play mode of the player."""
        await self._commands.set_play_mode(
            self._player_id, repeat, shuffle)

    async def clear_queue(self):
        """Clear the queue of the player."""
        await self._commands.clear_queue(self._player_id)

    async def play_next(self):
        """Clear the queue of the player."""
        await self._commands.play_next(self._player_id)

    async def play_previous(self):
        """Clear the queue of the player."""
        await self._commands.play_previous(self._player_id)

    async def play_input(
            self, input_name: str, *, source_player_id: int = None):
        """Play the specified input."""
        await self._commands.play_input(
            self._player_id, input_name, source_player_id=source_player_id)

    async def play_input_source(self, input_source: InputSource):
        """Play the specified input source."""
        await self.play_input(
            input_source.input_name, source_player_id=input_source.player_id)

    async def play_favorite(self, preset: int):
        """Play the favorite by 1-based index."""
        await self._commands.play_preset(self._player_id, preset)

    async def play_url(self, url: str):
        """Play the specified URL."""
        await self._commands.play_stream(self._player_id, url)

    async def event_update(self, event: HeosResponse,
                           all_progress_events: bool) -> bool:
        """Return True if player update event changed state."""
        if event.command == const.EVENT_PLAYER_NOW_PLAYING_PROGRESS:
            return self._now_playing_media.event_update_progress(
                event, all_progress_events)
        if event.command == const.EVENT_PLAYER_STATE_CHANGED:
            self._state = event.get_message('state')
            if self._state == const.PLAY_STATE_PLAY:
                self._now_playing_media.clear_progress()
        elif event.command == const.EVENT_PLAYER_NOW_PLAYING_CHANGED:
            await self.refresh_now_playing_media()
        elif event.command == const.EVENT_PLAYER_VOLUME_CHANGED:
            self._volume = int(float(event.get_message('level')))
            self._is_muted = event.get_message('mute') == 'on'
        elif event.command == const.EVENT_REPEAT_MODE_CHANGED:
            self._repeat = event.get_message('repeat')
        elif event.command == const.EVENT_SHUFFLE_MODE_CHANGED:
            self._shuffle = event.get_message('shuffle') == 'on'
        elif event.command == const.EVENT_PLAYER_PLAYBACK_ERROR:
            self._playback_error = event.get_message('error')
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
    def line_out(self) -> int:
        """Get the line out configuration."""
        return self._line_out

    @property
    def state(self) -> str:
        """Get the state of the player."""
        return self._state

    @property
    def now_playing_media(self) -> HeosNowPlayingMedia:
        """Get the now playing media information."""
        return self._now_playing_media

    @property
    def volume(self) -> int:
        """Get the volume of the player."""
        return self._volume

    @property
    def is_muted(self) -> bool:
        """Get whether the device is muted or not."""
        return self._is_muted

    @property
    def repeat(self) -> str:
        """Get the repeat mode."""
        return self._repeat

    @property
    def shuffle(self) -> bool:
        """Get if shuffle is active."""
        return self._shuffle

    @property
    def available(self) -> bool:
        """Return True if this player is available."""
        return self._available \
            and self._heos.connection_state == const.STATE_CONNECTED

    @property
    def playback_error(self) -> str:
        """Get the last playback error."""
        return self._playback_error

    @property
    def heos(self):
        """Get the heos instance attached to this player."""
        return self._heos
