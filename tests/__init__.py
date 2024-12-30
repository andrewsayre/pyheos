"""Tests for the pyheos library."""

import asyncio
import logging
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor
from typing import Any, Final, Optional, Union
from urllib.parse import parse_qsl, urlparse

import pytest

from pyheos import Heos, const
from pyheos.const import SEPARATOR, SEPARATOR_BYTES

FILE_IO_POOL = ThreadPoolExecutor()
_LOGGER: Final = logging.getLogger(__name__)


async def get_fixture(file: str) -> str:
    """Load a fixtures file."""
    file_name = f"tests/fixtures/{file}.json"

    def read_file() -> str:
        with open(file_name, encoding="utf-8") as open_file:
            return open_file.read()

    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(FILE_IO_POOL, read_file)


def connect_handler(heos: Heos, signal: str, event: str) -> asyncio.Event:
    """Connect a handler to the specific signal and assert event."""
    trigger = asyncio.Event()

    async def handler(target_event: str, *args: Any) -> None:
        if target_event == event:
            trigger.set()

    heos.dispatcher.connect(signal, handler)
    return trigger


class MockHeosDevice:
    """Define a mock heos device."""

    def __init__(self) -> None:
        """Init a new instance of the mock heos device."""
        self._server: asyncio.AbstractServer | None = None
        self._started: bool = False
        self.connections: list[ConnectionLog] = []
        self._matchers: list[CommandMatcher] = []

    async def start(self) -> None:
        """Start the heos server."""
        self._started = True
        self._server = await asyncio.start_server(
            self._handle_connection, "127.0.0.1", const.CLI_PORT
        )

        self.register(const.COMMAND_HEART_BEAT, None, "system.heart_beat")
        self.register(const.COMMAND_ACCOUNT_CHECK, None, "system.check_account")
        self.register(const.COMMAND_GET_PLAYERS, None, "player.get_players")
        self.register(const.COMMAND_GET_PLAY_STATE, None, "player.get_play_state")
        self.register(
            const.COMMAND_GET_NOW_PLAYING_MEDIA, None, "player.get_now_playing_media"
        )
        self.register(const.COMMAND_GET_VOLUME, None, "player.get_volume")
        self.register(const.COMMAND_GET_MUTE, None, "player.get_mute")
        self.register(const.COMMAND_GET_PLAY_MODE, None, "player.get_play_mode")
        self.register(const.COMMAND_GET_GROUPS, None, "group.get_groups")
        self.register(const.COMMAND_GET_GROUP_VOLUME, None, "group.get_volume")
        self.register(const.COMMAND_GET_GROUP_MUTE, None, "group.get_mute")

    async def stop(self) -> None:
        """Stop the heos server."""
        if not self._started:
            return
        self._started = False
        for connection in self.connections:
            await connection.disconnect()
        self.connections.clear()

        assert self._server is not None
        self._server.close()
        await self._server.wait_closed()

    async def write_event(self, event: str) -> None:
        """Send an event through the event channel."""
        connection = next(
            conn for conn in self.connections if conn.is_registered_for_events
        )
        await connection.write(event)

    def register(
        self,
        command: str,
        args: Optional[dict],
        response: Union[str, list[str]],
        *,
        replace: bool = False,
    ) -> None:
        """Register a matcher."""
        if replace:
            self._matchers = [m for m in self._matchers if m.command != command]
        self._matchers.append(CommandMatcher(command, args, response))

    async def _handle_connection(
        self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter
    ) -> None:
        log = ConnectionLog(reader, writer)
        self.connections.append(log)

        while self._started:
            try:
                result: str = (await reader.readuntil(SEPARATOR_BYTES)).decode()
            except asyncio.IncompleteReadError:
                # Occurs when the reader is being stopped
                return

            result = result.rstrip(SEPARATOR)

            url_parts = urlparse(result)
            query = dict(parse_qsl(url_parts.query))

            command = str(url_parts.hostname) + str(url_parts.path)
            fixture_name = (
                f"{str(url_parts.hostname)}.{str(url_parts.path.lstrip('/'))}"
            )

            log.commands[command].append(result)

            # Try matchers
            matcher = next(
                (
                    matcher
                    for matcher in self._matchers
                    if matcher.is_match(command, query)
                ),
                None,
            )
            if matcher:
                responses = await matcher.get_response(query)
                for response in responses:
                    writer.write((response + SEPARATOR).encode())
                    await writer.drain()
                continue

            if command == const.COMMAND_REGISTER_FOR_CHANGE_EVENTS:
                enable = str(query[const.ATTR_ENABLE])
                log.is_registered_for_events = enable == const.VALUE_ON
                response = (await get_fixture(fixture_name)).replace("{enable}", enable)
                writer.write((response + SEPARATOR).encode())
                await writer.drain()
            else:
                pytest.fail(f"Unrecognized command: {result}")

        try:
            self.connections.remove(log)
        except ValueError:
            pass


class CommandMatcher:
    """Define a command match response."""

    def __init__(
        self, command: str, args: dict | None, response: Union[str, list[str]]
    ) -> None:
        """Init the command response."""
        self.command = command
        self.args = args

        if isinstance(response, str):
            response = [response]
        self._response = response

    def is_match(self, command: str, args: dict) -> bool:
        """Determine if the command matches the target."""
        if command != self.command:
            return False
        if self.args:
            for key, value in self.args.items():
                if not args[key] == str(value):
                    return False
        return True

    async def get_response(self, query: dict) -> list[str]:
        """Get the response body."""
        responses = []
        for fixture in self._response:
            responses.append(await self._get_response(fixture, query))
        return responses

    async def _get_response(self, response: str, query: dict) -> str:
        response = await get_fixture(response)
        keys = {
            const.ATTR_PLAYER_ID: "{player_id}",
            const.ATTR_STATE: "{state}",
            const.ATTR_LEVEL: "{level}",
        }
        for key, token in keys.items():
            value = query.get(key)
            if value is not None and token in response:
                response = response.replace(token, value)
        return response


class ConnectionLog:
    """Define a connection log."""

    def __init__(
        self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter
    ) -> None:
        """Initialize the connection log."""
        self._reader = reader
        self._writer = writer
        self.is_registered_for_events = False
        self.commands: dict[str, list[str]] = defaultdict(list)

    async def disconnect(self) -> None:
        """Close the connection."""
        self._writer.close()
        await self._writer.wait_closed()

    async def write(self, payload: str) -> None:
        """Write the payload to the stream."""
        data = (payload + SEPARATOR).encode()
        self._writer.write(data)
        await self._writer.drain()
