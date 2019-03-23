"""Define the heos manager module."""
import asyncio
import logging
from typing import Dict, Optional, Sequence

from . import const
from .connection import HeosConnection
from .dispatch import Dispatcher
from .player import HeosPlayer
from .source import HeosSource, InputSource

_LOGGER = logging.getLogger(__name__)


class Heos:
    """The Heos class provides access to the CLI API."""

    def __init__(self, host: str, timeout: int = const.DEFAULT_TIMEOUT,
                 *, dispatcher=None):
        """Init a new instance of the Heos CLI API."""
        self._connection = HeosConnection(self, host, timeout)
        self._dispatcher = dispatcher or Dispatcher()
        self._players = {}

    async def connect(self):
        """Connect to the CLI."""
        await self._connection.connect()
        # get players and pull initial state
        players = await self._connection.commands.get_players()
        await asyncio.gather(*[player.refresh() for player in players])
        self._players = {player.player_id: player for player in players}

    async def disconnect(self):
        """Disconnect from the CLI."""
        await self._connection.disconnect()
        self._players.clear()

    async def get_music_sources(self) -> Sequence[HeosSource]:
        """Get available music sources."""
        return await self._connection.commands.get_music_sources()

    async def get_input_sources(self) -> Sequence[InputSource]:
        """Get available input sources."""
        sources = await self.get_music_sources()
        aux_input = next(source for source in sources
                         if source.name == const.SOURCE_AUX_INPUT)
        sources = await aux_input.browse()
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
        sources = await self.get_music_sources()
        favorites = next(source for source in sources
                         if source.name == const.SOURCE_FAVORITES)
        sources = await favorites.browse()
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
