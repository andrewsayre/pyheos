"""Define the heos group module."""

import asyncio
from collections.abc import Sequence
from typing import TYPE_CHECKING, Any

from pyheos.message import HeosMessage

from . import const
from .player import HeosPlayer

if TYPE_CHECKING:
    from pyheos.heos import Heos


def create_group(
    heos: "Heos", data: dict[str, Any], players: dict[int, HeosPlayer]
) -> "HeosGroup":
    """Create a group from the data."""
    leader = None
    members = []
    for group_player in data["players"]:
        player = players[int(group_player["pid"])]
        if group_player["role"] == "leader":
            leader = player
        else:
            members.append(player)
    if leader is None:
        raise ValueError("No leader found in group")
    return HeosGroup(heos, data[const.ATTR_NAME], int(data["gid"]), leader, members)


class HeosGroup:
    """A group of players."""

    def __init__(
        self,
        heos: "Heos",
        name: str,
        group_id: int,
        leader: HeosPlayer,
        members: Sequence[HeosPlayer],
    ) -> None:
        """Init the group class."""
        self._heos = heos
        # pylint: disable=protected-access
        self._commands = heos._commands
        self._name: str = name
        self._group_id: int = group_id
        self._leader: HeosPlayer = leader
        self._members: Sequence[HeosPlayer] = members
        self._volume: int = 0
        self._is_muted: bool = False

    async def refresh(self) -> None:
        """Pull current state."""
        await asyncio.gather(self.refresh_volume(), self.refresh_mute())

    async def refresh_volume(self) -> None:
        """Pull the latest volume."""
        self._volume = await self._commands.get_group_volume(self._group_id)

    async def refresh_mute(self) -> None:
        """Pull the latest mute status."""
        self._is_muted = await self._commands.get_group_mute(self._group_id)

    async def event_update(self, event: HeosMessage) -> bool:
        """Handle a group update event."""
        if event.command == const.EVENT_GROUP_VOLUME_CHANGED:
            self._volume = event.get_message_value_int("level")
            self._is_muted = event.get_message_value("mute") == "on"
        return True

    async def set_volume(self, level: int) -> None:
        """Set the volume level."""
        await self._commands.set_group_volume(self._group_id, level)

    async def volume_up(self, step: int = const.DEFAULT_STEP) -> None:
        """Raise the volume."""
        await self._commands.group_volume_up(self._group_id, step)

    async def volume_down(self, step: int = const.DEFAULT_STEP) -> None:
        """Raise the volume."""
        await self._commands.group_volume_down(self._group_id, step)

    async def set_mute(self, state: bool) -> None:
        """Set the mute state."""
        await self._commands.group_set_mute(self._group_id, state)

    async def mute(self) -> None:
        """Set mute state."""
        await self.set_mute(True)

    async def unmute(self) -> None:
        """Clear mute state."""
        await self.set_mute(False)

    async def toggle_mute(self) -> None:
        """Toggle mute state."""
        await self._commands.group_toggle_mute(self._group_id)

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
