"""Tests for the pyheos library."""

import asyncio
import functools
import json
from collections.abc import Callable, Sequence
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from typing import Any, cast
from urllib.parse import parse_qsl, quote_plus, urlencode, urlparse

from pyheos import Heos
from pyheos import command as c
from pyheos.connection import CLI_PORT, SEPARATOR, SEPARATOR_BYTES

FILE_IO_POOL = ThreadPoolExecutor()


@dataclass
class CallCommand:
    """Define a command call.

    Args:
        fixture: The name of the json fixture to load. The command will be determiend from this file.
        command_args: The arguments that are expected to be passed. If set to None, any argument combination is accepted.
        when: Only registers the command if the test method arguments match the provided values.
        replace: Replace any existing command matchers. The default is False.
        assert_called: Assert the command was called after test execution. The default is True.
        add_command_under_process: When True, the under process response will be sent prior to the command response.
    """

    fixture: str
    command_args: dict[str, Any] | None = None
    when: dict[str, Any] | None = None
    replace: bool = False
    assert_called: bool = True
    add_command_under_process: bool = False

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
            return c.VALUE_ON if arg_value else c.VALUE_OFF
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
                mock_device = cast(MockHeosDevice, kwargs["group"].heos.device)
            elif "player" in kwargs:
                mock_device = cast(MockHeosDevice, kwargs["player"].heos.device)
            elif "media_music_source" in kwargs:
                mock_device = cast(
                    MockHeosDevice, kwargs["media_music_source"].heos.device
                )
            elif "media_item_device" in kwargs:
                mock_device = cast(
                    MockHeosDevice, kwargs["media_item_device"].heos.device
                )
            elif "media_item_song" in kwargs:
                mock_device = cast(
                    MockHeosDevice, kwargs["media_item_song"].heos.device
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
                command_name = fixture_data[c.ATTR_HEOS][c.ATTR_COMMAND]

                # Resolve command arguments (they may contain a ArgumentValue)
                resolved_args = command.get_resolve_args(kwargs)

                fixtures: list[str] = [command.fixture]
                if command.add_command_under_process:
                    fixtures.insert(0, "other.command_under_process")

                matcher = mock_device.register(
                    command_name,
                    resolved_args,
                    fixtures,
                    replace=command.replace,
                )

                # Store item to assert later (so we don't need to keep a copy of the resolved args)
                if command.assert_called:
                    assert_list.append(matcher.assert_called)

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
    command_args: dict[str, Any] | None = None,
    assert_called: bool = True,
    when: dict[str, Any] | None = None,
    replace: bool = False,
    add_command_under_process: bool = False,
) -> Callable:
    """
    Decorator that registers a command prior to test execution.

    Args:
        fixture: The name of the json fixture to load. The command will be determiend from this file.
        command_args: The arguments that are expected to be passed. If set to None, any argument combination is accepted.
        when: Only registers the command if the test method arguments match the provided values.
        assert_called: Assert the command was called after test execution. The default is True.
        replace: Replace any existing command matchers. The default is False.
        add_command_under_process: When True, the under process response will be sent prior to the command response.
    """
    return calls_commands(
        CallCommand(
            fixture,
            command_args,
            when,
            replace,
            assert_called,
            add_command_under_process,
        )
    )


def calls_player_commands(
    player_ids: Sequence[int] = (1, 2), *additional: CallCommand
) -> Callable:
    """
    Decorator that registers player commands and any optional additional commands.
    """
    commands = [
        CallCommand("player.get_players"),
    ]
    for player_id in player_ids:
        commands.extend(
            [
                CallCommand("player.get_play_state", {c.ATTR_PLAYER_ID: player_id}),
                CallCommand(
                    "player.get_now_playing_media", {c.ATTR_PLAYER_ID: player_id}
                ),
                CallCommand("player.get_volume", {c.ATTR_PLAYER_ID: player_id}),
                CallCommand("player.get_mute", {c.ATTR_PLAYER_ID: player_id}),
                CallCommand("player.get_play_mode", {c.ATTR_PLAYER_ID: player_id}),
            ]
        )
    commands.extend(additional)
    return calls_commands(*commands)


def calls_group_commands(*additional: CallCommand) -> Callable:
    commands = [
        CallCommand("group.get_groups"),
        CallCommand("group.get_volume", {c.ATTR_GROUP_ID: 1}),
        CallCommand("group.get_mute", {c.ATTR_GROUP_ID: 1}),
    ]
    commands.extend(additional)
    return calls_commands(*commands)


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
            self._handle_connection, "127.0.0.1", CLI_PORT
        )

        self.register(c.COMMAND_ACCOUNT_CHECK, None, "system.check_account")

    async def stop(self) -> None:
        """Stop the heos server."""
        if not self._started:
            return
        self._started = False

        # Stop the server
        assert self._server is not None
        self._server.close()

        # Disconnect all connections
        for connection in self.connections:
            await connection.disconnect()
        self.connections.clear()

        # Wait for server to close
        await self._server.wait_closed()

    async def write_event(
        self, fixture: str, replacements: dict[str, Any] | None = None
    ) -> None:
        """Send an event through the event channel.

        Args:
            fixture: The name of the fixture to send.
            replacements: The replacements to apply to the fixture.
        """
        event = await get_fixture(fixture)
        if replacements:
            for key, value in replacements.items():
                event = event.replace("{" + key + "}", str(value))
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
    ) -> "CommandMatcher":
        """Register a matcher."""
        if replace:
            self._matchers = [m for m in self._matchers if m.command != command]
        if isinstance(responses, str):
            responses = [responses]
        matcher = CommandMatcher(command, args, responses)
        self._matchers.append(matcher)
        return matcher

    def assert_command_called(
        self, target_command: str, target_args: dict[str, Any] | None = None
    ) -> None:
        """
        Assert that the commands were called.

        Args:
            command: The command to check.
            args: The arguments to check. If None, only the command is checked.
        """
        for matcher in self._matchers:
            if matcher.is_match(target_command, target_args, increment=False):
                matcher.assert_called()
                return
        assert False, (
            f"Command was not registered: {target_command} with args {target_args}."
        )

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
            if command == c.COMMAND_REBOOT:
                # Simulate a reboot by shutting down the server
                await self.stop()
                await asyncio.sleep(0.3)
                await self.start()
                return
            if command == c.COMMAND_REGISTER_FOR_CHANGE_EVENTS:
                enable = str(query[c.ATTR_ENABLE])
                log.is_registered_for_events = enable == c.VALUE_ON
                response = (await get_fixture(fixture_name)).replace("{enable}", enable)
            else:
                response = (
                    (await get_fixture("other.unknown_command"))
                    .replace("{command}", command)
                    .replace("{full_command}", quote_plus(result))
                )

            # write the response
            writer.write((response + SEPARATOR).encode())
            await writer.drain()

        try:
            self.connections.remove(log)
        except ValueError:
            pass


@dataclass
class CommandMatcher:
    """Define a command match response."""

    command: str
    _args: dict[str, Any] | None = field(default_factory=dict)
    responses: list[str] = field(default_factory=list)
    match_count: int = field(default=0, init=False)

    @functools.cached_property
    def args(self) -> dict[str, str] | None:
        if self._args is None:
            return None
        return CommandMatcher._convert_dict_to_strings(self._args)

    @staticmethod
    def _convert_dict_to_strings(args: dict[str, Any]) -> dict[str, str]:
        return {key: str(value) for key, value in args.items()}

    def is_match(
        self,
        match_command: str,
        match_args: dict[str, Any] | None = None,
        increment: bool = True,
    ) -> bool:
        """Determine if the command matches the target."""
        if self.command != match_command:
            return False
        if match_args is not None and self.args is not None:
            if not self.args == CommandMatcher._convert_dict_to_strings(match_args):
                return False
        if increment:
            self.match_count += 1
        return True

    async def get_response(self, query: dict) -> list[str]:
        """Get the response body."""
        responses = []
        for fixture in self.responses:
            responses.append(await self._get_response(fixture, query))
        return responses

    async def _get_response(self, response: str, query: dict) -> str:
        response = await get_fixture(response)
        keys = {
            c.ATTR_PLAYER_ID: "{player_id}",
            c.ATTR_STATE: "{state}",
            c.ATTR_LEVEL: "{level}",
            c.ATTR_OPTIONS: "{options}",
        }
        for key, token in keys.items():
            value = query.get(key)
            if value is not None and token in response:
                response = response.replace(token, quote_plus(value))

        response = response.replace("{command}", self.command)
        response = response.replace("{parameters}", urlencode(query))

        return response

    def assert_called(self) -> None:
        """Assert that the command was called."""
        assert self.match_count, (
            f"Command {self.command} was not called with arguments {self._args}."
        )


class ConnectionLog:
    """Define a connection log."""

    def __init__(
        self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter
    ) -> None:
        """Initialize the connection log."""
        self._reader = reader
        self._writer = writer
        self.is_registered_for_events = False

    async def disconnect(self) -> None:
        """Close the connection."""
        self._writer.close()
        try:
            await self._writer.wait_closed()
        except ConnectionError:
            pass

    async def write(self, payload: str) -> None:
        """Write the payload to the stream."""
        data = (payload + SEPARATOR).encode()
        self._writer.write(data)
        await self._writer.drain()
