"""Define the connection module."""

import asyncio
import json
import logging
from typing import Optional, Sequence

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
        _LOGGER.debug("Connected to %s", self.host)

    async def disconnect(self):
        """Disconnect from the device."""
        if not self._connected:
            return
        self._connected = False
        if self._writer:
            self._writer.close()
        _LOGGER.debug("Disconnected from %s", self.host)

    async def command(self, command: str) -> Optional[HeosResponse]:
        """Run a command and get it's response."""
        if not self._connected:
            raise ValueError

        async with self._sequence_lock:
            # Send command
            self._writer.write((command + SEPARATOR).encode())
            await self._writer.drain()
            # Wait for response
            result = await asyncio.wait_for(
                self._reader.readuntil(SEPARATOR_BYTES), self.timeout)
        # Create response object
        data = json.loads(result.decode())
        response = HeosResponse()
        response.from_json(data)
        _LOGGER.debug("Executed command '%s': '%s'", command, data)
        return response


class HeosCommandConnection(HeosConnection):
    """Define the command connection."""

    async def connect(self):
        """Invoke the connect operation."""
        await super().connect()
        await self.commands.register_for_change_events(False)


class HeosCommands:
    """Define a class that encapsulates well-known commands."""

    def __init__(self, connection: HeosCommandConnection):
        """Init the command wrapper."""
        self._connection = connection

    async def register_for_change_events(self, enable=True) -> bool:
        """Enable or disable change event notifications."""
        enable_mode = "on" if enable else "off"
        command = const.COMMAND_REGISTER_FOR_CHANGE_EVENTS.format(
            enable=enable_mode)
        response = await self._connection.command(command)
        return response.get_message('enable') == enable_mode

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
        return response.get_message('state') == state

    async def get_now_playing_state(
            self, player_id: int, now_playing_media: HeosNowPlayingMedia):
        """Get the now playing media information."""
        command = const.COMMAND_GET_NOW_PLAYING_MEDIA.format(
            player_id=player_id)
        response = await self._connection.command(command)
        now_playing_media.from_data(response.payload)


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
            try:
                await self._event_handler_task
            except asyncio.CancelledError:
                pass
            self._event_handler_task = None

    async def _event_handler(self):
        while self._connected:
            # Wait for response
            try:
                result = await self._reader.readuntil(SEPARATOR_BYTES)
            except asyncio.IncompleteReadError:
                # Occurs when the task is being killed
                break

            if result is None:
                continue
            # Create response object
            try:
                data = json.loads(result.decode())
                response = HeosResponse()
                response.from_json(data)
                await self._handler.handle_event(response)
            except Exception:  # pylint: disable=broad-except
                _LOGGER.exception("Failed to handle event: %s", result)


class HeosEventHandler:
    """Define a class that handles unsolicited events."""

    def __init__(self, heos):
        """Init the event handler class."""
        self._heos = heos

    async def handle_event(self, response: HeosResponse):
        """Handle a response event."""
        if response.command == const.COMMAND_PLAYER_STATE_CHANGED:
            self._handle_state_changed(response)
        elif response.command == const.COMMAND_PLAYER_NOW_PLAYING_CHANGED:
            await self._handle_now_playing_changed(response)
        else:
            _LOGGER.debug("Unrecognized event: %s", response)

    def _handle_state_changed(self, response: HeosResponse):
        player_id = response.get_player_id()
        state = response.get_message('state')
        player = self._heos.get_player(player_id)
        if player:
            player._state = state  # pylint: disable=protected-access
            self._heos.dispatcher.send(
                const.SIGNAL_PLAYER_UPDATED, player_id)
            _LOGGER.debug("'%s' state changed to '%s'", player, state)

    async def _handle_now_playing_changed(self, response: HeosResponse):
        player_id = response.get_player_id()
        player = self._heos.get_player(player_id)
        if player:
            await player.refresh_now_playing_media()
            self._heos.dispatcher.send(
                const.SIGNAL_PLAYER_UPDATED, player_id)
            _LOGGER.debug("'%s' now playing media changed", player)
