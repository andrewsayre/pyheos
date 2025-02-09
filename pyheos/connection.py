"""Define the connection module."""

import asyncio
import logging
from collections.abc import Awaitable, Callable, Coroutine
from contextlib import suppress
from datetime import datetime, timedelta
from typing import TYPE_CHECKING, Any, Final

from pyheos.command import COMMAND_HEART_BEAT, COMMAND_REBOOT
from pyheos.message import HeosCommand, HeosMessage
from pyheos.types import ConnectionState

from .error import CommandError, CommandFailedError, HeosError

CLI_PORT: Final = 1255
SEPARATOR: Final = "\r\n"
SEPARATOR_BYTES: Final = SEPARATOR.encode()
MAX_RECONNECT_DELAY = 600

_LOGGER: Final = logging.getLogger(__name__)


class ConnectionBase:
    """
    Define a base class for HEOS connections.

    This class manages the connection with the HEOS devices, processes commands, and resets when failed.
    """

    def __init__(self, host: str, *, timeout: float) -> None:
        """Init a new instance of the ConnectionBase."""
        self._host: str = host
        self._timeout: float = timeout
        self._state: ConnectionState = ConnectionState.DISCONNECTED
        self._writer: asyncio.StreamWriter | None = None
        self._pending_command_event = ResponseEvent()
        self._running_tasks: set[asyncio.Task[None]] = set()
        self._last_activity: datetime = datetime.now()
        self._command_lock = asyncio.Lock()

        self._on_event_callbacks: list[Callable[[HeosMessage], Awaitable[None]]] = []
        self._on_connected_callbacks: list[Callable[[], Awaitable[None]]] = []
        self._on_disconnected_callbacks: list[Callable[[bool], Awaitable[None]]] = []
        self._on_command_error_callbacks: list[
            Callable[[CommandFailedError], Awaitable[None]]
        ] = []

    @property
    def state(self) -> ConnectionState:
        """Get the current state of the connection."""
        return self._state

    def add_on_event(self, callback: Callable[[HeosMessage], Awaitable[None]]) -> None:
        """Add a callback to be invoked when an event is received."""
        self._on_event_callbacks.append(callback)

    async def _on_event(self, message: HeosMessage) -> None:
        """Handle an HEOS message that is an event."""
        for callback in self._on_event_callbacks:
            await callback(message)

    def add_on_connected(self, callback: Callable[[], Awaitable[None]]) -> None:
        """Add a callback to be invoked when connected."""
        self._on_connected_callbacks.append(callback)

    async def _on_connected(self) -> None:
        """Handle when the connection is established."""
        for callback in self._on_connected_callbacks:
            await callback()

    def add_on_disconnected(self, callback: Callable[[bool], Awaitable[None]]) -> None:
        """Add a callback to be invoked when connected."""
        self._on_disconnected_callbacks.append(callback)

    async def _on_disconnected(self, due_to_error: bool = False) -> None:
        """Handle when the connection is lost. Invoked after the connection has been reset."""
        for callback in self._on_disconnected_callbacks:
            await callback(due_to_error)

    def add_on_command_error(
        self, callback: Callable[[CommandFailedError], Awaitable[None]]
    ) -> None:
        """Add a callback to be invoked when a command error occurs."""
        self._on_command_error_callbacks.append(callback)

    async def _on_command_error(self, error: CommandFailedError) -> None:
        """Handle when a command failed error occurs."""
        for callback in self._on_command_error_callbacks:
            await callback(error)

    def _register_task(
        self, future: Coroutine[Any, Any, None], name: str | None = None
    ) -> None:
        """Register a task that is running in the background, so it can be canceled and reset later."""
        task: asyncio.Task[None] = asyncio.create_task(future, name=name)
        self._running_tasks.add(task)
        task.add_done_callback(self._running_tasks.discard)

    async def _reset(self) -> None:
        """Reset the state of the connection."""
        # Stop running tasks and clear list
        while self._running_tasks:
            task = self._running_tasks.pop()
            if task.cancel():
                with suppress(asyncio.CancelledError):
                    await task
        # Close the writer
        if self._writer:
            self._writer.close()
            with suppress(OSError, asyncio.CancelledError):
                await self._writer.wait_closed()
            self._writer = None
        # Reset other parameters
        self._pending_command_event.clear()
        self._last_activity = datetime.now()
        self._state = ConnectionState.DISCONNECTED

    async def _disconnect_from_error(self, error: Exception) -> None:
        """Disconnect and reset as an of an error."""
        await self._reset()
        _LOGGER.debug(
            "Disconnected from %s due to error: %s: %s",
            self._host,
            type(error).__name__,
            error,
        )
        await self._on_disconnected(due_to_error=True)

    async def _read_handler(self, reader: asyncio.StreamReader) -> None:
        """Reads messages from the open connection and routes to the handler."""
        while True:
            try:
                binary_result = await reader.readuntil(SEPARATOR_BYTES)
            except (asyncio.IncompleteReadError, RuntimeError, OSError) as error:
                await self._disconnect_from_error(error)
                return
            else:
                self._last_activity = datetime.now()
                self._handle_message(
                    HeosMessage._from_raw_message(binary_result.decode())
                )

    def _handle_message(self, message: HeosMessage) -> None:
        """Handle a message received from the HEOS device."""
        if message.is_under_process:
            _LOGGER.debug("Command under process '%s'", message.command)
            return
        if message.is_event:
            _LOGGER.debug("Event received: '%s': '%s'", message.command, message)
            self._register_task(self._on_event(message), "Event Handler")
            return

        # Set the message on the pending command.
        if not self._pending_command_event.set(message):
            _LOGGER.debug(
                "Unexpected response received: '%s': '%s'", message.command, message
            )

    async def command(self, command: HeosCommand) -> HeosMessage:
        """Send a command to the HEOS device."""

        # Encapsulate the core logic so that we can wrap it in a lock.
        async def _command_impl() -> HeosMessage:
            """Implementation of the command."""
            if self._state is not ConnectionState.CONNECTED:
                _LOGGER.debug("Command failed '%s': Not connected to device", command)
                raise CommandError(command.command, "Not connected to device")
            if TYPE_CHECKING:
                assert self._writer is not None

            # Send the command
            try:
                self._writer.write((command.uri + SEPARATOR).encode())
                await self._writer.drain()
            except (ConnectionError, OSError, AttributeError) as error:
                # Occurs when the connection is broken. Run in the background to ensure connection is reset.
                _LOGGER.debug(
                    "Command failed '%s': %s: %s", command, type(error).__name__, error
                )
                self._register_task(
                    self._disconnect_from_error(error), "Disconnect From Error"
                )
                raise CommandError(
                    command.command, f"Command failed: {error}"
                ) from error
            else:
                self._last_activity = datetime.now()

            # If the command is a reboot, we won't get a response.
            if command.command == COMMAND_REBOOT:
                _LOGGER.debug("Command executed '%s': No response", command)
                return HeosMessage(COMMAND_REBOOT)

            # Wait for the response with a timeout
            try:
                response = await asyncio.wait_for(
                    self._pending_command_event.wait(command.command), self._timeout
                )
            except asyncio.TimeoutError as error:
                # Occurs when the command times out
                _LOGGER.debug("Command timed out '%s'", command)
                raise CommandError(command.command, "Command timed out") from error
            finally:
                self._pending_command_event.clear()

            # Check the result
            if not response.result:
                _LOGGER.debug("Command failed '%s': '%s'", command, response)
                raise CommandFailedError._from_message(response)

            _LOGGER.debug("Command executed '%s': '%s'", command, response)
            return response

        # Run the within the lock
        command_error: CommandFailedError | None = None
        await self._command_lock.acquire()
        try:
            return await _command_impl()
        except CommandFailedError as error:
            command_error = error
            raise  # Re-raise to send the error to the caller.
        finally:
            self._command_lock.release()
            if command_error:
                await self._on_command_error(command_error)

    async def connect(self) -> None:
        """Connect to the HEOS device."""
        if self._state is ConnectionState.CONNECTED:
            return
        # Open the connection to the host
        try:
            reader, self._writer = await asyncio.wait_for(
                asyncio.open_connection(self._host, CLI_PORT), self._timeout
            )
        except asyncio.TimeoutError as err:
            _LOGGER.debug("Failed to connect to %s: Connection timed out", self._host)
            raise HeosError("Connection timed out") from err
        except (OSError, ConnectionError) as err:
            _LOGGER.debug(
                "Failed to connect to %s: %s: %s", self._host, type(err).__name__, err
            )
            raise HeosError(
                f"Unable to connect to {self._host}: {type(err).__name__}: {err}"
            ) from err

        # Start read handler
        self._register_task(self._read_handler(reader), "Read Handler")
        self._last_activity = datetime.now()
        self._state = ConnectionState.CONNECTED
        _LOGGER.debug("Connected to %s", self._host)
        await self._on_connected()

    async def disconnect(self) -> None:
        """Disconnect from the HEOS device."""
        await self._reset()
        _LOGGER.debug("Disconnected from %s", self._host)
        await self._on_disconnected()


class AutoReconnectingConnection(ConnectionBase):
    """
    Define a class that manages the connection state and automatically reconnects on failure.

    This class adds heartbeat functionality and auto-reconnect logic.
    """

    def __init__(
        self,
        host: str,
        *,
        timeout: float,
        reconnect: bool = True,
        reconnect_delay: float,
        reconnect_max_attempts: int,
        heart_beat: bool = True,
        heart_beat_interval: float,
    ) -> None:
        """Init a new instance of the AutoReconnectingConnection class."""
        super().__init__(host, timeout=timeout)
        self._reconnect = reconnect
        self._reconnect_delay = reconnect_delay
        self._reconnect_max_attempts = reconnect_max_attempts
        self._heart_beat = heart_beat
        self._heart_beat_interval = heart_beat_interval
        self._heart_beat_interval_delta = timedelta(seconds=heart_beat_interval)

    async def _heart_beat_handler(self) -> None:
        """
        Send heart beat command to the device at the heart beat interval.

        This effectively tests that the connection to the device is still alive. If the heart beat
        fails or times out, the existing command processing logic will reset the state of the connection.
        """
        while self._state == ConnectionState.CONNECTED:
            last_acitvity_delta = datetime.now() - self._last_activity
            if last_acitvity_delta >= self._heart_beat_interval_delta:
                with suppress(CommandError):
                    await self.command(HeosCommand(COMMAND_HEART_BEAT))
            # Sleep until next interval
            await asyncio.sleep(self._heart_beat_interval)

    async def _attempt_reconnect(self) -> None:
        """Attempt to reconnect after disconnection from error."""
        self._state = ConnectionState.RECONNECTING
        attempts = 0
        unlimited_attempts = self._reconnect_max_attempts == 0
        delay = min(self._reconnect_delay, MAX_RECONNECT_DELAY)
        while (attempts < self._reconnect_max_attempts) or unlimited_attempts:
            _LOGGER.debug("Waiting %s seconds before attempting to reconnect", delay)
            await asyncio.sleep(delay)
            _LOGGER.debug("Attempting reconnect #%s to %s", (attempts + 1), self._host)
            try:
                await self.connect()
            except HeosError:
                attempts += 1
                delay = min(delay * 2, MAX_RECONNECT_DELAY)
            else:
                return

    async def _on_connected(self) -> None:
        """Handle when the connection is established."""
        # Start heart beat when enabled
        if self._heart_beat:
            self._register_task(self._heart_beat_handler(), "Heart Beat")
        await super()._on_connected()

    async def _on_disconnected(self, due_to_error: bool = False) -> None:
        """Handle when the connection is lost. Invoked after the connection has been reset."""
        if due_to_error and self._reconnect:
            self._register_task(self._attempt_reconnect(), "Reconnect")
        await super()._on_disconnected(due_to_error)


class ResponseEvent:
    """Define an awaitable command event response."""

    def __init__(self) -> None:
        """Init a new instance of the CommandEvent."""
        self._event: asyncio.Event = asyncio.Event()
        self._response: HeosMessage | None = None
        self._target_command: str | None = None

    async def wait(self, target_command: str) -> HeosMessage:
        """Wait until the event is set."""
        self._target_command = target_command
        await self._event.wait()
        if TYPE_CHECKING:
            assert self._response is not None
        return self._response

    def set(self, response: HeosMessage) -> bool:
        """Set the response."""
        if self._target_command is None or self._target_command != response.command:
            return False
        self._target_command = None
        self._response = response
        self._event.set()
        return True

    def clear(self) -> None:
        """Clear the event."""
        self._response = None
        self._target_command = None
        self._event.clear()
