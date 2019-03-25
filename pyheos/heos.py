"""Define the heos manager module."""
import asyncio
import logging
from typing import Dict, Optional, Sequence

from . import const
from .connection import HeosConnection
from .dispatch import Dispatcher
from .player import HeosPlayer
from .response import HeosResponse
from .source import HeosSource, InputSource

_LOGGER = logging.getLogger(__name__)


class Heos:
    """The Heos class provides access to the CLI API."""

    def __init__(self, host: str, *,
                 timeout: float = const.DEFAULT_TIMEOUT,
                 heart_beat: Optional[float] = const.DEFAULT_HEART_BEAT,
                 all_progress_events=True,
                 dispatcher: Dispatcher = None):
        """Init a new instance of the Heos CLI API."""
        self._connection = HeosConnection(
            self, host, timeout=timeout, heart_beat=heart_beat,
            all_progress_events=all_progress_events)
        self._dispatcher = dispatcher or Dispatcher()
        self._players = {}  # type: Dict[int, HeosPlayer]
        self._players_loaded = False
        self._music_sources = {}  # type: Dict[int, HeosSource]
        self._music_sources_loaded = False

    async def connect(self, *, auto_reconnect=False,
                      reconnect_delay: float = const.DEFAULT_RECONNECT_DELAY):
        """Connect to the CLI."""
        await self._connection.connect(auto_reconnect=auto_reconnect,
                                       reconnect_delay=reconnect_delay)

    async def disconnect(self):
        """Disconnect from the CLI."""
        await self._connection.disconnect()

    async def _handle_event(self, event: HeosResponse) -> bool:
        """Handle a heos event."""
        if event.command == const.EVENT_PLAYERS_CHANGED \
                and self._players_loaded:
            await self.get_players(refresh=True)
        if event.command == const.EVENT_SOURCES_CHANGED \
                and self._music_sources_loaded:
            await self.get_music_sources(refresh=True)
        return True

    async def get_players(self, *, refresh=False) -> Dict[int, HeosPlayer]:
        """Get available players."""
        # get players and pull initial state
        if not self._players or refresh:
            payload = await self._connection.commands.get_players()
            players = {}
            player_data = {}
            for data in payload:
                player = HeosPlayer(self._connection.commands, data)
                players[player.player_id] = player
                player_data[player.player_id] = data
            # Match to existing
            for player_id in self._players.copy():
                if player_id in players:
                    players.pop(player_id)
                    self._players[player_id].from_data(player_data[player_id])
                else:
                    self._players.pop(player_id).set_removed()
            self._players.update(players)
            # Update all statuses
            await asyncio.gather(*[player.refresh() for player in
                                   self._players.values()])
            self._players_loaded = True
        return self._players

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
        payload = await self._connection.commands.browse(
            const.MUSIC_SOURCE_AUX_INPUT)
        sources = [HeosSource(self._connection.commands, item)
                   for item in payload]
        input_sources = []
        for source in sources:
            player_id = source.source_id
            items = await source.browse()
            input_sources.extend(
                [InputSource(player_id, item.name, item.media_id)
                 for item in items])
        return input_sources

    async def get_favorites(self) -> Dict[int, HeosSource]:
        """Get available favorites."""
        payload = await self._connection.commands.browse(
            const.MUSIC_SOURCE_FAVORITES)
        sources = [HeosSource(self._connection.commands, item)
                   for item in payload]
        return {index + 1: source for index, source in enumerate(sources)}

    @property
    def dispatcher(self) -> Dispatcher:
        """Get the dispatcher instance."""
        return self._dispatcher

    @property
    def players(self) -> Dict[int, HeosPlayer]:
        """Get the available players."""
        return self._players

    @property
    def music_sources(self) -> Dict[int, HeosSource]:
        """Get available music sources."""
        return self._music_sources

    @property
    def connection_state(self):
        """Get the state of the connection."""
        return self._connection.state

    def get_player(self, player_id: int) -> Optional[HeosPlayer]:
        """Get the player with the specified id."""
        return self._players.get(player_id)
