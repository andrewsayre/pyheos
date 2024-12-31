"""Define the HEOS command module."""

from collections.abc import Sequence
from typing import Any, Final, Optional, cast

from pyheos import const
from pyheos.connection import ConnectionBase, HeosCommand


class HeosCommands:
    """Define a class that encapsulates well-known commands and response processing."""

    def __init__(self, connection: ConnectionBase) -> None:
        """Initialize the command processor."""
        self._connection = connection

    _account_check_command: Final = HeosCommand(const.COMMAND_ACCOUNT_CHECK)

    async def register_for_change_events(self, enable: bool = True) -> None:
        """Register for change events."""
        await self._connection.command(
            HeosCommand(
                const.COMMAND_REGISTER_FOR_CHANGE_EVENTS,
                {const.ATTR_ENABLE: const.VALUE_ON if enable else const.VALUE_OFF},
            )
        )

    async def check_account(self) -> Optional[str]:
        """Return the logged in username."""
        response = await self._connection.command(HeosCommands._account_check_command)
        if const.ATTR_SIGNED_IN in response.message:
            return response.get_message_value(const.ATTR_USER_NAME)
        return None

    async def sign_in(self, username: str, password: str) -> str:
        """Sign in to the HEOS account using the provided credential and return the user name."""
        params = {const.ATTR_USER_NAME: username, const.ATTR_PASSWORD: password}
        response = await self._connection.command(
            HeosCommand(const.COMMAND_SIGN_IN, params)
        )
        return response.get_message_value(const.ATTR_USER_NAME)

    async def sign_out(self) -> None:
        """Sign out of the HEOS account."""
        await self._connection.command(HeosCommand(const.COMMAND_SIGN_OUT))

    async def get_players(self) -> Sequence[dict]:
        """Get players."""
        response = await self._connection.command(
            HeosCommand(const.COMMAND_GET_PLAYERS)
        )
        return cast(Sequence[dict], response.payload)

    async def get_player_state(self, player_id: int) -> str:
        """Get the state of the player."""
        params = {const.ATTR_PLAYER_ID: player_id}
        response = await self._connection.command(
            HeosCommand(const.COMMAND_GET_PLAY_STATE, params)
        )
        return str(response.message.get(const.ATTR_STATE))

    async def set_player_state(self, player_id: int, state: str) -> None:
        """Set the state of the player."""
        if state not in const.VALID_PLAY_STATES:
            raise ValueError("Invalid play state: " + state)
        params = {const.ATTR_PLAYER_ID: player_id, const.ATTR_STATE: state}
        await self._connection.command(
            HeosCommand(const.COMMAND_SET_PLAY_STATE, params)
        )

    async def get_now_playing_state(self, player_id: int) -> dict[str, Any]:
        """Get the now playing media information."""
        params = {const.ATTR_PLAYER_ID: player_id}
        response = await self._connection.command(
            HeosCommand(const.COMMAND_GET_NOW_PLAYING_MEDIA, params)
        )
        assert isinstance(response.payload, dict)
        return response.payload

    async def get_volume(self, player_id: int) -> int:
        """Get the volume of the player."""
        params = {const.ATTR_PLAYER_ID: player_id}
        response = await self._connection.command(
            HeosCommand(const.COMMAND_GET_VOLUME, params)
        )
        return response.get_message_value_int(const.ATTR_LEVEL)

    async def set_volume(self, player_id: int, level: int) -> None:
        """Set the volume of the player."""
        if level < 0 or level > 100:
            raise ValueError("'level' must be in the range 0-100")
        params = {const.ATTR_PLAYER_ID: player_id, const.ATTR_LEVEL: level}
        await self._connection.command(HeosCommand(const.COMMAND_SET_VOLUME, params))

    async def get_mute(self, player_id: int) -> bool:
        """Get the mute state of the player."""
        params = {const.ATTR_PLAYER_ID: player_id}
        response = await self._connection.command(
            HeosCommand(const.COMMAND_GET_MUTE, params)
        )
        return str(response.message.get(const.ATTR_STATE)) == const.VALUE_ON

    async def set_mute(self, player_id: int, state: bool) -> None:
        """Set the mute state of the player."""
        params = {
            const.ATTR_PLAYER_ID: player_id,
            const.ATTR_STATE: const.VALUE_ON if state else const.VALUE_OFF,
        }
        await self._connection.command(HeosCommand(const.COMMAND_SET_MUTE, params))

    async def volume_up(self, player_id: int, step: int = const.DEFAULT_STEP) -> None:
        """Increase the volume level."""
        if step < 1 or step > 10:
            raise ValueError("'step' must be in the range 1-10")
        params = {const.ATTR_PLAYER_ID: player_id, const.ATTR_STEP: step}
        await self._connection.command(HeosCommand(const.COMMAND_VOLUME_UP, params))

    async def volume_down(self, player_id: int, step: int = const.DEFAULT_STEP) -> None:
        """Increase the volume level."""
        if step < 1 or step > 10:
            raise ValueError("'step' must be in the range 1-10")
        params = {const.ATTR_PLAYER_ID: player_id, const.ATTR_STEP: step}
        await self._connection.command(HeosCommand(const.COMMAND_VOLUME_DOWN, params))

    async def toggle_mute(self, player_id: int) -> None:
        """Toggle the mute state.."""
        params = {const.ATTR_PLAYER_ID: player_id}
        await self._connection.command(HeosCommand(const.COMMAND_TOGGLE_MUTE, params))

    async def get_play_mode(self, player_id: int) -> tuple[const.RepeatType, bool]:
        """Get the current play mode."""
        params = {const.ATTR_PLAYER_ID: player_id}
        response = await self._connection.command(
            HeosCommand(const.COMMAND_GET_PLAY_MODE, params)
        )
        repeat = const.RepeatType(response.get_message_value(const.ATTR_REPEAT))
        shuffle = response.get_message_value(const.ATTR_SHUFFLE) == const.VALUE_ON
        return repeat, shuffle

    async def set_play_mode(
        self, player_id: int, repeat: const.RepeatType, shuffle: bool
    ) -> None:
        """Set the current play mode."""
        params = {
            const.ATTR_PLAYER_ID: player_id,
            const.ATTR_REPEAT: repeat,
            const.ATTR_SHUFFLE: const.VALUE_ON if shuffle else const.VALUE_OFF,
        }
        await self._connection.command(HeosCommand(const.COMMAND_SET_PLAY_MODE, params))

    async def clear_queue(self, player_id: int) -> None:
        """Clear the queue."""
        params = {const.ATTR_PLAYER_ID: player_id}
        await self._connection.command(HeosCommand(const.COMMAND_CLEAR_QUEUE, params))

    async def play_next(self, player_id: int) -> None:
        """Play next."""
        params = {const.ATTR_PLAYER_ID: player_id}
        await self._connection.command(HeosCommand(const.COMMAND_PLAY_NEXT, params))

    async def play_previous(self, player_id: int) -> None:
        """Play next."""
        params = {const.ATTR_PLAYER_ID: player_id}
        await self._connection.command(HeosCommand(const.COMMAND_PLAY_PREVIOUS, params))

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

    async def play_quick_select(self, player_id: int, quick_select_id: int) -> None:
        """Play a quick select."""
        if quick_select_id < 1 or quick_select_id > 6:
            raise ValueError("'quick_select_id' must be in the range 1-6")
        params = {const.ATTR_PLAYER_ID: player_id, const.ATTR_ID: quick_select_id}
        await self._connection.command(
            HeosCommand(const.COMMAND_PLAY_QUICK_SELECT, params)
        )

    async def set_quick_select(self, player_id: int, quick_select_id: int) -> None:
        """Play a quick select."""
        if quick_select_id < 1 or quick_select_id > 6:
            raise ValueError("'quick_select_id' must be in the range 1-6")
        params = {const.ATTR_PLAYER_ID: player_id, const.ATTR_ID: quick_select_id}
        await self._connection.command(
            HeosCommand(const.COMMAND_SET_QUICK_SELECT, params)
        )

    async def get_quick_selects(self, player_id: int) -> Sequence[dict]:
        """Play a quick select."""
        params = {const.ATTR_PLAYER_ID: player_id}
        response = await self._connection.command(
            HeosCommand(const.COMMAND_GET_QUICK_SELECTS, params)
        )
        return cast(Sequence[dict], response.payload)
