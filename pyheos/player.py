"""Define the player module."""
from typing import Optional

from pyheos import const


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
        self._song_id = None  # type: int
        self._current_position = None  # type: int
        self._duration = None  # type: int

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
        self._song_id = int(data['sid'])
        self._current_position = None
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
    def song_id(self) -> int:
        """Get the source id of the playing media."""
        return self._song_id

    @property
    def current_position(self) -> int:
        """Get the current position within the playing media."""
        return self._current_position

    @property
    def duration(self):
        """Get the duration of the current playing media."""
        return self._duration


class HeosPlayer:
    """Define a HEOS player."""

    def __init__(self, commands, data: Optional[dict] = None):
        """Initialize a player with the data."""
        self._commands = commands
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
        self._now_playing_media = HeosNowPlayingMedia()

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
        self._version = data['version']
        self._ip_address = data['ip']
        self._network = data['network']
        self._line_out = int(data['lineout'])

    async def refresh(self):
        """Pull current state."""
        await self.refresh_state()
        await self.refresh_now_playing_media()
        await self.refresh_volume()
        await self.refresh_mute()
        await self.refresh_play_mode()

    async def refresh_state(self):
        """Refresh the now playing state."""
        self._state = await self._commands.get_player_state(self._player_id)

    async def refresh_now_playing_media(self):
        """Pull the latest now playing media."""
        await self._commands.get_now_playing_state(
            self._player_id, self._now_playing_media)

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

    async def set_state(self, state: str) -> bool:
        """Set the state of the player."""
        return await self._commands.set_player_state(self._player_id, state)

    async def play(self) -> bool:
        """Set the start to play."""
        return await self.set_state(const.PLAY_STATE_PLAY)

    async def pause(self) -> bool:
        """Set the start to pause."""
        return await self.set_state(const.PLAY_STATE_PAUSE)

    async def stop(self) -> bool:
        """Set the start to stop."""
        return await self.set_state(const.PLAY_STATE_STOP)

    async def set_volume(self, level: int) -> bool:
        """Set the volume level."""
        return await self._commands.set_volume(self._player_id, level)

    async def set_mute(self, state: bool) -> bool:
        """Set the mute state."""
        return await self._commands.set_mute(self._player_id, state)

    async def mute(self):
        """Set mute state."""
        return await self.set_mute(True)

    async def unmute(self):
        """Clear mute state."""
        return await self.set_mute(False)

    async def volume_up(self, step: int = const.DEFAULT_STEP):
        """Raise the volume."""
        return await self._commands.volume_up(self._player_id, step)

    async def volume_down(self, step: int = const.DEFAULT_STEP):
        """Raise the volume."""
        return await self._commands.volume_down(self._player_id, step)

    async def toggle_mute(self):
        """Toggle mute state."""
        return await self._commands.toggle_mute(self._player_id)

    async def set_play_mode(self, repeat: str, shuffle: bool):
        """Set the play mode of the player."""
        return await self._commands.set_play_mode(
            self._player_id, repeat, shuffle)

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
