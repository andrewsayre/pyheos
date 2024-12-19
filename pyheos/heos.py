"""Define the heos manager module."""

import asyncio
import logging
from collections.abc import Sequence
from dataclasses import dataclass, field
from typing import Any, Final, Optional

from pyheos.command import HeosCommands
from pyheos.credentials import Credentials
from pyheos.error import CommandError
from pyheos.message import HeosMessage

from . import const
from .connection import AutoReconnectingConnection
from .dispatch import Dispatcher
from .group import HeosGroup, create_group
from .player import HeosPlayer
from .source import HeosSource, InputSource

_LOGGER: Final = logging.getLogger(__name__)


@dataclass(frozen=True)
class HeosOptions:
    """
    The HeosOptions encapsulates options for connecting to a Heos System.

    Args:
        host: A host name or IP address of a HEOS-capable device.
        timeout: The timeout in seconds for opening a connectoin and issuing commands to the device.
        heart_beat: Set to True to enable heart beat messages, False to disable. Used in conjunction with heart_beat_delay. The default is True.
        heart_beat_interval: The interval in seconds between heart beat messages. Used in conjunction with heart_beat.
        all_progress_events: Set to True to receive media progress events, False to only receive media changed events. The default is True.
        dispatcher: The dispatcher instance to use for event callbacks. If not provided, an internally created instance will be used.
        auto_reconnect: Set to True to automatically reconnect if the connection is lost. The default is False. Used in conjunction with auto_reconnect_delay.
        auto_reconnect_delay: The delay in seconds before attempting to reconnect. The default is 10 seconds. Used in conjunction with auto_reconnect.
        credentials: credentials to use to automatically sign-in to the HEOS account upon successful connection. If not provided, the account will not be signed in.
    """

    host: str
    timeout: float = field(default=const.DEFAULT_TIMEOUT, kw_only=True)
    all_progress_events: bool = field(default=True, kw_only=True)
    dispatcher: Dispatcher | None = field(default=None, kw_only=True)
    auto_reconnect: bool = field(default=False, kw_only=True)
    auto_reconnect_delay: float = field(
        default=const.DEFAULT_RECONNECT_DELAY, kw_only=True
    )
    auto_reconnect_max_attempts: int = field(
        default=const.DEFAULT_RECONNECT_ATTEMPTS, kw_only=True
    )
    heart_beat: bool = field(default=True, kw_only=True)
    heart_beat_interval: float = field(default=const.DEFAULT_HEART_BEAT, kw_only=True)
    credentials: Credentials | None = field(default=None, kw_only=True)


class Heos:
    """The Heos class provides access to the CLI API."""

    @classmethod
    async def create_and_connect(cls, host: str, **kwargs: Any) -> "Heos":
        """
        Create a new instance of the Heos CLI API and connect.

        Args:
            host: A host name or IP address of a HEOS-capable device.
            timeout: The timeout in seconds for opening a connectoin and issuing commands to the device.
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

    def __init__(self, options: HeosOptions) -> None:
        """Init a new instance of the Heos CLI API."""
        self._options = options

        self._connection = AutoReconnectingConnection(
            options.host,
            timeout=options.timeout,
            reconnect=options.auto_reconnect,
            reconnect_delay=options.auto_reconnect_delay,
            reconnect_max_attempts=options.auto_reconnect_max_attempts,
            heart_beat=options.heart_beat,
            heart_beat_interval=options.heart_beat_interval,
        )
        self._connection.add_on_connected(self._on_connected)
        self._connection.add_on_disconnected(self._on_disconnected)
        self._connection.add_on_event(self._on_event)

        self._commands = HeosCommands(self._connection)

        self._dispatcher = options.dispatcher or Dispatcher()

        self._players: dict[int, HeosPlayer] = {}
        self._players_loaded = False

        self._music_sources: dict[int, HeosSource] = {}
        self._music_sources_loaded = False

        self._groups: dict[int, HeosGroup] = {}
        self._groups_loaded = False

        self._signed_in_username: str | None = None

    async def connect(self) -> None:
        """Connect to the CLI."""
        await self._connection.connect()

    async def _on_connected(self) -> None:
        """Handle when connected, which may occur more than once."""
        assert self._connection.state == const.STATE_CONNECTED

        # Sign-in to the account if provided
        if self._options.credentials:
            try:
                await self._commands.sign_in(
                    self._options.credentials.username,
                    self._options.credentials.password,
                )
            except CommandError as err:
                _LOGGER.error("Failed to sign-in to HEOS account: %s", err)
                self._dispatcher.send(
                    const.SIGNAL_HEOS_EVENT, const.EVENT_USER_CREDENTIALS_INVALID
                )

        self._signed_in_username = await self._commands.check_account()
        await self._commands.register_for_change_events(True)

        self._dispatcher.send(const.SIGNAL_HEOS_EVENT, const.EVENT_CONNECTED)

    async def disconnect(self) -> None:
        """Disconnect from the CLI."""
        await self._connection.disconnect()

    async def _on_disconnected(self, from_error: bool) -> None:
        """Handle when disconnected, which may occur more than once."""
        assert self._connection.state == const.STATE_DISCONNECTED
        self._dispatcher.send(const.SIGNAL_HEOS_EVENT, const.EVENT_DISCONNECTED)

    async def _handle_heos_event(self, event: HeosMessage) -> None:
        """Process a HEOS system event."""
        result: dict[str, list | dict] | None = None
        if event.command == const.EVENT_PLAYERS_CHANGED and self._players_loaded:
            result = await self.load_players()
        if event.command == const.EVENT_SOURCES_CHANGED and self._music_sources_loaded:
            await self.get_music_sources(refresh=True)
        elif event.command == const.EVENT_USER_CHANGED:
            if const.PARAM_SIGNED_IN in event.message:
                self._signed_in_username = event.get_message_value(
                    const.PARAM_USER_NAME
                )
            else:
                self._signed_in_username = None
        elif event.command == const.EVENT_GROUPS_CHANGED and self._groups_loaded:
            await self.get_groups(refresh=True)

        self._dispatcher.send(const.SIGNAL_CONTROLLER_EVENT, event.command, result)
        _LOGGER.debug("Event received: %s", event)

    async def _handle_player_event(self, event: HeosMessage) -> None:
        """Process an event about a player."""
        player_id = event.get_message_value_int(const.PARAM_PLAYER_ID)
        player = self.players.get(player_id)
        if player and (
            await player.event_update(event, self._options.all_progress_events)
        ):
            self.dispatcher.send(const.SIGNAL_PLAYER_EVENT, player_id, event.command)
            _LOGGER.debug("Event received for player %s: %s", player, event)

    async def _handle_group_event(self, event: HeosMessage) -> None:
        """Process an event about a group."""
        group_id = event.get_message_value_int(const.PARAM_GROUP_ID)
        group = self.groups.get(group_id)
        if group:
            await group.event_update(event)
            self.dispatcher.send(const.SIGNAL_GROUP_EVENT, group_id, event.command)
            _LOGGER.debug("Event received for group %s: %s", group_id, event)

    async def _on_event(self, event: HeosMessage) -> None:
        """Handle a heos event."""
        if event.command in const.HEOS_EVENTS:
            await self._handle_heos_event(event)
        elif event.command in const.PLAYER_EVENTS:
            await self._handle_player_event(event)
        elif event.command in const.GROUP_EVENTS:
            await self._handle_group_event(event)
        else:
            _LOGGER.debug("Unrecognized event: %s", event)

    async def sign_in(self, username: str, password: str) -> None:
        """Sign-in to the HEOS account on the device directly connected."""
        await self._commands.sign_in(username, password)

    async def sign_out(self) -> None:
        """Sign-out of the HEOS account on the device directly connected."""
        await self._commands.sign_out()

    async def load_players(self) -> dict[str, list | dict]:
        """Refresh the players."""
        new_player_ids = []
        mapped_player_ids = {}
        players = {}
        payload = await self._commands.get_players()
        existing = list(self._players.values())
        for player_data in payload:
            player_id = player_data["pid"]
            name = player_data["name"]
            version = player_data["version"]
            # Try finding existing player by id or match name when firmware
            # version is different because IDs change after a firmware upgrade
            player = next(
                (
                    player
                    for player in existing
                    if player.player_id == player_id
                    or (player.name == name and player.version != version)
                ),
                None,
            )
            if player:
                # Existing player matched - update
                if player.player_id != player_id:
                    mapped_player_ids[player_id] = player.player_id
                player.from_data(player_data)
                players[player_id] = player
                existing.remove(player)
            else:
                # New player
                player = HeosPlayer(self, player_data)
                new_player_ids.append(player_id)
                players[player_id] = player
        # For any item remaining in existing, mark unavailalbe, add to updated
        for player in existing:
            player.set_available(False)
            players[player.player_id] = player

        # Update all statuses
        await asyncio.gather(
            *[player.refresh() for player in players.values() if player.available]
        )
        self._players = players
        self._players_loaded = True
        return {
            const.DATA_NEW: new_player_ids,
            const.DATA_MAPPED_IDS: mapped_player_ids,
        }

    async def get_players(self, *, refresh: bool = False) -> dict[int, HeosPlayer]:
        """Get available players."""
        # get players and pull initial state
        if not self._players_loaded or refresh:
            await self.load_players()
        return self._players

    async def get_groups(self, *, refresh: bool = False) -> dict[int, HeosGroup]:
        """Get available groups."""
        if not self._groups_loaded or refresh:
            players = await self.get_players()
            groups = {}
            payload = await self._commands.get_groups()
            for data in payload:
                group = create_group(self, data, players)
                groups[group.group_id] = group
            self._groups = groups
            # Update all statuses
            await asyncio.gather(*[group.refresh() for group in self._groups.values()])
            self._groups_loaded = True
        return self._groups

    async def create_group(self, leader_id: int, member_ids: Sequence[int]) -> None:
        """Create a HEOS group."""
        ids = [leader_id]
        ids.extend(member_ids)
        await self._commands.set_group(ids)

    async def remove_group(self, group_id: int) -> None:
        """Ungroup the specified group."""
        await self._commands.set_group([group_id])

    async def update_group(self, group_id: int, member_ids: Sequence[int]) -> None:
        """Update the membership of a group."""
        ids = [group_id]
        ids.extend(member_ids)
        await self._commands.set_group(ids)

    async def get_music_sources(self, refresh: bool = True) -> dict[int, HeosSource]:
        """Get available music sources."""
        if not self._music_sources or refresh:
            payload = await self._commands.get_music_sources()
            self._music_sources.clear()
            for data in payload:
                source = HeosSource(self._commands, data)
                assert source.source_id is not None
                self._music_sources[source.source_id] = source
            self._music_sources_loaded = True
        return self._music_sources

    async def get_input_sources(self) -> Sequence[InputSource]:
        """Get available input sources."""
        payload = await self._commands.browse(const.MUSIC_SOURCE_AUX_INPUT)
        sources = [HeosSource(self._commands, item) for item in payload]
        input_sources = []
        for source in sources:
            assert source.source_id is not None
            player_id = source.source_id
            items = await source.browse()
            input_sources.extend(
                [
                    InputSource(player_id, item.name, str(item.media_id))
                    for item in items
                ]
            )
        return input_sources

    async def get_favorites(self) -> dict[int, HeosSource]:
        """Get available favorites."""
        payload = await self._commands.browse(const.MUSIC_SOURCE_FAVORITES)
        sources = [HeosSource(self._commands, item) for item in payload]
        return {index + 1: source for index, source in enumerate(sources)}

    async def get_playlists(self) -> Sequence[HeosSource]:
        """Get available playlists."""
        payload = await self._commands.browse(const.MUSIC_SOURCE_PLAYLISTS)
        playlists = []
        for item in payload:
            item["sid"] = const.MUSIC_SOURCE_PLAYLISTS
            playlists.append(HeosSource(self._commands, item))
        return playlists

    @property
    def dispatcher(self) -> Dispatcher:
        """Get the dispatcher instance."""
        return self._dispatcher

    @property
    def players(self) -> dict[int, HeosPlayer]:
        """Get the loaded players."""
        return self._players

    @property
    def groups(self) -> dict[int, HeosGroup]:
        """Get the loaded groups."""
        return self._groups

    @property
    def music_sources(self) -> dict[int, HeosSource]:
        """Get available music sources."""
        return self._music_sources

    @property
    def connection_state(self) -> str:
        """Get the state of the connection."""
        return self._connection.state

    @property
    def is_signed_in(self) -> bool:
        """Return True if the HEOS accuont is signed in."""
        return bool(self._signed_in_username)

    @property
    def signed_in_username(self) -> Optional[str]:
        """Return the signed-in username."""
        return self._signed_in_username
