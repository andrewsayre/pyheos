"""Tests for the pyheos library."""
from urllib.parse import urlparse, parse_qsl
from pyheos import const
from pyheos.connection import SEPARATOR_BYTES, SEPARATOR
from collections import defaultdict

import asyncio


def get_fixture(file: str):
    """Load a fixtures file."""
    file_name = "tests/fixtures/{file}.json".format(file=file)
    with open(file_name) as open_file:
        return open_file.read()


class MockHeosDevice:
    """Define a mock heos device."""

    def __init__(self):
        """Init a new instance of the mock heos device."""
        self._server = None  # type: asyncio.AbstractServer
        self._started = False
        self.connections = []

    async def start(self):
        """Start the heos server."""
        self._started = True
        self._server = await asyncio.start_server(
            self._handle_connection, '127.0.0.1', const.CLI_PORT)

    async def stop(self):
        """Stop the heos server."""
        self._started = False
        self._server.close()
        await self._server.wait_closed()

    async def _handle_connection(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter):

        log = ConnectionLog()
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
            fixture_name = "{}.{}".format(url_parts.hostname, url_parts.path.lstrip('/'))
            response = None

            if command == 'system/register_for_change_events':
                enable = query["enable"]
                if enable == 'on':
                    log.is_registered_for_events = True
                response = get_fixture(fixture_name).replace(
                    "{enable}", enable)
            elif command == 'player/get_players':
                response = get_fixture(fixture_name)

            elif command == 'player/get_play_state':
                response = get_fixture(fixture_name).replace(
                    '{player_id}', query['pid'])

            elif command == 'player/get_now_playing_media':
                response = get_fixture(fixture_name).replace(
                    '{player_id}', query['pid'])

            log.commands[command].append(result)

            writer.write((response + SEPARATOR).encode())
            await writer.drain()


class ConnectionLog:
    """Define a connection log."""

    def __init__(self):
        """Initialize the connection log."""
        self.is_registered_for_events = False
        self.commands = defaultdict(list)
