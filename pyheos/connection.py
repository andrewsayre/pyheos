"""Define the connection module."""

import asyncio
from collections import defaultdict
import json
import logging
from typing import Any, DefaultDict, Dict, List, Optional

from . import const
from .command import HeosCommands
from .response import HeosResponse

SEPARATOR = '\r\n'
SEPARATOR_BYTES = SEPARATOR.encode()

_LOGGER = logging.getLogger(__name__)


_QUOTE_MAP = {
    '&': '%26',
    '=': '%3D',
    '%': '%25'
}


def _quote(string: str) -> str:
    """Quote a string per the CLI specification."""
    return ''.join([_QUOTE_MAP.get(char, char) for char in str(string)])


def _encode_query(items: dict) -> str:
    """Encode a dict to query string per CLI specifications."""
    pairs = []
    for key, value in items.items():
        item = key + "=" + _quote(value)
        # Ensure 'url' goes last per CLI spec
        if key == 'url':
            pairs.append(item)
        else:
            pairs.insert(0, item)
    return '&'.join(pairs)


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

    async def command(self, command: str,
                      params: Dict[str, Any] = None) -> Optional[HeosResponse]:
        """Run a command and get it's response."""
        if not self._connected:
            raise ValueError

        # append sequence number
        sequence = self._sequence
        self._sequence += 1
        params = params or {}
        params['sequence'] = sequence
        command_name = command
        command = const.BASE_URI + command + '?' + _encode_query(params)

        # Add reservation
        event = ResponseEvent(sequence)
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


class HeosEventHandler:
    """Define a class that handles unsolicited events."""

    def __init__(self, heos):
        """Init the event handler class."""
        self._heos = heos

    async def handle_event(self, response: HeosResponse):
        """Handle a response event."""
        if response.command in const.PLAYER_EVENTS:
            player_id = response.get_player_id()
            player = self._heos.get_player(player_id)
            if player and (await player.event_update(response)):
                self._heos.dispatcher.send(
                    const.SIGNAL_PLAYER_UPDATED, player_id, response.command)
                _LOGGER.debug("%s event received: %s", player, response)
        elif response.command == const.EVENT_SOURCES_CHANGED:
            self._heos.dispatcher.send(
                const.SIGNAL_HEOS_UPDATED,
                const.EVENT_SOURCES_CHANGED)
        else:
            _LOGGER.debug("Unrecognized event: %s", response)
