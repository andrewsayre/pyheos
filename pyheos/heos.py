"""Define the heos manager module."""

import logging
from typing import Any, Final

from pyheos.command import COMMAND_SIGN_IN
from pyheos.command.browse import BrowseCommands
from pyheos.command.group import GroupCommands
from pyheos.command.player import PlayerCommands
from pyheos.command.system import SystemCommands
from pyheos.dispatch import (
    CallbackType,
    ControllerEventCallbackType,
    DisconnectType,
    EventCallbackType,
    callback_wrapper,
)
from pyheos.error import CommandAuthenticationError, CommandFailedError
from pyheos.message import HeosMessage
from pyheos.options import HeosOptions
from pyheos.player import PlayerUpdateResult
from pyheos.system import HeosSystem

from . import command as c
from . import const
from .dispatch import Dispatcher
from .types import (
    ConnectionState,
    SignalHeosEvent,
    SignalType,
)

_LOGGER: Final = logging.getLogger(__name__)


class Heos(SystemCommands, BrowseCommands, GroupCommands, PlayerCommands):
    """The Heos class provides access to the CLI API."""

    @classmethod
    async def create_and_connect(cls, host: str, **kwargs: Any) -> "Heos":
        """
        Create a new instance of the Heos CLI API and connect.

        Args:
            host: A host name or IP address of a HEOS-capable device.
            timeout: The timeout in seconds for opening a connectoin and issuing commands to the device.
            events: Set to True to enable event updates, False to disable. The default is True.
            all_progress_events: Set to True to receive media progress events, False to only receive media changed events. The default is True.
            dispatcher: The dispatcher instance to use for event callbacks. If not provided, an internally created instance will be used.
            auto_reconnect: Set to True to automatically reconnect if the connection is lost. The default is False. Used in conjunction with auto_reconnect_delay.
            auto_reconnect_delay: The delay in seconds before attempting to reconnect. The default is 10 seconds. Used in conjunction with auto_reconnect.
            auto_reconnect_max_attempts: The maximum number of reconnection attempts before giving up. Set to 0 for unlimited attempts. The default is 0 (unlimited).
            heart_beat: Set to True to enable heart beat messages, False to disable. Used in conjunction with heart_beat_delay. The default is True.
            heart_beat_interval: The interval in seconds between heart beat messages. Used in conjunction with heart_beat.
            credentials: credentials to use to automatically sign-in to the HEOS account upon successful connection. If not provided, the account will not be signed in.

        """
        heos = Heos(HeosOptions(host, **kwargs))
        await heos.connect()
        return heos

    @classmethod
    async def validate_connection(cls, host: str) -> HeosSystem:
        """
        Validate the connection to the HEOS device and return information about the HEOS system.

        Args:
            host: A host name or IP address of a HEOS-capable device.
        """
        heos = Heos(HeosOptions(host, events=False, heart_beat=False))
        try:
            await heos.connect()
            return await heos.get_system_info()
        finally:
            await heos.disconnect()

    def __init__(self, options: HeosOptions) -> None:
        """Init a new instance of the Heos CLI API."""
        super(Heos, self).__init__(options)
        self._connection.add_on_connected(self._on_connected)
        self._connection.add_on_disconnected(self._on_disconnected)
        self._connection.add_on_event(self._on_event)
        self._connection.add_on_command_error(self._on_command_error)
        self._dispatcher = options.dispatcher or Dispatcher()

    async def connect(self) -> None:
        """Connect to the CLI."""
        await self._connection.connect()

    async def disconnect(self) -> None:
        """Disconnect from the CLI."""
        await self._connection.disconnect()

    def add_on_controller_event(
        self, callback: ControllerEventCallbackType
    ) -> DisconnectType:
        """Connect a callback to receive controller events.

        Args:
            callback: The callback to receive the controller events.
        Returns:
            A function that disconnects the callback."""
        return self._dispatcher.connect(SignalType.CONTROLLER_EVENT, callback)

    def add_on_heos_event(self, callback: EventCallbackType) -> DisconnectType:
        """Connect a callback to receive HEOS events.

        Args:
            callback: The callback to receive the HEOS events. The callback should accept a single string argument which will contain the event name.
        Returns:
            A function that disconnects the callback."""
        return self._dispatcher.connect(SignalType.HEOS_EVENT, callback)

    def add_on_connected(self, callback: CallbackType) -> DisconnectType:
        """Connect a callback to be invoked when connected.

        Args:
            callback: The callback to be invoked.
        Returns:
            A function that disconnects the callback."""
        return self.add_on_heos_event(
            callback_wrapper(callback, {0: SignalHeosEvent.CONNECTED}),
        )

    def add_on_disconnected(self, callback: CallbackType) -> DisconnectType:
        """Connect a callback to be invoked when disconnected.

        Args:
            callback: The callback to be invoked.
        Returns:
            A function that disconnects the callback."""
        return self.add_on_heos_event(
            callback_wrapper(callback, {0: SignalHeosEvent.DISCONNECTED}),
        )

    def add_on_user_credentials_invalid(self, callback: CallbackType) -> DisconnectType:
        """Connect a callback to be invoked when the user credentials are invalid.

        Args:
            callback: The callback to be invoked.
        Returns:
            A function that disconnects the callback."""
        return self.add_on_heos_event(
            callback_wrapper(callback, {0: SignalHeosEvent.USER_CREDENTIALS_INVALID}),
        )

    async def _on_connected(self) -> None:
        """Handle when connected, which may occur more than once."""
        assert self._connection.state == ConnectionState.CONNECTED

        await self._dispatcher.wait_send(
            SignalType.HEOS_EVENT, SignalHeosEvent.CONNECTED, return_exceptions=True
        )

        if self.current_credentials:
            # Sign-in to the account if provided
            try:
                await self.sign_in(
                    self.current_credentials.username,
                    self.current_credentials.password,
                )
            except CommandAuthenticationError as err:
                _LOGGER.debug(
                    "Failed to sign-in to HEOS Account after connection: %s", err
                )
                self.current_credentials = None
                await self._dispatcher.wait_send(
                    SignalType.HEOS_EVENT,
                    SignalHeosEvent.USER_CREDENTIALS_INVALID,
                    return_exceptions=True,
                )
        else:
            # Determine the logged in user
            await self.check_account()

        await self.register_for_change_events(self._options.events)

        # Refresh players and mark available
        if self._players_loaded:
            await self.load_players()

    async def _on_disconnected(self, from_error: bool) -> None:
        """Handle when disconnected, which may occur more than once."""
        assert self._connection.state == ConnectionState.DISCONNECTED
        # Mark loaded players unavailable
        for player in self.players.values():
            player.available = False
        await self._dispatcher.wait_send(
            SignalType.HEOS_EVENT, SignalHeosEvent.DISCONNECTED, return_exceptions=True
        )

    async def _on_command_error(self, error: CommandFailedError) -> None:
        """Handle when a command error occurs."""
        if (
            isinstance(error, CommandAuthenticationError)
            and error.command != COMMAND_SIGN_IN
        ):
            # If we're managing credentials, clear them
            if self.current_credentials is not None:
                _LOGGER.debug(
                    "HEOS Account credentials are no longer valid: %s",
                    error.error_text,
                    exc_info=error,
                )
            # Ensure a stale credential is cleared
            await self.sign_out()
            await self._dispatcher.wait_send(
                SignalType.HEOS_EVENT,
                SignalHeosEvent.USER_CREDENTIALS_INVALID,
                return_exceptions=True,
            )

    async def _on_event(self, event: HeosMessage) -> None:
        """Handle a heos event."""
        if event.command in const.HEOS_EVENTS:
            await self._on_event_heos(event)
        elif event.command in const.PLAYER_EVENTS:
            await self._on_event_player(event)
        elif event.command in const.GROUP_EVENTS:
            await self._on_event_group(event)
        else:
            _LOGGER.debug("Unrecognized event: %s", event.command)

    async def _on_event_heos(self, event: HeosMessage) -> None:
        """Process a HEOS system event."""
        result: PlayerUpdateResult | None = None
        if event.command == const.EVENT_PLAYERS_CHANGED and self._players_loaded:
            result = await self.load_players()
        if event.command == const.EVENT_SOURCES_CHANGED and self._music_sources_loaded:
            await self.get_music_sources(refresh=True)
        elif event.command == const.EVENT_USER_CHANGED:
            if c.ATTR_SIGNED_IN in event.message:
                self._signed_in_username = event.get_message_value(c.ATTR_USER_NAME)
            else:
                self._signed_in_username = None
        elif event.command == const.EVENT_GROUPS_CHANGED and self._groups_loaded:
            await self.get_groups(refresh=True)

        await self._dispatcher.wait_send(
            SignalType.CONTROLLER_EVENT, event.command, result, return_exceptions=True
        )

    async def _on_event_player(self, event: HeosMessage) -> None:
        """Process an event about a player."""
        player_id = event.get_message_value_int(c.ATTR_PLAYER_ID)
        player = self.players.get(player_id)
        if player and (
            await player._on_event(event, self._options.all_progress_events)
        ):
            await self.dispatcher.wait_send(
                SignalType.PLAYER_EVENT,
                player_id,
                event.command,
                return_exceptions=True,
            )
            _LOGGER.debug("Event received for player %s: %s", player, event.command)

    async def _on_event_group(self, event: HeosMessage) -> None:
        """Process an event about a group."""
        group_id = event.get_message_value_int(c.ATTR_GROUP_ID)
        group = self.groups.get(group_id)
        if group and await group._on_event(event):
            await self.dispatcher.wait_send(
                SignalType.GROUP_EVENT,
                group_id,
                event.command,
                return_exceptions=True,
            )
            _LOGGER.debug("Event received for group %s: %s", group_id, event.command)

    @property
    def dispatcher(self) -> Dispatcher:
        """Get the dispatcher instance."""
        return self._dispatcher
