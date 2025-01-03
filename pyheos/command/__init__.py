"""Define the HEOS command module."""

from collections.abc import Sequence
from typing import cast

from pyheos import const
from pyheos.connection import ConnectionBase, HeosCommand


class HeosCommands:
    """Define a class that encapsulates well-known commands and response processing."""

    def __init__(self, connection: ConnectionBase) -> None:
        """Initialize the command processor."""
        self._connection = connection

    async def get_groups(self) -> Sequence[dict]:
        """Get groups."""
        response = await self._connection.command(HeosCommand(const.COMMAND_GET_GROUPS))
        return cast(Sequence[dict], response.payload)

    async def set_group(self, player_ids: Sequence[int]) -> None:
        """Create, modify, or ungroup players."""
        params = {const.ATTR_PLAYER_ID: ",".join(map(str, player_ids))}
        await self._connection.command(HeosCommand(const.COMMAND_SET_GROUP, params))

    async def get_group_volume(self, group_id: int) -> int:
        """Get the volume of a group."""
        params = {const.ATTR_GROUP_ID: group_id}
        response = await self._connection.command(
            HeosCommand(const.COMMAND_GET_GROUP_VOLUME, params)
        )
        return response.get_message_value_int(const.ATTR_LEVEL)

    async def get_group_mute(self, group_id: int) -> bool:
        """Get the mute status of the group."""
        params = {const.ATTR_GROUP_ID: group_id}
        response = await self._connection.command(
            HeosCommand(const.COMMAND_GET_GROUP_MUTE, params)
        )
        return response.get_message_value(const.ATTR_STATE) == const.VALUE_ON

    async def set_group_volume(self, group_id: int, level: int) -> None:
        """Set the volume of the group."""
        if level < 0 or level > 100:
            raise ValueError("'level' must be in the range 0-100")
        params = {const.ATTR_GROUP_ID: group_id, const.ATTR_LEVEL: level}
        await self._connection.command(
            HeosCommand(const.COMMAND_SET_GROUP_VOLUME, params)
        )

    async def group_volume_up(
        self, group_id: int, step: int = const.DEFAULT_STEP
    ) -> None:
        """Increase the volume level."""
        if step < 1 or step > 10:
            raise ValueError("'step' must be in the range 1-10")
        params = {const.ATTR_GROUP_ID: group_id, const.ATTR_STEP: step}
        await self._connection.command(
            HeosCommand(const.COMMAND_GROUP_VOLUME_UP, params)
        )

    async def group_volume_down(
        self, group_id: int, step: int = const.DEFAULT_STEP
    ) -> None:
        """Increase the volume level."""
        if step < 1 or step > 10:
            raise ValueError("'step' must be in the range 1-10")
        params = {const.ATTR_GROUP_ID: group_id, const.ATTR_STEP: step}
        await self._connection.command(
            HeosCommand(const.COMMAND_GROUP_VOLUME_DOWN, params)
        )

    async def group_set_mute(self, group_id: int, state: bool) -> None:
        """Set the mute state of the group."""
        params = {
            const.ATTR_GROUP_ID: group_id,
            const.ATTR_STATE: const.VALUE_ON if state else const.VALUE_OFF,
        }
        await self._connection.command(
            HeosCommand(const.COMMAND_SET_GROUP_MUTE, params)
        )

    async def group_toggle_mute(self, group_id: int) -> None:
        """Toggle the mute state."""
        params = {const.ATTR_GROUP_ID: group_id}
        await self._connection.command(
            HeosCommand(const.COMMAND_GROUP_TOGGLE_MUTE, params)
        )
