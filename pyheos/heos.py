"""Define the heos manager module."""

import asyncio
from typing import Dict, Optional, Sequence

from . import const
from .connection import HeosConnection
from .dispatch import Dispatcher
from .group import HeosGroup, create_group
from .player import HeosPlayer, parse_player_id, parse_player_name, parse_player_version
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
        all_progress_events=True,
        dispatcher: Dispatcher = None,
    ):
        """Init a new instance of the Heos CLI API."""
        self._connection = HeosConnection(
            self,
            host,
            timeout=timeout,
            heart_beat=heart_beat,
            all_progress_events=all_progress_events,
        )
        self._dispatcher = dispatcher or Dispatcher()
        self._players = {}  # type: Dict[int, HeosPlayer]
        self._players_loaded = False
        self._music_sources = {}  # type: Dict[int, HeosSource]
        self._music_sources_loaded = False
        self._signed_in_username = None  # type: str
        self._groups = {}  # type: Dict[int, HeosGroup]
        self._groups_loaded = False

    async def connect(
        self,
        *,
        auto_reconnect=False,
        reconnect_delay: float = const.DEFAULT_RECONNECT_DELAY,
    ):
        """Connect to the CLI."""
        await self._connection.connect(
            auto_reconnect=auto_reconnect, reconnect_delay=reconnect_delay
        )
        self._signed_in_username = await self._connection.commands.check_account()

    async def disconnect(self):
        """Disconnect from the CLI."""
        await self._connection.disconnect()

    async def _handle_event(self, event: HeosResponse):
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

    async def sign_in(self, username: str, password: str):
        """Sign-in to the HEOS account on the device directly connected."""
        await self._connection.commands.sign_in(username, password)

    async def sign_out(self):
        """Sign-out of the HEOS account on the device directly connected."""
        await self._connection.commands.sign_out()

    async def load_players(self):
        """Refresh the players."""
        changes = {const.DATA_NEW: [], const.DATA_MAPPED_IDS: {}}
        players = {}
        payload = await self._connection.commands.get_players()
        existing = list(self._players.values())
        for player_data in payload:
            player_id = parse_player_id(player_data)
            name = parse_player_name(player_data)
            version = parse_player_version(player_data)
            # Try finding existing player by id or match name when firmware
            # verion is different because IDs change after a firmware upgrade
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
                    changes[const.DATA_MAPPED_IDS][player_id] = player.player_id
                player.from_data(player_data)
                players[player_id] = player
                existing.remove(player)
            else:
                # New player
                player = HeosPlayer(self, player_data)
                changes[const.DATA_NEW].append(player_id)
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
        return changes

    async def get_players(self, *, refresh=False) -> Dict[int, HeosPlayer]:
        """Get available players."""
        # get players and pull initial state
        if not self._players_loaded or refresh:
            await self.load_players()
        return self._players

    async def get_groups(self, *, refresh=False) -> Dict[int, HeosGroup]:
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

    async def create_group(self, leader_id: int, member_ids: Sequence[int]):
        """Create a HEOS group."""
        ids = [leader_id]
        ids.extend(member_ids)
        await self._connection.commands.set_group(ids)

    async def remove_group(self, group_id: int):
        """Ungroup the specifid group."""
        await self._connection.commands.set_group([group_id])

    async def update_group(self, group_id: int, member_ids: Sequence[int]):
        """Update the membership of a group."""
        ids = [group_id]
        ids.extend(member_ids)
        await self._connection.commands.set_group(ids)

    async def get_music_sources(self, refresh=True) -> Dict[int, HeosSource]:
        """Get available music sources."""
        if not self._music_sources or refresh:
            payload = await self._connection.commands.get_music_sources()
            self._music_sources.clear()
            for data in payload:
                source = HeosSource(self._connection.commands, data)
                self._music_sources[source.source_id] = source
            self._music_sources_loaded = True
        return self._music_sources

    async def get_input_sources(self) -> Sequence[InputSource]:
        """Get available input sources."""
        payload = await self._connection.commands.browse(const.MUSIC_SOURCE_AUX_INPUT)
        sources = [HeosSource(self._connection.commands, item) for item in payload]
        input_sources = []
        for source in sources:
            player_id = source.source_id
            items = await source.browse()
            input_sources.extend(
                [InputSource(player_id, item.name, item.media_id) for item in items]
            )
        return input_sources

    async def get_favorites(self) -> Dict[int, HeosSource]:
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
    def players(self) -> Dict[int, HeosPlayer]:
        """Get the loaded players."""
        return self._players

    @property
    def groups(self) -> Dict[int, HeosGroup]:
        """Get the loaded groups."""
        return self._groups

    @property
    def music_sources(self) -> Dict[int, HeosSource]:
        """Get available music sources."""
        return self._music_sources

    @property
    def connection_state(self):
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
