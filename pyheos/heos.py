"""Define the heos manager module."""

import asyncio
from collections.abc import Sequence
from typing import Any, Optional

from . import const
from .connection import HeosConnection
from .dispatch import Dispatcher
from .group import HeosGroup, create_group
from .player import HeosPlayer
from .response import HeosResponse
from .source import HeosSource, InputSource


class Heos:
    """The Heos class provides access to the CLI API."""

    def __init__(
        self,
        host: str,
        *,
        timeout: float = const.DEFAULT_TIMEOUT,
        heart_beat: Optional[float] = const.DEFAULT_HEART_BEAT,
        all_progress_events: bool = True,
        dispatcher: Dispatcher | None = None,
    ) -> None:
        """Init a new instance of the Heos CLI API."""
        self._connection = HeosConnection(
            self,
            host,
            timeout=timeout,
            heart_beat=heart_beat,
            all_progress_events=all_progress_events,
        )
        self._dispatcher = dispatcher or Dispatcher()
        self._players: dict[int, HeosPlayer] = {}
        self._players_loaded = False
        self._music_sources: dict[int, HeosSource] = {}
        self._music_sources_loaded = False
        self._signed_in_username: str | None = None
        self._groups: dict[int, HeosGroup] = {}
        self._groups_loaded = False

    async def connect(
        self,
        *,
        auto_reconnect: bool = False,
        reconnect_delay: float = const.DEFAULT_RECONNECT_DELAY,
    ) -> None:
        """Connect to the CLI."""
        await self._connection.connect(
            auto_reconnect=auto_reconnect, reconnect_delay=reconnect_delay
        )
        self._signed_in_username = await self._connection.commands.check_account()

    async def disconnect(self) -> None:
        """Disconnect from the CLI."""
        await self._connection.disconnect()

    async def _handle_event(self, event: HeosResponse) -> Any:
        """Handle a heos event."""
        if event.command == const.EVENT_PLAYERS_CHANGED and self._players_loaded:
            return await self.load_players()
        if event.command == const.EVENT_SOURCES_CHANGED and self._music_sources_loaded:
            await self.get_music_sources(refresh=True)
        elif event.command == const.EVENT_USER_CHANGED:
            self._signed_in_username = (
                event.get_message("un") if event.has_message("signed_in") else None
            )
        elif event.command == const.EVENT_GROUPS_CHANGED and self._groups_loaded:
            await self.get_groups(refresh=True)
        return True

    async def sign_in(self, username: str, password: str) -> None:
        """Sign-in to the HEOS account on the device directly connected."""
        await self._connection.commands.sign_in(username, password)

    async def sign_out(self) -> None:
        """Sign-out of the HEOS account on the device directly connected."""
        await self._connection.commands.sign_out()

    async def load_players(self) -> dict[str, list | dict]:
        """Refresh the players."""
        new_player_ids = []
        mapped_player_ids = {}
        players = {}
        payload = await self._connection.commands.get_players()
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
            payload = await self._connection.commands.get_groups()
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
        await self._connection.commands.set_group(ids)

    async def remove_group(self, group_id: int) -> None:
        """Ungroup the specified group."""
        await self._connection.commands.set_group([group_id])

    async def update_group(self, group_id: int, member_ids: Sequence[int]) -> None:
        """Update the membership of a group."""
        ids = [group_id]
        ids.extend(member_ids)
        await self._connection.commands.set_group(ids)

    async def get_music_sources(self, refresh: bool = True) -> dict[int, HeosSource]:
        """Get available music sources."""
        if not self._music_sources or refresh:
            payload = await self._connection.commands.get_music_sources()
            self._music_sources.clear()
            for data in payload:
                source = HeosSource(self._connection.commands, data)
                assert source.source_id is not None
                self._music_sources[source.source_id] = source
            self._music_sources_loaded = True
        return self._music_sources

    async def get_input_sources(self) -> Sequence[InputSource]:
        """Get available input sources."""
        payload = await self._connection.commands.browse(const.MUSIC_SOURCE_AUX_INPUT)
        sources = [HeosSource(self._connection.commands, item) for item in payload]
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
        payload = await self._connection.commands.browse(const.MUSIC_SOURCE_FAVORITES)
        sources = [HeosSource(self._connection.commands, item) for item in payload]
        return {index + 1: source for index, source in enumerate(sources)}

    async def get_playlists(self) -> Sequence[HeosSource]:
        """Get available playlists."""
        payload = await self._connection.commands.browse(const.MUSIC_SOURCE_PLAYLISTS)
        playlists = []
        for item in payload:
            item["sid"] = const.MUSIC_SOURCE_PLAYLISTS
            playlists.append(HeosSource(self._connection.commands, item))
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
