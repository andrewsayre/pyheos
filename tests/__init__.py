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

FILE_IO_POOL = ThreadPoolExecutor()


@dataclass
class CallCommand:
    """Define a command call.

    Args:
        fixture: The name of the json fixture to load. The command will be determiend from this file.
        command_args: The arguments that are expected to be passed. If set to None, any argument combination is accepted.
        when: Only registers the command if the test method arguments match the provided values.
        assert_called: Assert the command was called after test execution. The default is True.
    """

    fixture: str
    command_args: dict[str, Any] | None = None
    when: dict[str, Any] | None = None
    assert_called: bool = True

    def get_resolve_args(self, args: dict[str, Any]) -> dict[str, Any] | None:
        """Resolve the arguments."""
        if self.command_args is None:
            return None
        resolved_args = {}
        for key, value in self.command_args.items():
            if isinstance(value, ArgumentValue):
                resolved_args[key] = value.get_value(args)
            else:
                resolved_args[key] = value
        return resolved_args


@dataclass
class ArgumentValue:
    """Define an argument value source."""

    value: Any | None = field(default=None, kw_only=True)
    arg_name: str | None = field(default=None, kw_only=True)
    formatter: str | None = field(default=None, kw_only=True)

    def get_value(self, args: dict[str, Any]) -> Any:
        """Get the value."""
        if self.value:
            return value
        assert self.arg_name is not None
        arg_value = args[self.arg_name]
        if self.formatter == "on_off":
            return const.VALUE_ON if arg_value else const.VALUE_OFF
        return arg_value


def calls_commands(*commands: CallCommand) -> Callable:
    """
    Decorator that registers commands prior to test execution.

    Args:
        commands: The commands to register.
    """

    def wrapper(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapped(*args: Any, **kwargs: Any) -> Any:
            # Build a list of commands that match the when conditions
            matched_commands: list[CallCommand] = []
            for command in commands:
                if command.when is not None:
                    for key, value in command.when.items():
                        if kwargs.get(key) != value:
                            break
                    else:
                        matched_commands.append(command)
                else:
                    matched_commands.append(command)

            # Find the mock heos parameter.
            if "mock_device" in kwargs:
                mock_device = cast(MockHeosDevice, kwargs["mock_device"])
            elif "heos" in kwargs:
                mock_device = cast(MockHeosDevice, kwargs["heos"].device)
            elif "group" in kwargs:
                mock_device = cast(MockHeosDevice, kwargs["group"]._heos.device)
            elif "player" in kwargs:
                mock_device = cast(MockHeosDevice, kwargs["player"]._heos.device)
            elif "media_music_source" in kwargs:
                mock_device = cast(
                    MockHeosDevice, kwargs["media_music_source"]._heos.device
                )
            elif "media_item_device" in kwargs:
                mock_device = cast(
                    MockHeosDevice, kwargs["media_item_device"]._heos.device
                )
            elif "media_item_song" in kwargs:
                mock_device = cast(
                    MockHeosDevice, kwargs["media_item_song"]._heos.device
                )
            else:
                raise ValueError(
                    "The mock device must be accessible through one of the fixture parameters."
                )

            # Register commands
            assert_list: list[Callable] = []

            for command in matched_commands:
                # Get the fixture command
                fixture_data = json.loads(await get_fixture(command.fixture))
                command_name = fixture_data[const.ATTR_HEOS][const.ATTR_COMMAND]

                # Resolve command arguments (they may contain a ArgumentValue)
                resolved_args = command.get_resolve_args(kwargs)

                mock_device.register(
                    command_name, resolved_args, command.fixture, replace=True
                )

                # Store item to assert later (so we don't need to keep a copy of the resolved args)
                if command.assert_called:
                    assert_list.append(
                        lambda: mock_device.assert_command_called(
                            command_name, resolved_args
                        )
                    )

            # Call the wrapped method
            result = await func(*args, **kwargs)

            # Assert the commands were called
            for callable in assert_list:
                callable()

            return result

        return wrapped

    return wrapper


def value(
    *,
    value: Any | None = None,
    arg_name: str | None = None,
    formatter: str | None = None,
) -> ArgumentValue:
    """Define a value source."""
    return ArgumentValue(value=value, arg_name=arg_name, formatter=formatter)


def calls_command(
    fixture: str,
    command_args: dict[str, Any],
    assert_called: bool = True,
    when: dict[str, Any] | None = None,
) -> Callable:
    """
    Decorator that registers a command prior to test execution.

    Args:
        fixture: The name of the json fixture to load. The command will be determiend from this file.
        command_args: The arguments that are expected to be passed. If set to None, any argument combination is accepted.
        when: Only registers the command if the test method arguments match the provided values.
        assert_called: Assert the command was called after test execution. The default is True.
    """
    return calls_commands(CallCommand(fixture, command_args, when, assert_called))


async def get_fixture(file: str) -> str:
    """Load a fixtures file."""
    file_name = f"tests/fixtures/{file}.json"
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(FILE_IO_POOL, lambda: read_file(file_name))


@functools.lru_cache
def read_file(file_name: str) -> str:
    with open(file_name, encoding="utf-8") as open_file:
        return open_file.read()


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

            # Special processing for known/unknown commands
            if command == const.COMMAND_REGISTER_FOR_CHANGE_EVENTS:
                enable = str(query[const.ATTR_ENABLE])
                log.is_registered_for_events = enable == const.VALUE_ON
                response = (await get_fixture(fixture_name)).replace("{enable}", enable)
            else:
                response = (
                    (await get_fixture("unknown_command"))
                    .replace("{command}", command)
                    .replace("{full_command}", result)
                )

            # write the response
            writer.write((response + SEPARATOR).encode())
            await writer.drain()

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
