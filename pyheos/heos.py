"""Define the heos manager module."""
import asyncio
import logging
from typing import Optional, Sequence

from .connection import HeosConnection
from .const import DEFAULT_TIMEOUT
from .dispatch import Dispatcher
from .player import HeosPlayer
from .source import HeosSource

_LOGGER = logging.getLogger(__name__)


class Heos:
    """The Heos class provides access to the CLI API."""

    def __init__(self, host: str, timeout: int = DEFAULT_TIMEOUT,
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
