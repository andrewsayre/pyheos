"""
Define the group command module.

This module creates HEOS group commands.
"""

import asyncio
from collections.abc import Sequence
from typing import TYPE_CHECKING, Any, cast

from pyheos import command as c
from pyheos.command.connection import ConnectionMixin
from pyheos.const import DEFAULT_STEP
from pyheos.group import HeosGroup
from pyheos.message import HeosCommand

if TYPE_CHECKING:
    from pyheos.heos import Heos


class GroupCommands(ConnectionMixin):
    """A mixin to provide access to the group commands."""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        """Init a new instance of the BrowseMixin."""
        super(GroupCommands, self).__init__(*args, **kwargs)
        self._groups: dict[int, HeosGroup] = {}
        self._groups_loaded = False

    @property
    def groups(self) -> dict[int, HeosGroup]:
        """Get the loaded groups."""
        return self._groups

    async def get_groups(self, *, refresh: bool = False) -> dict[int, HeosGroup]:
        """Get available groups.

        References:
            4.3.1 Get Groups"""
        if not self._groups_loaded or refresh:
            groups = {}
            result = await self._connection.command(HeosCommand(c.COMMAND_GET_GROUPS))
            payload = cast(Sequence[dict], result.payload)
            for data in payload:
                group = HeosGroup._from_data(data, cast("Heos", self))
                groups[group.group_id] = group
            self._groups = groups
            # Update all statuses
            await asyncio.gather(
                *[
                    group.refresh(refresh_base_info=False)
                    for group in self._groups.values()
                ]
            )
            self._groups_loaded = True
        return self._groups

    async def get_group_info(
        self,
        group_id: int | None = None,
        group: HeosGroup | None = None,
        *,
        refresh: bool = False,
    ) -> HeosGroup:
        """Get information about a group.

        Only one of group_id or group should be provided.

        Args:
            group_id: The identifier of the group to get information about. Only one of group_id or group should be provided.
            group: The HeosGroup instance to update with the latest information. Only one of group_id or group should be provided.
            refresh: Set to True to force a refresh of the group information.

        References:
            4.3.2 Get Group Info"""
        if group_id is None and group is None:
            raise ValueError("Either group_id or group must be provided")
        if group_id is not None and group is not None:
            raise ValueError("Only one of group_id or group should be provided")

        # if only group_id provided, try getting from loaded
        if group is None:
            assert group_id is not None
            group = self._groups.get(group_id)
        else:
            group_id = group.group_id

        if group is None or refresh:
            # Get the latest information
            result = await self._connection.command(
                HeosCommand(c.COMMAND_GET_GROUP_INFO, {c.ATTR_GROUP_ID: group_id})
            )
            payload = cast(dict[str, Any], result.payload)
            if group is None:
                group = HeosGroup._from_data(payload, cast("Heos", self))
            else:
                group._update_from_data(payload)
            await group.refresh(refresh_base_info=False)
        return group

    async def set_group(self, player_ids: Sequence[int]) -> None:
        """Create, modify, or ungroup players.

        Args:
            player_ids: The list of player identifiers to group or ungroup. The first player is the group leader.

        References:
            4.3.3 Set Group"""
        await self._connection.command(
            HeosCommand(
                c.COMMAND_SET_GROUP,
                {c.ATTR_PLAYER_ID: ",".join(map(str, player_ids))},
            )
        )

    async def create_group(
        self, leader_player_id: int, member_player_ids: Sequence[int]
    ) -> None:
        """Create a HEOS group.

        Args:
            leader_player_id: The player_id of the lead player in the group.
            member_player_ids: The player_ids of the group members.

        References:
            4.3.3 Set Group"""
        player_ids = [leader_player_id]
        player_ids.extend(member_player_ids)
        await self.set_group(player_ids)

    async def remove_group(self, group_id: int) -> None:
        """Ungroup the specified group.

        Args:
            group_id: The identifier of the group to ungroup. Must be the lead player.

        References:
            4.3.3 Set Group
        """
        await self.set_group([group_id])

    async def update_group(
        self, group_id: int, member_player_ids: Sequence[int]
    ) -> None:
        """Update the membership of a group.

        Args:
            group_id: The identifier of the group to update (same as the lead player_id)
            member_player_ids: The new player_ids of the group members.
        """
        await self.create_group(group_id, member_player_ids)

    async def get_group_volume(self, group_id: int) -> int:
        """
        Get the volume of a group.

        References:
            4.3.4 Get Group Volume
        """
        result = await self._connection.command(
            HeosCommand(c.COMMAND_GET_GROUP_VOLUME, {c.ATTR_GROUP_ID: group_id})
        )
        return result.get_message_value_int(c.ATTR_LEVEL)

    async def set_group_volume(self, group_id: int, level: int) -> None:
        """Set the volume of the group.

        References:
            4.3.5 Set Group Volume"""
        if level < 0 or level > 100:
            raise ValueError("'level' must be in the range 0-100")
        await self._connection.command(
            HeosCommand(
                c.COMMAND_SET_GROUP_VOLUME,
                {c.ATTR_GROUP_ID: group_id, c.ATTR_LEVEL: level},
            )
        )

    async def group_volume_up(self, group_id: int, step: int = DEFAULT_STEP) -> None:
        """Increase the volume level.

        References:
            4.3.6 Group Volume Up"""
        if step < 1 or step > 10:
            raise ValueError("'step' must be in the range 1-10")
        await self._connection.command(
            HeosCommand(
                c.COMMAND_GROUP_VOLUME_UP,
                {c.ATTR_GROUP_ID: group_id, c.ATTR_STEP: step},
            )
        )

    async def group_volume_down(self, group_id: int, step: int = DEFAULT_STEP) -> None:
        """Increase the volume level.

        References:
            4.2.7 Group Volume Down"""
        if step < 1 or step > 10:
            raise ValueError("'step' must be in the range 1-10")
        await self._connection.command(
            HeosCommand(
                c.COMMAND_GROUP_VOLUME_DOWN,
                {c.ATTR_GROUP_ID: group_id, c.ATTR_STEP: step},
            )
        )

    async def get_group_mute(self, group_id: int) -> bool:
        """Get the mute status of the group.

        References:
            4.3.8 Get Group Mute"""
        result = await self._connection.command(
            HeosCommand(c.COMMAND_GET_GROUP_MUTE, {c.ATTR_GROUP_ID: group_id})
        )
        return result.get_message_value(c.ATTR_STATE) == c.VALUE_ON

    async def group_set_mute(self, group_id: int, state: bool) -> None:
        """Set the mute state of the group.

        References:
            4.3.9 Set Group Mute"""
        await self._connection.command(
            HeosCommand(
                c.COMMAND_SET_GROUP_MUTE,
                {
                    c.ATTR_GROUP_ID: group_id,
                    c.ATTR_STATE: c.VALUE_ON if state else c.VALUE_OFF,
                },
            )
        )

    async def group_toggle_mute(self, group_id: int) -> None:
        """Toggle the mute state.

        References:
            4.3.10 Toggle Group Mute"""
        await self._connection.command(
            HeosCommand(c.COMMAND_GROUP_TOGGLE_MUTE, {c.ATTR_GROUP_ID: group_id})
        )
