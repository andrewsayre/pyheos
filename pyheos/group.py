"""Define the heos group module."""
import asyncio
from typing import Dict, Sequence

from . import const
from .player import HeosPlayer
from .response import HeosResponse


def create_group(heos, data: dict,
                 players: Dict[int, HeosPlayer]) -> 'HeosGroup':
    """Create a group from the data."""
    leader = None
    members = []
    for group_player in data['players']:
        player = players[int(group_player['pid'])]
        if group_player['role'] == 'leader':
            leader = player
        else:
            members.append(player)
    return HeosGroup(heos, data['name'], int(data['gid']), leader, members)


class HeosGroup:
    """A group of players."""

    def __init__(self, heos, name: str, group_id: int,
                 leader: HeosPlayer, members: Sequence[HeosPlayer]):
        """Init the group class."""
        self._heos = heos
        # pylint: disable=protected-access
        self._commands = heos._connection.commands
        self._name = name  # type: str
        self._group_id = group_id  # type: int
        self._leader = leader  # type: HeosPlayer
        self._members = members  # type: Sequence[HeosPlayer]
        self._volume = None  # type: int
        self._is_muted = None  # type: bool

    async def refresh(self):
        """Pull current state."""
        await asyncio.gather(self.refresh_volume(), self.refresh_mute())

    async def refresh_volume(self):
        """Pull the latest volume."""
        self._volume = await self._commands.get_group_volume(self._group_id)

    async def refresh_mute(self):
        """Pull the latest mute status."""
        self._is_muted = await self._commands.get_group_mute(self._group_id)

    async def event_update(self, event: HeosResponse) -> bool:
        """Handle a group update event."""
        if event.command == const.EVENT_GROUP_VOLUME_CHANGED:
            self._volume = int(float(event.get_message('level')))
            self._is_muted = event.get_message('mute') == 'on'
        return True

    async def set_volume(self, level: int):
        """Set the volume level."""
        await self._commands.set_group_volume(self._group_id, level)

    async def volume_up(self, step: int = const.DEFAULT_STEP):
        """Raise the volume."""
        await self._commands.group_volume_up(self._group_id, step)

    async def volume_down(self, step: int = const.DEFAULT_STEP):
        """Raise the volume."""
        await self._commands.group_volume_down(self._group_id, step)

    async def set_mute(self, state: bool):
        """Set the mute state."""
        return await self._commands.group_set_mute(self._group_id, state)

    async def mute(self):
        """Set mute state."""
        return await self.set_mute(True)

    async def unmute(self):
        """Clear mute state."""
        return await self.set_mute(False)

    async def toggle_mute(self):
        """Toggle mute state."""
        return await self._commands.group_toggle_mute(self._group_id)

    @property
    def name(self) -> str:
        """Get the name of the group."""
        return self._name

    @property
    def group_id(self) -> int:
        """Get the id of the group."""
        return self._group_id

    @property
    def leader(self) -> HeosPlayer:
        """Get the leader player of the group."""
        return self._leader

    @property
    def members(self) -> Sequence[HeosPlayer]:
        """Get the members of the group."""
        return self._members

    @property
    def volume(self) -> int:
        """Get the volume of the group."""
        return self._volume

    @property
    def is_muted(self) -> bool:
        """Return True if the group is muted."""
        return self._is_muted
