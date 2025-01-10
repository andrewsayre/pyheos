"""
Define the group command module.

This module creates HEOS group commands.
"""

from collections.abc import Sequence

from pyheos import command
from pyheos.message import HeosCommand


class GroupCommands:
    """Define functions for creating group commands."""

    @staticmethod
    def get_groups() -> HeosCommand:
        """Create a get groups command.

        References:
            4.3.1 Get Groups"""
        return HeosCommand(command.COMMAND_GET_GROUPS)

    @staticmethod
    def get_group_info(group_id: int) -> HeosCommand:
        """Get information about a group.

        References:
            4.3.2 Get Group Info"""
        return HeosCommand(
            command.COMMAND_GET_GROUP_INFO, {command.ATTR_GROUP_ID: group_id}
        )

    @staticmethod
    def set_group(player_ids: Sequence[int]) -> HeosCommand:
        """Create, modify, or ungroup players.

        References:
            4.3.3 Set Group"""
        return HeosCommand(
            command.COMMAND_SET_GROUP,
            {command.ATTR_PLAYER_ID: ",".join(map(str, player_ids))},
        )

    @staticmethod
    def get_group_volume(group_id: int) -> HeosCommand:
        """
        Get the volume of a group.

        References:
            4.3.4 Get Group Volume
        """
        return HeosCommand(
            command.COMMAND_GET_GROUP_VOLUME, {command.ATTR_GROUP_ID: group_id}
        )

    @staticmethod
    def set_group_volume(group_id: int, level: int) -> HeosCommand:
        """Set the volume of the group.

        References:
            4.3.5 Set Group Volume"""
        if level < 0 or level > 100:
            raise ValueError("'level' must be in the range 0-100")
        return HeosCommand(
            command.COMMAND_SET_GROUP_VOLUME,
            {command.ATTR_GROUP_ID: group_id, command.ATTR_LEVEL: level},
        )

    @staticmethod
    def group_volume_up(group_id: int, step: int) -> HeosCommand:
        """Increase the volume level.

        References:
            4.3.6 Group Volume Up"""
        if step < 1 or step > 10:
            raise ValueError("'step' must be in the range 1-10")
        return HeosCommand(
            command.COMMAND_GROUP_VOLUME_UP,
            {command.ATTR_GROUP_ID: group_id, command.ATTR_STEP: step},
        )

    @staticmethod
    def group_volume_down(group_id: int, step: int) -> HeosCommand:
        """Increase the volume level.

        References:
            4.2.7 Group Volume Down"""
        if step < 1 or step > 10:
            raise ValueError("'step' must be in the range 1-10")
        return HeosCommand(
            command.COMMAND_GROUP_VOLUME_DOWN,
            {command.ATTR_GROUP_ID: group_id, command.ATTR_STEP: step},
        )

    @staticmethod
    def get_group_mute(group_id: int) -> HeosCommand:
        """Get the mute status of the group.

        References:
            4.3.8 Get Group Mute"""
        return HeosCommand(
            command.COMMAND_GET_GROUP_MUTE, {command.ATTR_GROUP_ID: group_id}
        )

    @staticmethod
    def group_set_mute(group_id: int, state: bool) -> HeosCommand:
        """Set the mute state of the group.

        References:
            4.3.9 Set Group Mute"""
        return HeosCommand(
            command.COMMAND_SET_GROUP_MUTE,
            {
                command.ATTR_GROUP_ID: group_id,
                command.ATTR_STATE: command.VALUE_ON if state else command.VALUE_OFF,
            },
        )

    @staticmethod
    def group_toggle_mute(group_id: int) -> HeosCommand:
        """Toggle the mute state.

        References:
            4.3.10 Toggle Group Mute"""
        return HeosCommand(
            command.COMMAND_GROUP_TOGGLE_MUTE, {command.ATTR_GROUP_ID: group_id}
        )
