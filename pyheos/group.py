"""Define the heos group module."""

import asyncio
from collections.abc import Sequence
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, Optional

from pyheos.const import DEFAULT_STEP, EVENT_GROUP_VOLUME_CHANGED
from pyheos.dispatch import DisconnectType, EventCallbackType, callback_wrapper
from pyheos.message import HeosMessage
from pyheos.types import SignalType

from . import command as c

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

    @staticmethod
    def _from_data(
        data: dict[str, Any],
        heos: Optional["Heos"] = None,
    ) -> "HeosGroup":
        """Create a new instance from the provided data."""
        player_id: int | None = None
        player_ids: list[int] = []
        player_id, player_ids = HeosGroup.__get_ids(data[c.ATTR_PLAYERS])
        return HeosGroup(
            name=data[c.ATTR_NAME],
            group_id=int(data[c.ATTR_GROUP_ID]),
            lead_player_id=player_id,
            member_player_ids=player_ids,
            heos=heos,
        )

    @staticmethod
    def __get_ids(players: list[dict[str, Any]]) -> tuple[int, list[int]]:
        """Get the leader and members from the player data."""
        lead_player_id: int | None = None
        member_player_ids: list[int] = []
        for member_player in players:
            # Find the loaded player
            member_player_id = int(member_player[c.ATTR_PLAYER_ID])
            if member_player[c.ATTR_ROLE] == c.VALUE_LEADER:
                lead_player_id = member_player_id
            else:
                member_player_ids.append(member_player_id)
        if lead_player_id is None:
            raise ValueError("No leader found in group data")
        return lead_player_id, member_player_ids

    def _update_from_data(self, data: dict[str, Any]) -> None:
        """Update the group with the provided data."""
        self.name = data[c.ATTR_NAME]
        self.group_id = int(data[c.ATTR_GROUP_ID])
        self.lead_player_id, self.member_player_ids = self.__get_ids(
            data[c.ATTR_PLAYERS]
        )

    async def _on_event(self, event: HeosMessage) -> bool:
        """Handle a group update event."""
        if not (
            event.command == EVENT_GROUP_VOLUME_CHANGED
            and event.get_message_value_int(c.ATTR_GROUP_ID) == self.group_id
        ):
            return False
        self.volume = event.get_message_value_int(c.ATTR_LEVEL)
        self.is_muted = event.get_message_value(c.ATTR_MUTE) == c.VALUE_ON
        return True

    def add_on_group_event(self, callback: EventCallbackType) -> DisconnectType:
        """Connect a callback to be invoked when an event occurs for this group.

        Args:
            callback: The callback to be invoked.
        Returns:
            A function that disconnects the callback."""
        assert self.heos, "Heos instance not set"
        # Use lambda to yield player_id since the value can change
        return self.heos.dispatcher.connect(
            SignalType.GROUP_EVENT,
            callback_wrapper(callback, {0: lambda: self.group_id}),
        )

    async def refresh(self, *, refresh_base_info: bool = True) -> None:
        """Pulls the current volume and mute state of the group.

        Args:
            refresh_base_info: When True, the base information of the group, including the name and members, will also be pulled. Defaults is False.
        """
        assert self.heos, "Heos instance not set"
        if refresh_base_info:
            await self.heos.get_group_info(group=self, refresh=True)
        else:
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

    async def volume_up(self, step: int = DEFAULT_STEP) -> None:
        """Raise the volume."""
        assert self.heos, "Heos instance not set"
        await self.heos.group_volume_up(self.group_id, step)

    async def volume_down(self, step: int = DEFAULT_STEP) -> None:
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
