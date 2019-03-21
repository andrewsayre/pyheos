"""Define the connection module."""

import asyncio
from collections import defaultdict
import json
import logging
from typing import DefaultDict, List, Optional, Sequence, Tuple
from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse

from . import const
from .player import HeosNowPlayingMedia, HeosPlayer
from .response import HeosResponse

SEPARATOR = '\r\n'
SEPARATOR_BYTES = SEPARATOR.encode()

_LOGGER = logging.getLogger(__name__)


class HeosConnection:
    """Define a class that encapsulates read/write."""

    def __init__(self, heos, host: str, timeout: int = const.DEFAULT_TIMEOUT):
        """Init a new HeosConnection class."""
        self.host = host  # type: str
        self.commands = HeosCommands(self)
        self.timeout = timeout  # type: int
        self._connected = False  # type: bool
        self._reader = None  # type: asyncio.StreamReader
        self._writer = None   # type: asyncio.StreamWriter
        self._response_handler_task = None  # type: asyncio.Task
        self._handler = HeosEventHandler(heos)
        self._pending_commands = \
            defaultdict(list)  # type: DefaultDict[str, List[ResponseEvent]]
        self._sequence = 0

    async def connect(self):
        """Invoke the connect operation."""
        if self._connected:
            return
        self._reader, self._writer = await asyncio.open_connection(
            self.host, const.CLI_PORT)
        self._connected = True
        self._response_handler_task = asyncio.ensure_future(
            self._response_handler())
        await self.commands.register_for_change_events()
        _LOGGER.debug("Connected to %s", self.host)

    async def disconnect(self):
        """Disconnect from the device."""
        if not self._connected:
            return
        self._connected = False
        if self._response_handler_task:
            self._response_handler_task.cancel()
            await self._response_handler_task
            self._response_handler_task = None
        if self._writer:
            self._writer.close()
            self._writer = None
        self._reader = None
        self._sequence = 0
        self._pending_commands.clear()
        _LOGGER.debug("Disconnected from %s", self.host)

    async def _response_handler(self):
        while self._connected:
            # Wait for response
            try:
                result = await self._reader.readuntil(SEPARATOR_BYTES)
                data = json.loads(result.decode())
                response = HeosResponse(data)

                # Ignore processing
                if response.is_under_process:
                    _LOGGER.debug("Command under process '%s': '%s'",
                                  response.command, data)
                    continue
                # Handle events
                if response.is_event:
                    asyncio.ensure_future(self._handler.handle_event(response))
                    continue
                # Find pending command
                commands = self._pending_commands[response.command]
                if not commands:
                    _LOGGER.debug("Received response with no pending "
                                  "command: '%s'", response.command)
                    continue
                sequence = response.get_message('sequence')
                if sequence:
                    sequence_id = int(sequence)
                    event = next((event for event in commands
                                  if event.sequence == sequence_id), None)
                    commands.remove(event)
                else:
                    event = commands.pop(0)
                event.set(response)

            except asyncio.CancelledError:
                # Occurs when the task is being killed
                return
            except Exception:  # pylint: disable=broad-except
                _LOGGER.exception("Failed to handle response")

    async def command(self, command: str) -> Optional[HeosResponse]:
        """Run a command and get it's response."""
        if not self._connected:
            raise ValueError

        # append sequence number
        sequence = self._sequence
        self._sequence += 1
        uri = list(urlparse(command))
        query = dict(parse_qsl(uri[4]))
        query['sequence'] = sequence
        uri[4] = urlencode(query)
        command = urlunparse(uri)
        # Add reservation
        event = ResponseEvent(sequence)
        command_name = uri[1] + uri[2]
        pending_commands = self._pending_commands[command_name]
        pending_commands.append(event)
        # Send command
        self._writer.write((command + SEPARATOR).encode())
        await self._writer.drain()

        try:
            response = await asyncio.wait_for(event.wait(), self.timeout)
        except asyncio.TimeoutError:
            if event in pending_commands:
                pending_commands.remove(event)
            raise
        _LOGGER.debug("Executed command '%s': '%s'", command, response)
        return response


class ResponseEvent:
    """Define an awaitable command event response."""

    def __init__(self, sequence: int):
        """Init a new instance of the CommandEvent."""
        self._event = asyncio.Event()
        self._sequence = sequence
        self._response = None

    @property
    def sequence(self) -> int:
        """Get the sequence that represents this event."""
        return self._sequence

    async def wait(self):
        """Wait until the event is set."""
        await self._event.wait()
        return self._response

    def set(self, response: HeosResponse):
        """Set the response."""
        self._response = response
        self._event.set()


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
