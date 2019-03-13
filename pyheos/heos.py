"""Define the heos manager module."""
import asyncio
import logging
from typing import Optional, Sequence

from .connection import HeosCommandConnection, HeosEventConnection
from .const import DEFAULT_TIMEOUT
from .dispatch import Dispatcher
from .player import HeosPlayer

_LOGGER = logging.getLogger(__name__)


class Heos:
    """The Heos class provides access to the CLI API."""

    def __init__(self, host: str, timeout: int = DEFAULT_TIMEOUT,
                 *, dispatcher=None):
        """Init a new instance of the Heos CLI API."""
        self._command = HeosCommandConnection(host, timeout)
        self._event = HeosEventConnection(self, host, timeout)
        self._dispatcher = dispatcher or Dispatcher()
        self._players = {}

    async def connect(self):
        """Connect to the CLI."""
        await self._command.connect()
        # get players and pull initial state
        players = await self._command.commands.get_players()
        for player in players:
            await player.refresh()
        self._players = {player.player_id: player for player in players}
        # setup event channel
        await self._event.connect()

    async def disconnect(self):
        """Disconnect from the CLI."""
        await asyncio.gather(self._event.disconnect(),
                             self._command.disconnect())
        self._players.clear()

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
