"""Define the connection module."""

import asyncio
import json
import logging
from collections import defaultdict
from collections.abc import Coroutine
from datetime import datetime, timedelta
from typing import TYPE_CHECKING, Any, Final, Optional

from . import const
from .command import HeosCommands
from .error import CommandError, HeosError, format_error_message
from .response import HeosResponse

if TYPE_CHECKING:
    from .heos import Heos

SEPARATOR: Final = "\r\n"
SEPARATOR_BYTES: Final = SEPARATOR.encode()

_LOGGER: Final = logging.getLogger(__name__)

_QUOTE_MAP: Final = {"&": "%26", "=": "%3D", "%": "%25"}
_MASKED_PARAMS: Final = {"pw"}
_MASK: Final = "********"


def _quote(string: str) -> str:
    """Quote a string per the CLI specification."""
    return "".join([_QUOTE_MAP.get(char, char) for char in str(string)])


def _encode_query(items: dict[str, str], *, mask: bool = False) -> str:
    """Encode a dict to query string per CLI specifications."""
    pairs = []
    for key in sorted(items.keys()):
        value = _MASK if mask and key in _MASKED_PARAMS else items[key]
        item = f"{key}={_quote(value)}"
        # Ensure 'url' goes last per CLI spec
        if key == "url":
            pairs.append(item)
        else:
            pairs.insert(0, item)
    return "&".join(pairs)


class HeosConnection:
    """Define a class that encapsulates read/write."""

    def __init__(
        self,
        heos: "Heos",
        host: str,
        *,
        timeout: float = const.DEFAULT_TIMEOUT,
        heart_beat: Optional[float] = const.DEFAULT_HEART_BEAT,
        all_progress_events: bool = True,
    ) -> None:
        """Init a new HeosConnection class."""
        self._heos = heos
        self._all_progress_events = all_progress_events
        self.host: str = host
        self.commands = HeosCommands(self)
        self.timeout: float = timeout
        self._reader: asyncio.StreamReader | None = None
        self._writer: asyncio.StreamWriter | None = None
        self._response_handler_task: asyncio.Task | None = None
        self._pending_commands: defaultdict[str, list[ResponseEvent]] = defaultdict(
            list
        )
        self._sequence: int = 0
        self._state: str = const.STATE_DISCONNECTED
        self._auto_reconnect: bool = False
        self._reconnect_delay: float = const.DEFAULT_RECONNECT_DELAY
        self._reconnect_task: asyncio.Task | None = None
        self._last_activity: datetime = datetime.now()
        self._heart_beat_interval: float | None = heart_beat
        self._heart_beat_task: asyncio.Task | None = None

    async def connect(
        self,
        *,
        auto_reconnect: bool = False,
        reconnect_delay: float = const.DEFAULT_RECONNECT_DELAY,
    ) -> None:
        """Invoke the connect operation."""
        if self._state == const.STATE_CONNECTED:
            return
        # Ensure we don't try to reconnect during initial failures
        self._auto_reconnect = False
        await self._connect()
        self._auto_reconnect = auto_reconnect
        self._reconnect_delay = reconnect_delay

    async def _connect(self) -> None:
        """Perform core connection logic."""
        try:
            open_future: Coroutine = asyncio.open_connection(self.host, const.CLI_PORT)
            self._reader, self._writer = await asyncio.wait_for(
                open_future, self.timeout
            )
        except (OSError, ConnectionError, asyncio.TimeoutError) as err:
            raise HeosError(format_error_message(err)) from err
        # Start response handler
        self._response_handler_task = asyncio.ensure_future(self._response_handler())
        # Set state before calling command as it checks for handling
        self._state = const.STATE_CONNECTED
        await self.commands.register_for_change_events()
        # Start heart beat if enabled.
        if self._heart_beat_interval is not None and self._heart_beat_interval > 0:
            self._heart_beat_task = asyncio.ensure_future(self._heart_beat())

        _LOGGER.debug("Connected to %s", self.host)
        self._heos.dispatcher.send(const.SIGNAL_HEOS_EVENT, const.EVENT_CONNECTED)

    async def disconnect(self) -> None:
        """Disconnect from the device."""
        if self._state == const.STATE_DISCONNECTED:
            return
        # Cancel pending reconnect
        if self._reconnect_task:
            self._reconnect_task.cancel()
            await self._reconnect_task
            self._reconnect_task = None
        # Core disconnect
        await self._disconnect()
        self._state = const.STATE_DISCONNECTED

        _LOGGER.debug("Disconnected from %s", self.host)
        self._heos.dispatcher.send(const.SIGNAL_HEOS_EVENT, const.EVENT_DISCONNECTED)

    async def _disconnect(self) -> None:
        # Cancel response handler
        if self._heart_beat_task:
            self._heart_beat_task.cancel()
            try:
                await self._heart_beat_task
            except asyncio.CancelledError:
                pass
            self._heart_beat_task = None
        if self._response_handler_task:
            self._response_handler_task.cancel()
            await self._response_handler_task
            self._response_handler_task = None
        # Close channel
        if self._writer:
            self._writer.close()
            self._writer = None
        self._reader = None
        self._sequence = 0
        self._pending_commands.clear()

    async def _handle_connection_error(self, error: Exception) -> None:
        """Handle connection failures and schedule reconnect."""
        if self._reconnect_task:
            return

        await self._disconnect()

        if self._auto_reconnect:
            self._state = const.STATE_RECONNECTING
            self._reconnect_task = asyncio.ensure_future(self._reconnect())
        else:
            self._state = const.STATE_DISCONNECTED

        _LOGGER.debug("Disconnected from %s: %s", self.host, error)
        self._heos.dispatcher.send(const.SIGNAL_HEOS_EVENT, const.EVENT_DISCONNECTED)

    async def _reconnect(self) -> None:
        """Perform core reconnection logic."""
        while self._state != const.STATE_CONNECTED:
            try:
                await self._connect()
                self._reconnect_task = None
                return
            except HeosError as err:
                # Occurs when we could not reconnect
                # Set state to reconnecting since _connect may have set it to connected and failed after
                self._state = const.STATE_RECONNECTING
                _LOGGER.debug("Failed to reconnect to %s: %s", self.host, err)
                await self._disconnect()
                await asyncio.sleep(self._reconnect_delay)
            except asyncio.CancelledError:
                # Occurs when reconnect is cancelled via disconnect
                return

    async def _response_handler(self) -> None:
        while self._reader:
            # Wait for response
            try:
                result = await self._reader.readuntil(SEPARATOR_BYTES)
                self._last_activity = datetime.now()
                data = json.loads(result.decode())
                response = HeosResponse(data)

                # Ignore processing
                if response.is_under_process:
                    _LOGGER.debug(
                        "Command under process '%s': '%s'", response.command, data
                    )
                    continue
                # Handle events
                if response.is_event:
                    asyncio.ensure_future(self._handle_event(response))
                    continue
                # Find pending command
                commands = self._pending_commands[response.command]
                if not commands:
                    _LOGGER.debug(
                        "Received response with no pending command: '%s'",
                        response.command,
                    )
                    continue
                sequence = response.get_message("sequence")
                if sequence:
                    sequence_id = int(sequence)
                    event = next(
                        (event for event in commands if event.sequence == sequence_id)
                    )
                    commands.remove(event)
                else:
                    event = commands.pop(0)
                event.set(response)

            except asyncio.CancelledError:
                # Occurs when the task is being killed
                return
            except (
                ConnectionError,
                asyncio.IncompleteReadError,
                RuntimeError,
                OSError,
            ) as error:
                # Occurs when the connection breaks
                asyncio.ensure_future(self._handle_connection_error(error))
                return

    async def _heart_beat(self) -> None:
        if TYPE_CHECKING:
            assert self._heart_beat_interval is not None
        while self._state == const.STATE_CONNECTED:
            last_activity = datetime.now() - self._last_activity
            threshold = timedelta(seconds=self._heart_beat_interval)
            if last_activity > threshold:
                try:
                    await self.commands.heart_beat()
                except CommandError:
                    pass
            await asyncio.sleep(float(self._heart_beat_interval) / 2)

    async def command(
        self, command: str, params: dict[str, Any] | None = None
    ) -> HeosResponse:
        """Execute a command and get it's response."""
        # Build command URI
        sequence = self._sequence
        self._sequence += 1
        params = params or {}
        params["sequence"] = sequence
        uri = f"{const.BASE_URI}{command}?{_encode_query(params)}"
        masked_uri = f"{const.BASE_URI}{command}?{_encode_query(params, mask=True)}"

        if self._state != const.STATE_CONNECTED or self._writer is None:
            _LOGGER.debug(
                "Command failed '%s': %s", masked_uri, "Not connected to device"
            )
            raise CommandError(command, "Not connected to device")

        # Add reservation
        event = ResponseEvent(sequence)
        self._pending_commands[command].append(event)
        # Send command
        try:
            self._writer.write((uri + SEPARATOR).encode())
            await self._writer.drain()
            response = await asyncio.wait_for(event.wait(), self.timeout)
        except (
            ConnectionError,
            asyncio.TimeoutError,
            OSError,
            AttributeError,
        ) as error:
            # Occurs when the connection breaks
            asyncio.ensure_future(self._handle_connection_error(error))
            message = format_error_message(error)
            _LOGGER.debug("Command failed '%s': %s", masked_uri, message)
            raise CommandError(command, message) from error

        if response.result:
            _LOGGER.debug("Command executed '%s': '%s'", masked_uri, response)
        else:
            _LOGGER.debug("Command failed '%s': %s", masked_uri, response)
        response.raise_for_result()
        return response

    async def _handle_event(self, response: HeosResponse) -> None:
        """Handle a response event."""
        if response.command in const.PLAYER_EVENTS:
            player_id = response.get_player_id()
            player = self._heos.players.get(player_id)
            if player and (
                await player.event_update(response, self._all_progress_events)
            ):
                self._heos.dispatcher.send(
                    const.SIGNAL_PLAYER_EVENT, player_id, response.command
                )
                _LOGGER.debug("Event received for player %s: %s", player, response)
        elif response.command in const.GROUP_EVENTS:
            group_id = response.get_group_id()
            group = self._heos.groups.get(group_id)
            if group:
                await group.event_update(response)
                self._heos.dispatcher.send(
                    const.SIGNAL_GROUP_EVENT, group_id, response.command
                )
                _LOGGER.debug("Event received for group %s: %s", group_id, response)
        elif response.command in const.HEOS_EVENTS:
            # pylint: disable=protected-access
            result = await self._heos._handle_event(response)
            self._heos.dispatcher.send(
                const.SIGNAL_CONTROLLER_EVENT, response.command, result
            )
            _LOGGER.debug("Event received: %s", response)
        else:
            _LOGGER.debug("Unrecognized event: %s", response)

    @property
    def state(self) -> str:
        """Get the current state of the connection."""
        return self._state


class ResponseEvent:
    """Define an awaitable command event response."""

    def __init__(self, sequence: int) -> None:
        """Init a new instance of the CommandEvent."""
        self._event: asyncio.Event = asyncio.Event()
        self._sequence: int = sequence
        self._response: HeosResponse | None = None

    @property
    def sequence(self) -> int:
        """Get the sequence that represents this event."""
        return self._sequence

    async def wait(self) -> HeosResponse:
        """Wait until the event is set."""
        await self._event.wait()
        if TYPE_CHECKING:
            assert self._response is not None
        return self._response

    def set(self, response: HeosResponse) -> None:
        """Set the response."""
        if response is None:
            raise ValueError("Response must not be None")
        self._response = response
        self._event.set()
