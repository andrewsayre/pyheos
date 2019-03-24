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

    def __init__(self, host: str, timeout: int = const.DEFAULT_TIMEOUT,
                 *, dispatcher=None, all_progress_events=True):
        """Init a new instance of the Heos CLI API."""
        self._connection = HeosConnection(
            self, host, timeout, all_progress_events)
        self._dispatcher = dispatcher or Dispatcher()
        self._players = {}

    async def connect(self):
        """Connect to the CLI."""
        await self._connection.connect()

    async def disconnect(self):
        """Disconnect from the CLI."""
        await self._connection.disconnect()
        self._players.clear()

    async def _handle_event(self, event: HeosResponse) -> bool:
        """Handle a heos event."""
        if event.command == const.EVENT_PLAYERS_CHANGED:
            await self.get_players(refresh=True)
        return True

    async def get_players(self, *, refresh=False) -> Sequence[HeosPlayer]:
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

        return self._players

    async def get_music_sources(self) -> Sequence[HeosSource]:
        """Get available music sources."""
        payload = await self._connection.commands.get_music_sources()
        return [HeosSource(self._connection.commands, data)
                for data in payload]

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
    def players(self) -> Sequence[HeosPlayer]:
        """Get the available players."""
        return list(self._players.values())

    def get_player(self, player_id: int) -> Optional[HeosPlayer]:
        """Get the player with the specified id."""
        return self._players.get(player_id)
