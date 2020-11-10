"""Define the HEOS command module."""
from typing import Optional, Sequence, Tuple

from . import const


class HeosCommands:
    """Define a class that encapsulates well-known commands."""

    def __init__(self, connection):
        """Init the command wrapper."""
        self._connection = connection

    async def heart_beat(self):
        """Perform heart beat command."""
        await self._connection.command(const.COMMAND_HEART_BEAT, None)

    async def check_account(self) -> Optional[str]:
        """Return the logged in username."""
        response = await self._connection.command(const.COMMAND_ACCOUNT_CHECK, None)
        if response.has_message("signed_in"):
            return response.get_message("un")
        return None

    async def sign_in(self, username: str, password: str):
        """Sign in to the HEOS account using the provided credential."""
        params = {"un": username, "pw": password}
        await self._connection.command(const.COMMAND_SIGN_IN, params)

    async def sign_out(self):
        """Sign out of the HEOS account."""
        await self._connection.command(const.COMMAND_SIGN_OUT, None)

    async def register_for_change_events(self, enable=True):
        """Enable or disable change event notifications."""
        params = {"enable": "on" if enable else "off"}
        await self._connection.command(const.COMMAND_REGISTER_FOR_CHANGE_EVENTS, params)

    async def get_players(self) -> Sequence[dict]:
        """Get players."""
        response = await self._connection.command(const.COMMAND_GET_PLAYERS)
        return response.payload

    async def get_player_state(self, player_id: int) -> str:
        """Get the state of the player."""
        params = {"pid": player_id}
        response = await self._connection.command(const.COMMAND_GET_PLAY_STATE, params)
        return response.get_message("state")

    async def set_player_state(self, player_id: int, state: str):
        """Set the state of the player."""
        if state not in const.VALID_PLAY_STATES:
            raise ValueError("Invalid play state: " + state)
        params = {"pid": player_id, "state": state}
        await self._connection.command(const.COMMAND_SET_PLAY_STATE, params)

    async def get_now_playing_state(self, player_id: int):
        """Get the now playing media information."""
        params = {"pid": player_id}
        response = await self._connection.command(
            const.COMMAND_GET_NOW_PLAYING_MEDIA, params
        )
        return response.payload

    async def get_volume(self, player_id: int) -> int:
        """Get the volume of the player."""
        params = {"pid": player_id}
        response = await self._connection.command(const.COMMAND_GET_VOLUME, params)
        return int(float(response.get_message("level")))

    async def set_volume(self, player_id: int, level: int):
        """Set the volume of the player."""
        if level < 0 or level > 100:
            raise ValueError("'level' must be in the range 0-100")
        params = {"pid": player_id, "level": level}
        await self._connection.command(const.COMMAND_SET_VOLUME, params)

    async def get_mute(self, player_id: str) -> bool:
        """Get the mute state of the player."""
        params = {"pid": player_id}
        response = await self._connection.command(const.COMMAND_GET_MUTE, params)
        return response.get_message("state") == "on"

    async def set_mute(self, player_id: str, state: bool):
        """Set the mute state of the player."""
        params = {"pid": player_id, "state": "on" if state else "off"}
        await self._connection.command(const.COMMAND_SET_MUTE, params)

    async def volume_up(self, player_id: int, step: int = const.DEFAULT_STEP):
        """Increase the volume level."""
        if step < 1 or step > 10:
            raise ValueError("'step' must be in the range 1-10")
        params = {"pid": player_id, "step": step}
        await self._connection.command(const.COMMAND_VOLUME_UP, params)

    async def volume_down(self, player_id: int, step: int = const.DEFAULT_STEP):
        """Increase the volume level."""
        if step < 1 or step > 10:
            raise ValueError("'step' must be in the range 1-10")
        params = {"pid": player_id, "step": step}
        await self._connection.command(const.COMMAND_VOLUME_DOWN, params)

    async def toggle_mute(self, player_id: int):
        """Toggle the mute state.."""
        params = {"pid": player_id}
        await self._connection.command(const.COMMAND_TOGGLE_MUTE, params)

    async def get_play_mode(self, player_id: int) -> Tuple[str, bool]:
        """Get the current play mode."""
        params = {"pid": player_id}
        response = await self._connection.command(const.COMMAND_GET_PLAY_MODE, params)
        repeat = response.get_message("repeat")
        shuffle = response.get_message("shuffle") == "on"
        return repeat, shuffle

    async def set_play_mode(self, player_id: int, repeat: str, shuffle: bool):
        """Set the current play mode."""
        if repeat not in const.VALID_REPEAT_MODES:
            raise ValueError("Invalid repeat mode: " + repeat)
        params = {
            "pid": player_id,
            "repeat": repeat,
            "shuffle": "on" if shuffle else "off",
        }
        await self._connection.command(const.COMMAND_SET_PLAY_MODE, params)

    async def clear_queue(self, player_id: int):
        """Clear the queue."""
        params = {"pid": player_id}
        await self._connection.command(const.COMMAND_CLEAR_QUEUE, params)

    async def play_next(self, player_id: int):
        """Play next."""
        params = {"pid": player_id}
        await self._connection.command(const.COMMAND_PLAY_NEXT, params)

    async def play_previous(self, player_id: int):
        """Play next."""
        params = {"pid": player_id}
        await self._connection.command(const.COMMAND_PLAY_PREVIOUS, params)

    async def get_music_sources(self) -> Sequence[dict]:
        """Get available music sources."""
        response = await self._connection.command(const.COMMAND_BROWSE_GET_SOURCES)
        return response.payload

    async def browse(self, source_id: int) -> Sequence[dict]:
        """Browse a music source."""
        params = {"sid": source_id}
        response = await self._connection.command(const.COMMAND_BROWSE_BROWSE, params)
        return response.payload

    async def play_input(
        self, player_id: int, input_name: str, *, source_player_id: int = None
    ):
        """Play the specified input source."""
        if input_name not in const.VALID_INPUTS:
            raise ValueError("Invalid input name: " + input_name)
        params = {
            "pid": player_id,
            "spid": source_player_id or player_id,
            "input": input_name,
        }
        await self._connection.command(const.COMMAND_BROWSE_PLAY_INPUT, params)

    async def play_preset(self, player_id: int, preset: int):
        """Play the specified preset by 1-based index."""
        if preset < 1:
            raise ValueError("Invalid preset: " + str(preset))
        params = {"pid": player_id, "preset": preset}
        await self._connection.command(const.COMMAND_BROWSE_PLAY_PRESET, params)

    async def play_stream(self, player_id: int, url: str):
        """Play the specified URL."""
        params = {"pid": player_id, "url": url}
        await self._connection.command(const.COMMAND_BROWSE_PLAY_STREAM, params)

    async def add_to_queue(
        self,
        player_id: int,
        source_id: int,
        container_id: str,
        add_queue_option: int,
        media_id: str = None,
    ):
        """Add the container or track to the queue."""
        if add_queue_option not in const.VALID_ADD_QUEUE_OPTIONS:
            raise ValueError("Invalid queue options: " + add_queue_option)
        params = {
            "pid": player_id,
            "sid": source_id,
            "cid": container_id,
            "aid": add_queue_option,
        }
        if media_id is not None:
            params["mid"] = media_id
        await self._connection.command(const.COMMAND_BROWSE_ADD_TO_QUEUE, params)

    async def get_groups(self) -> Sequence[dict]:
        """Get groups."""
        response = await self._connection.command(const.COMMAND_GET_GROUPS)
        return response.payload

    async def set_group(self, player_ids: Sequence[int]):
        """Create, modify, or ungroup players."""
        params = {"pid": ",".join(map(str, player_ids))}
        await self._connection.command(const.COMMAND_SET_GROUP, params)

    async def get_group_volume(self, group_id: int) -> int:
        """Get the volume of a group."""
        params = {"gid": group_id}
        response = await self._connection.command(
            const.COMMAND_GET_GROUP_VOLUME, params
        )
        return int(float(response.get_message("level")))

    async def get_group_mute(self, group_id: int) -> bool:
        """Get the mute status of the group."""
        params = {"gid": group_id}
        response = await self._connection.command(const.COMMAND_GET_GROUP_MUTE, params)
        return response.get_message("state") == "on"

    async def set_group_volume(self, group_id: int, level: int):
        """Set the volume of the group."""
        if level < 0 or level > 100:
            raise ValueError("'level' must be in the range 0-100")
        params = {"gid": group_id, "level": level}
        await self._connection.command(const.COMMAND_SET_GROUP_VOLUME, params)

    async def group_volume_up(self, group_id: int, step: int = const.DEFAULT_STEP):
        """Increase the volume level."""
        if step < 1 or step > 10:
            raise ValueError("'step' must be in the range 1-10")
        params = {"gid": group_id, "step": step}
        await self._connection.command(const.COMMAND_GROUP_VOLUME_UP, params)

    async def group_volume_down(self, group_id: int, step: int = const.DEFAULT_STEP):
        """Increase the volume level."""
        if step < 1 or step > 10:
            raise ValueError("'step' must be in the range 1-10")
        params = {"gid": group_id, "step": step}
        await self._connection.command(const.COMMAND_GROUP_VOLUME_DOWN, params)

    async def group_set_mute(self, group_id: str, state: bool):
        """Set the mute state of the group."""
        params = {"gid": group_id, "state": "on" if state else "off"}
        await self._connection.command(const.COMMAND_SET_GROUP_MUTE, params)

    async def group_toggle_mute(self, group_id: int):
        """Toggle the mute state."""
        params = {"gid": group_id}
        await self._connection.command(const.COMMAND_GROUP_TOGGLE_MUTE, params)

    async def play_quick_select(self, player_id: int, quick_select_id: int):
        """Play a quick select."""
        if quick_select_id < 1 or quick_select_id > 6:
            raise ValueError("'quick_select_id' must be in the range 1-6")
        params = {"pid": player_id, "id": quick_select_id}
        await self._connection.command(const.COMMAND_PLAY_QUICK_SELECT, params)

    async def set_quick_select(self, player_id: int, quick_select_id: int):
        """Play a quick select."""
        if quick_select_id < 1 or quick_select_id > 6:
            raise ValueError("'quick_select_id' must be in the range 1-6")
        params = {"pid": player_id, "id": quick_select_id}
        await self._connection.command(const.COMMAND_SET_QUICK_SELECT, params)

    async def get_quick_selects(self, player_id: int) -> Sequence[dict]:
        """Play a quick select."""
        params = {"pid": player_id}
        response = await self._connection.command(
            const.COMMAND_GET_QUICK_SELECTS, params
        )
        return response.payload
