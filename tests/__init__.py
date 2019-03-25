"""Tests for the pyheos library."""
import asyncio
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor
from typing import List, Optional, Union
from urllib.parse import parse_qsl, urlparse

import pytest

from pyheos import const
from pyheos.connection import SEPARATOR, SEPARATOR_BYTES

FILE_IO_POOL = ThreadPoolExecutor()


async def get_fixture(file: str):
    """Load a fixtures file."""
    file_name = "tests/fixtures/{file}.json".format(file=file)

    def read_file():
        with open(file_name) as open_file:
            return open_file.read()

    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(FILE_IO_POOL, read_file)


class MockHeosDevice:
    """Define a mock heos device."""

    def __init__(self):
        """Init a new instance of the mock heos device."""
        self._server = None  # type: asyncio.AbstractServer
        self._started = False
        self.connections = []  # type: List[ConnectionLog]
        self._matchers = []  # type: List[CommandMatcher]

    async def start(self):
        """Start the heos server."""
        self._started = True
        self._server = await asyncio.start_server(
            self._handle_connection, '127.0.0.1', const.CLI_PORT)

        self.register(const.COMMAND_HEART_BEAT, None, 'system.heart_beat')
        self.register(const.COMMAND_GET_PLAYERS, None, 'player.get_players')
        self.register(const.COMMAND_GET_PLAY_STATE, None,
                      'player.get_play_state')
        self.register(const.COMMAND_GET_NOW_PLAYING_MEDIA, None,
                      'player.get_now_playing_media')
        self.register(const.COMMAND_GET_VOLUME, None, 'player.get_volume')
        self.register(const.COMMAND_GET_MUTE, None, 'player.get_mute')
        self.register(const.COMMAND_GET_PLAY_MODE, None,
                      'player.get_play_mode')

    async def stop(self):
        """Stop the heos server."""
        if not self._started:
            return
        self._started = False
        for connection in self.connections:
            await connection.disconnect()
        self.connections.clear()
        self._server.close()
        await self._server.wait_closed()

    async def write_event(self, event: str):
        """Send an event through the event channel."""
        connection = next(conn for conn in self.connections
                          if conn.is_registered_for_events)
        await connection.write(event)

    def register(self, command: str, args: Optional[dict],
                 response: Union[str, List[str]], *,
                 replace: bool = False):
        """Register a matcher."""
        if replace:
            self._matchers = [m for m in self._matchers
                              if m.command != command]
        self._matchers.append(CommandMatcher(command, args, response))

    async def _handle_connection(
            self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter):

        log = ConnectionLog(reader, writer)
        self.connections.append(log)

        while self._started:
            try:
                result = await reader.readuntil(SEPARATOR_BYTES)
            except asyncio.IncompleteReadError:
                # Occurs when the reader is being stopped
                break

            result = result.decode().rstrip(SEPARATOR)

            url_parts = urlparse(result)
            query = dict(parse_qsl(url_parts.query))

            command = url_parts.hostname + url_parts.path
            fixture_name = "{}.{}".format(url_parts.hostname,
                                          url_parts.path.lstrip('/'))

            log.commands[command].append(result)

            # Try matchers
            matcher = next((matcher for matcher in self._matchers
                            if matcher.is_match(command, query)), None)
            if matcher:
                responses = await matcher.get_response(query)
                for response in responses:
                    writer.write((response + SEPARATOR).encode())
                    await writer.drain()
                continue

            if command == const.COMMAND_REGISTER_FOR_CHANGE_EVENTS:
                enable = query["enable"]
                if enable == 'on':
                    log.is_registered_for_events = True
                response = (await get_fixture(fixture_name)).replace(
                    "{enable}", enable)
                writer.write((response + SEPARATOR).encode())
                await writer.drain()
            else:
                pytest.fail("Unrecognized command: " + result)

        self.connections.remove(log)


class CommandMatcher:
    """Define a command match response."""

    def __init__(self, command: str, args: dict,
                 response: Union[str, List[str]]):
        """Init the command response."""
        self.command = command
        self.args = args

        if isinstance(response, str):
            response = [response]
        self._response = response

    def is_match(self, command, args):
        """Determine if the command matches the target."""
        if command != self.command:
            return False
        if self.args:
            for key, value in self.args.items():
                if not args[key] == value:
                    return False
        return True

    async def get_response(self, query: dict) -> List[str]:
        """Get the response body."""
        responses = []
        for fixture in self._response:
            responses.append(await self._get_response(fixture, query))
        return responses

    async def _get_response(self, response: str, query: dict) -> str:
        response = await get_fixture(response)
        keys = {
            'pid': '{player_id}',
            'sequence': '{sequence}',
            'state': '{state}',
            'level': '{level}'
        }
        for key, token in keys.items():
            value = query.get(key)
            if value is not None and token in response:
                response = response.replace(token, value)
        return response


class ConnectionLog:
    """Define a connection log."""

    def __init__(self, reader: asyncio.StreamReader,
                 writer: asyncio.StreamWriter):
        """Initialize the connection log."""
        self._reader = reader
        self._writer = writer
        self.is_registered_for_events = False
        self.commands = defaultdict(list)

    async def disconnect(self):
        """Close the connection."""
        self._writer.close()

    async def write(self, payload: str):
        """Write the payload to the stream."""
        data = (payload + SEPARATOR).encode()
        self._writer.write(data)
        await self._writer.drain()
