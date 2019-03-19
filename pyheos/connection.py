"""Define the connection module."""

import asyncio
import json
import logging
from typing import Optional, Sequence, Tuple

from . import const
from .player import HeosNowPlayingMedia, HeosPlayer
from .response import HeosResponse

SEPARATOR = '\r\n'
SEPARATOR_BYTES = SEPARATOR.encode()

_LOGGER = logging.getLogger(__name__)


class HeosConnection:
    """Define a class that encapsulates read/write."""

    def __init__(self, host: str, timeout: int = const.DEFAULT_TIMEOUT):
        """Init a new HeosConnection class."""
        self.host = host  # type: str
        self.timeout = timeout  # type: int
        self._connected = False  # type: bool
        self._reader = None  # type: asyncio.StreamReader
        self._writer = None   # type: asyncio.StreamWriter
        self._sequence_lock = asyncio.Lock()
        self.commands = HeosCommands(self)

    async def connect(self):
        """Invoke the connect operation."""
        if self._connected:
            return
        self._reader, self._writer = await asyncio.open_connection(
            self.host, const.CLI_PORT)
        self._connected = True
        _LOGGER.debug("%s connected to %s", self.__class__.__name__, self.host)

    async def disconnect(self):
        """Disconnect from the device."""
        if not self._connected:
            return
        self._connected = False
        if self._writer:
            self._writer.close()
        _LOGGER.debug("%s disconnected from %s",
                      self.__class__.__name__, self.host)

    async def command(self, command: str) -> Optional[HeosResponse]:
        """Run a command and get it's response."""
        if not self._connected:
            raise ValueError

        async with self._sequence_lock:
            # Send command
            self._writer.write((command + SEPARATOR).encode())
            await self._writer.drain()

            while True:
                # Wait for response
                result = await asyncio.wait_for(
                    self._reader.readuntil(SEPARATOR_BYTES), self.timeout)
                # Create response object
                data = json.loads(result.decode())
                response = HeosResponse(data)
                # Support pending process
                if not response.is_under_process:
                    _LOGGER.debug("Executed command '%s': '%s'", command, data)
                    return response
                _LOGGER.debug("Command under process '%s': '%s'",
                              command, data)


class HeosCommandConnection(HeosConnection):
    """Define the command connection."""

    async def connect(self):
        """Invoke the connect operation."""
        await super().connect()
        await self.commands.register_for_change_events(False)


class HeosCommands:
    """Define a class that encapsulates well-known commands."""

    def __init__(self, connection: HeosConnection):
        """Init the command wrapper."""
        self._connection = connection

    async def register_for_change_events(self, enable=True) -> bool:
        """Enable or disable change event notifications."""
        enable_mode = "on" if enable else "off"
        command = const.COMMAND_REGISTER_FOR_CHANGE_EVENTS.format(
            enable=enable_mode)
        response = await self._connection.command(command)
        return response.result

    async def get_players(self) -> Sequence[HeosPlayer]:
        """Get players."""
        response = await self._connection.command(const.COMMAND_GET_PLAYERS)
        return [HeosPlayer(self, data) for data in response.payload]

    async def get_player_state(self, player_id: int) -> str:
        """Get the state of the player."""
        command = const.COMMAND_GET_PLAY_STATE.format(player_id=player_id)
        response = await self._connection.command(command)
        return response.get_message('state')

    async def set_player_state(self, player_id: int, state: str) -> bool:
        """Set the state of the player."""
        if state not in const.VALID_PLAY_STATES:
            raise ValueError("Invalid play state: " + state)
        command = const.COMMAND_SET_PLAY_STATE.format(
            player_id=player_id, state=state)
        response = await self._connection.command(command)
        return response.result

    async def get_now_playing_state(
            self, player_id: int,
            now_playing_media: HeosNowPlayingMedia) -> bool:
        """Get the now playing media information."""
        command = const.COMMAND_GET_NOW_PLAYING_MEDIA.format(
            player_id=player_id)
        response = await self._connection.command(command)
        now_playing_media.from_data(response.payload)
        return response.result

    async def get_volume(self, player_id: int) -> int:
        """Get the volume of the player."""
        command = const.COMMAND_GET_VOLUME.format(player_id=player_id)
        response = await self._connection.command(command)
        return int(response.get_message('level'))

    async def set_volume(self, player_id: int, level: int) -> bool:
        """Set the volume of the player."""
        if level < 0 or level > 100:
            raise ValueError("'level' must be in the range 0-100")
        command = const.COMMAND_SET_VOLUME.format(
            player_id=player_id, level=level)
        response = await self._connection.command(command)
        return response.result

    async def get_mute(self, player_id: str) -> bool:
        """Get the mute state of the player."""
        command = const.COMMAND_GET_MUTE.format(player_id=player_id)
        response = await self._connection.command(command)
        return response.get_message('state') == 'on'

    async def set_mute(self, player_id: str, state: bool) -> bool:
        """Set the mute state of the player."""
        mute_state = "on" if state else "off"
        command = const.COMMAND_SET_MUTE.format(
            player_id=player_id, state=mute_state)
        response = await self._connection.command(command)
        return response.result

    async def volume_up(self, player_id: int,
                        step: int = const.DEFAULT_STEP) -> bool:
        """Increase the volume level."""
        if step < 1 or step > 10:
            raise ValueError("'step' must be in the range 1-10")
        command = const.COMMAND_VOLUME_UP.format(
            player_id=player_id, step=step)
        response = await self._connection.command(command)
        return response.result

    async def volume_down(self, player_id: int,
                          step: int = const.DEFAULT_STEP) -> bool:
        """Increase the volume level."""
        if step < 1 or step > 10:
            raise ValueError("'step' must be in the range 1-10")
        command = const.COMMAND_VOLUME_DOWN.format(
            player_id=player_id, step=step)
        response = await self._connection.command(command)
        return response.result

    async def toggle_mute(self, player_id: int) -> bool:
        """Toggle the mute state.."""
        command = const.COMMAND_TOGGLE_MUTE.format(player_id=player_id)
        response = await self._connection.command(command)
        return response.result

    async def get_play_mode(self, player_id: int) -> Tuple[str, bool]:
        """Get the current play mode."""
        command = const.COMMAND_GET_PLAY_MODE.format(player_id=player_id)
        response = await self._connection.command(command)
        repeat = response.get_message('repeat')
        shuffle = response.get_message('shuffle') == 'on'
        return repeat, shuffle

    async def set_play_mode(self, player_id: int, repeat: str, shuffle: bool):
        """Set the current play mode."""
        if repeat not in const.VALID_REPEAT_MODES:
            raise ValueError("Invalid repeat mode: " + repeat)
        command = const.COMMAND_SET_PLAY_MODE.format(
            player_id=player_id, repeat=repeat,
            shuffle='on' if shuffle else 'off')
        response = await self._connection.command(command)
        return response.result

    async def clear_queue(self, player_id: int) -> bool:
        """Clear the queue."""
        command = const.COMMAND_CLEAR_QUEUE.format(player_id=player_id)
        response = await self._connection.command(command)
        return response.result

    async def play_next(self, player_id: int) -> bool:
        """Play next."""
        command = const.COMMAND_PLAY_NEXT.format(player_id=player_id)
        response = await self._connection.command(command)
        return response.result

    async def play_previous(self, player_id: int) -> bool:
        """Play next."""
        command = const.COMMAND_PLAY_PREVIOUS.format(player_id=player_id)
        response = await self._connection.command(command)
        return response.result


class HeosEventConnection(HeosConnection):
    """Define the event update channel connection."""

    def __init__(self, heos, host: str, timeout: int = const.DEFAULT_TIMEOUT):
        """Init HeosCommandConnection class."""
        super().__init__(host, timeout)
        self._handler = HeosEventHandler(heos)
        self._event_handler_task = None  # type: asyncio.Task

    async def connect(self):
        """Invoke the connect operation."""
        await super().connect()
        await self.commands.register_for_change_events(True)
        self._event_handler_task = asyncio.ensure_future(
            self._event_handler())

    async def disconnect(self):
        """Disconnect from the device."""
        await super().disconnect()
        if self._event_handler_task:
            self._event_handler_task.cancel()
            await self._event_handler_task
            self._event_handler_task = None

    async def _event_handler(self):
        while self._connected:
            # Wait for response
            try:
                result = await self._reader.readuntil(SEPARATOR_BYTES)
                data = json.loads(result.decode())
                response = HeosResponse()
                response.from_json(data)
                await self._handler.handle_event(response)
            except asyncio.CancelledError:
                # Occurs when the task is being killed
                return
            except Exception:  # pylint: disable=broad-except
                _LOGGER.exception("Failed to handle event")


class HeosEventHandler:
    """Define a class that handles unsolicited events."""

    def __init__(self, heos):
        """Init the event handler class."""
        self._heos = heos

    async def handle_event(self, response: HeosResponse):
        """Handle a response event."""
        if response.command == const.EVENT_PLAYER_NOW_PLAYING_PROGRESS:
            self._now_playing_progress(response)
        elif response.command == const.EVENT_PLAYER_STATE_CHANGED:
            self._state_changed(response)
        elif response.command == const.EVENT_PLAYER_NOW_PLAYING_CHANGED:
            await self._now_playing_changed(response)
        elif response.command == const.EVENT_PLAYER_VOLUME_CHANGED:
            self._volume_changed(response)
        elif response.command == const.EVENT_REPEAT_MODE_CHANGED:
            self._repeat_mode_changed(response)
        elif response.command == const.EVENT_SHUFFLE_MODE_CHANGED:
            self._shuffle_mode_changed(response)
        else:
            _LOGGER.debug("Unrecognized event: %s", response)

    def _state_changed(self, response: HeosResponse):
        player_id = response.get_player_id()
        state = response.get_message('state')
        player = self._heos.get_player(player_id)
        if player:
            player._state = state  # pylint: disable=protected-access
            self._heos.dispatcher.send(
                const.SIGNAL_PLAYER_UPDATED, player_id,
                const.EVENT_PLAYER_STATE_CHANGED)
            _LOGGER.debug("'%s' state changed to '%s'", player, state)

    async def _now_playing_changed(self, response: HeosResponse):
        player_id = response.get_player_id()
        player = self._heos.get_player(player_id)
        if player:
            await player.refresh_now_playing_media()
            self._heos.dispatcher.send(
                const.SIGNAL_PLAYER_UPDATED, player_id,
                const.EVENT_PLAYER_NOW_PLAYING_CHANGED)
            _LOGGER.debug("'%s' now playing media changed", player)

    def _volume_changed(self, response: HeosResponse):
        player_id = response.get_player_id()
        level = int(response.get_message('level'))
        mute = response.get_message('mute')
        player = self._heos.get_player(player_id)
        if player:
            # pylint: disable=protected-access
            player._volume = level
            # pylint: disable=protected-access
            player._is_muted = mute == 'on'
            self._heos.dispatcher.send(
                const.SIGNAL_PLAYER_UPDATED, player_id,
                const.EVENT_PLAYER_VOLUME_CHANGED)
            _LOGGER.debug("'%s' volume changed to '%s', mute changed to '%s'",
                          player, level, mute)

    def _now_playing_progress(self, response: HeosResponse):
        player_id = response.get_player_id()
        current_position = int(response.get_message('cur_pos'))
        duration = int(response.get_message('duration'))
        player = self._heos.get_player(player_id)
        if player:
            # pylint: disable=protected-access
            player.now_playing_media._current_position = current_position
            # pylint: disable=protected-access
            player.now_playing_media._duration = duration
            self._heos.dispatcher.send(
                const.SIGNAL_PLAYER_UPDATED, player_id,
                const.EVENT_PLAYER_NOW_PLAYING_PROGRESS)
            _LOGGER.debug("'%s' now playing progress changed: %s/%s",
                          player, current_position, duration)

    def _repeat_mode_changed(self, response: HeosResponse):
        player_id = response.get_player_id()
        repeat = response.get_message('repeat')
        player = self._heos.get_player(player_id)
        if player:
            # pylint: disable=protected-access
            player._repeat = repeat
            self._heos.dispatcher.send(
                const.SIGNAL_PLAYER_UPDATED, player_id,
                const.EVENT_REPEAT_MODE_CHANGED)
            _LOGGER.debug("'%s' repeat mode changed to '%s'",
                          player, repeat)

    def _shuffle_mode_changed(self, response: HeosResponse):
        player_id = response.get_player_id()
        shuffle = response.get_message('shuffle') == 'on'
        player = self._heos.get_player(player_id)
        if player:
            # pylint: disable=protected-access
            player._shuffle = shuffle
            self._heos.dispatcher.send(
                const.SIGNAL_PLAYER_UPDATED, player_id,
                const.EVENT_SHUFFLE_MODE_CHANGED)
            _LOGGER.debug("'%s' shuffle to '%s'",
                          player, shuffle)
