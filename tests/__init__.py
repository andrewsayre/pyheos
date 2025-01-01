"""Tests for the pyheos library."""

import asyncio
import functools
import json
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from typing import Any, cast
from urllib.parse import parse_qsl, urlparse

from pyheos import Heos, const
from pyheos.const import SEPARATOR, SEPARATOR_BYTES
from pyheos.media import MediaItem

FILE_IO_POOL = ThreadPoolExecutor()


def calls_command(
    fixture: str, command_args: dict[str, Any], assert_called: bool = True
) -> Callable:
    """Return decoraor that registers the command fixture provided."""

    def wrapper(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapped(*args: Any, **kwargs: Any) -> Any:
            # Get the fixture command
            fixture_data = json.loads(await get_fixture(fixture))
            command = fixture_data[const.ATTR_HEOS]["command"]

            # Find the mock heos parameter.
            mock_heos = cast(MockHeosDevice, kwargs["heos"].device)
            mock_heos.register(command, command_args, fixture)

            result = await func(*args, **kwargs)

            if assert_called:
                mock_heos.assert_command_called(command)

            return result

        return wrapped

    return wrapper


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


class MockHeos(Heos):
    """Define a mock heos connection."""

    device: "MockHeosDevice"


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
        args: dict[str, Any] | None,
        responses: str | list[str],
        *,
        replace: bool = False,
    ) -> None:
        """Register a matcher."""
        if replace:
            self._matchers = [m for m in self._matchers if m.command != command]
        if isinstance(responses, str):
            responses = [responses]
        self._matchers.append(CommandMatcher(command, args, responses))

    def assert_command_called(
        self, target_command: str, target_args: dict[str, Any] | None = None
    ) -> None:
        """
        Assert that the commands were called.

        Args:
            command: The command to check.
            args: The arguments to check. If None, only the command is checked.
        """
        self.connections[0].assert_command_called(target_command, target_args)

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

            log.add_called_command(command, query)

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
                assert False, f"Unrecognized command: {result}"

        try:
            self.connections.remove(log)
        except ValueError:
            pass


@dataclass
class CalledCommand:
    command: str
    _args: dict[str, Any] | None = field(default_factory=dict)

    @functools.cached_property
    def args(self) -> dict[str, str] | None:
        if self._args is None:
            return None
        return CalledCommand._convert_dict_to_strings(self._args)

    @staticmethod
    def _convert_dict_to_strings(args: dict[str, Any]) -> dict[str, str]:
        return {key: str(value) for key, value in args.items()}

    def is_match(
        self, match_command: str, match_args: dict[str, Any] | None = None
    ) -> bool:
        """Determine if the command matches the target."""
        if self.command != match_command:
            return False
        if match_args is not None and self.args is not None:
            return self.args == CalledCommand._convert_dict_to_strings(match_args)
        return True


@dataclass
class CommandMatcher(CalledCommand):
    """Define a command match response."""

    responses: list[str] = field(default_factory=list)

    async def get_response(self, query: dict) -> list[str]:
        """Get the response body."""
        responses = []
        for fixture in self.responses:
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
        self.commands: list[CalledCommand] = []

    async def disconnect(self) -> None:
        """Close the connection."""
        self._writer.close()
        await self._writer.wait_closed()

    async def write(self, payload: str) -> None:
        """Write the payload to the stream."""
        data = (payload + SEPARATOR).encode()
        self._writer.write(data)
        await self._writer.drain()

    def add_called_command(self, command: str, args: dict[str, str]) -> None:
        """Add a called command."""
        self.commands.append(CalledCommand(command, args))

    def assert_command_called(
        self, target_command: str, target_args: dict[str, Any] | None = None
    ) -> None:
        """Assert that the command was called."""
        for called_command in self.commands:
            if called_command.is_match(target_command, target_args):
                return
        assert (
            False
        ), f"Command {target_command} was not called with arguments {target_args}."


class media_items:
    input = MediaItem(
        -263109739,
        "HEOS Drive - AUX In 1",
        const.MediaType.STATION,
        "",
        None,
        True,
        False,
        None,
        "inputs/aux_in_1",
        None,
        None,
        None,
    )
