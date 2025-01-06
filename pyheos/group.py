"""Define the heos group module."""

import asyncio
from collections.abc import Sequence
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, Optional

from pyheos.message import HeosMessage

from . import const

if TYPE_CHECKING:
    from pyheos.heos import Heos


@dataclass
class HeosGroup:
    """A group of players."""

    name: str
    group_id: int
    lead_player_id: int
    member_player_ids: Sequence[int]
    volume: int = 0
    is_muted: bool = False
    heos: Optional["Heos"] = field(repr=False, hash=False, compare=False, default=None)

    @classmethod
    def from_data(
        cls,
        data: dict[str, Any],
        heos: Optional["Heos"] = None,
    ) -> "HeosGroup":
        """Create a new instance from the provided data."""
        player_id: int | None = None
        player_ids: list[int] = []
        for group_player in data[const.ATTR_PLAYERS]:
            # Find the loaded player
            member_player_id = int(group_player[const.ATTR_PLAYER_ID])
            if group_player[const.ATTR_ROLE] == const.VALUE_LEADER:
                player_id = member_player_id
            else:
                player_ids.append(member_player_id)
        if player_id is None:
            raise ValueError("No leader found in group data")
        return cls(
            name=data[const.ATTR_NAME],
            group_id=int(data[const.ATTR_GROUP_ID]),
            lead_player_id=player_id,
            member_player_ids=player_ids,
            heos=heos,
        )

    async def on_event(self, event: HeosMessage) -> bool:
        """Handle a group update event."""
        if not (
            event.command == const.EVENT_GROUP_VOLUME_CHANGED
            and event.get_message_value_int(const.ATTR_GROUP_ID) == self.group_id
        ):
            return False
        self.volume = event.get_message_value_int(const.ATTR_LEVEL)
        self.is_muted = event.get_message_value(const.ATTR_MUTE) == const.VALUE_ON
        return True

    async def refresh(self) -> None:
        """Pull current state."""
        assert self.heos, "Heos instance not set"
        await asyncio.gather(self.refresh_volume(), self.refresh_mute())

    async def refresh_volume(self) -> None:
        """Pull the latest volume."""
        assert self.heos, "Heos instance not set"
        self.volume = await self.heos.get_group_volume(self.group_id)

    async def refresh_mute(self) -> None:
        """Pull the latest mute status."""
        assert self.heos, "Heos instance not set"
        self.is_muted = await self.heos.get_group_mute(self.group_id)

    async def set_volume(self, level: int) -> None:
        """Set the volume level."""
        assert self.heos, "Heos instance not set"
        await self.heos.set_group_volume(self.group_id, level)

    async def volume_up(self, step: int = const.DEFAULT_STEP) -> None:
        """Raise the volume."""
        assert self.heos, "Heos instance not set"
        await self.heos.group_volume_up(self.group_id, step)

    async def volume_down(self, step: int = const.DEFAULT_STEP) -> None:
        """Raise the volume."""
        assert self.heos, "Heos instance not set"
        await self.heos.group_volume_down(self.group_id, step)

    async def set_mute(self, state: bool) -> None:
        """Set the mute state."""
        assert self.heos, "Heos instance not set"
        await self.heos.group_set_mute(self.group_id, state)

    async def mute(self) -> None:
        """Set mute state."""
        assert self.heos, "Heos instance not set"
        await self.set_mute(True)

    async def unmute(self) -> None:
        """Clear mute state."""
        assert self.heos, "Heos instance not set"
        await self.set_mute(False)

    async def toggle_mute(self) -> None:
        """Toggle mute state."""
        assert self.heos, "Heos instance not set"
        await self.heos.group_toggle_mute(self.group_id)
