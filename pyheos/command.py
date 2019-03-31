"""Define the HEOS command module."""
from typing import Sequence, Tuple

from . import const
from .player import HeosNowPlayingMedia


class HeosCommands:
    """Define a class that encapsulates well-known commands."""

    def __init__(self, connection):
        """Init the command wrapper."""
        self._connection = connection

    async def heart_beat(self, *, raise_for_result=False) -> bool:
        """Perform heart beat command."""
        response = await self._connection.command(
            const.COMMAND_HEART_BEAT, raise_for_result,
            raise_for_result=raise_for_result)
        return response.result

    async def register_for_change_events(
            self, enable=True, *, raise_for_result=False) -> bool:
        """Enable or disable change event notifications."""
        params = {
            'enable': "on" if enable else "off"
        }
        response = await self._connection.command(
            const.COMMAND_REGISTER_FOR_CHANGE_EVENTS, params,
            raise_for_result=raise_for_result)
        return response.result

    async def get_players(self) -> Sequence[dict]:
        """Get players."""
        response = await self._connection.command(
            const.COMMAND_GET_PLAYERS, raise_for_result=True)
        return response.payload

    async def get_player_state(self, player_id: int) -> str:
        """Get the state of the player."""
        params = {
            'pid': player_id
        }
        response = await self._connection.command(
            const.COMMAND_GET_PLAY_STATE, params, raise_for_result=True)
        return response.get_message('state')

    async def set_player_state(self, player_id: int, state: str,
                               *, raise_for_result=False) -> bool:
        """Set the state of the player."""
        if state not in const.VALID_PLAY_STATES:
            raise ValueError("Invalid play state: " + state)
        params = {
            'pid': player_id,
            'state': state
        }
        response = await self._connection.command(
            const.COMMAND_SET_PLAY_STATE, params,
            raise_for_result=raise_for_result)
        return response.result

    async def get_now_playing_state(
            self, player_id: int,
            now_playing_media: HeosNowPlayingMedia):
        """Get the now playing media information."""
        params = {
            'pid': player_id
        }
        response = await self._connection.command(
            const.COMMAND_GET_NOW_PLAYING_MEDIA, params, raise_for_result=True)
        now_playing_media.from_data(response.payload)

    async def get_volume(self, player_id: int) -> int:
        """Get the volume of the player."""
        params = {
            'pid': player_id
        }
        response = await self._connection.command(
            const.COMMAND_GET_VOLUME, params, raise_for_result=True)
        return int(response.get_message('level'))

    async def set_volume(self, player_id: int, level: int,
                         *, raise_for_result=False) -> bool:
        """Set the volume of the player."""
        if level < 0 or level > 100:
            raise ValueError("'level' must be in the range 0-100")
        params = {
            'pid': player_id,
            'level': level
        }
        response = await self._connection.command(
            const.COMMAND_SET_VOLUME, params,
            raise_for_result=raise_for_result)
        return response.result

    async def get_mute(self, player_id: str) -> bool:
        """Get the mute state of the player."""
        params = {
            'pid': player_id
        }
        response = await self._connection.command(
            const.COMMAND_GET_MUTE, params, raise_for_result=True)
        return response.get_message('state') == 'on'

    async def set_mute(self, player_id: str, state: bool,
                       *, raise_for_result=False) -> bool:
        """Set the mute state of the player."""
        params = {
            'pid': player_id,
            'state': "on" if state else "off"
        }
        response = await self._connection.command(
            const.COMMAND_SET_MUTE, params,
            raise_for_result=raise_for_result)
        return response.result

    async def volume_up(self, player_id: int,
                        step: int = const.DEFAULT_STEP,
                        *, raise_for_result=False) -> bool:
        """Increase the volume level."""
        if step < 1 or step > 10:
            raise ValueError("'step' must be in the range 1-10")
        params = {
            'pid': player_id,
            'step': step
        }
        response = await self._connection.command(
            const.COMMAND_VOLUME_UP, params,
            raise_for_result=raise_for_result)
        return response.result

    async def volume_down(self, player_id: int,
                          step: int = const.DEFAULT_STEP,
                          *, raise_for_result=False) -> bool:
        """Increase the volume level."""
        if step < 1 or step > 10:
            raise ValueError("'step' must be in the range 1-10")
        params = {
            'pid': player_id,
            'step': step
        }
        response = await self._connection.command(
            const.COMMAND_VOLUME_DOWN, params,
            raise_for_result=raise_for_result)
        return response.result

    async def toggle_mute(self, player_id: int,
                          *, raise_for_result=False) -> bool:
        """Toggle the mute state.."""
        params = {
            'pid': player_id
        }
        response = await self._connection.command(
            const.COMMAND_TOGGLE_MUTE, params,
            raise_for_result=raise_for_result)
        return response.result

    async def get_play_mode(self, player_id: int) -> Tuple[str, bool]:
        """Get the current play mode."""
        params = {
            'pid': player_id
        }
        response = await self._connection.command(
            const.COMMAND_GET_PLAY_MODE, params, raise_for_result=True)
        repeat = response.get_message('repeat')
        shuffle = response.get_message('shuffle') == 'on'
        return repeat, shuffle

    async def set_play_mode(self, player_id: int, repeat: str,
                            shuffle: bool, *, raise_for_result=False):
        """Set the current play mode."""
        if repeat not in const.VALID_REPEAT_MODES:
            raise ValueError("Invalid repeat mode: " + repeat)
        params = {
            'pid': player_id,
            'repeat': repeat,
            'shuffle': 'on' if shuffle else 'off'
        }
        response = await self._connection.command(
            const.COMMAND_SET_PLAY_MODE, params,
            raise_for_result=raise_for_result)
        return response.result

    async def clear_queue(self, player_id: int,
                          *, raise_for_result=False) -> bool:
        """Clear the queue."""
        params = {
            'pid': player_id
        }
        response = await self._connection.command(
            const.COMMAND_CLEAR_QUEUE, params,
            raise_for_result=raise_for_result)
        return response.result

    async def play_next(self, player_id: int,
                        *, raise_for_result=False) -> bool:
        """Play next."""
        params = {
            'pid': player_id
        }
        response = await self._connection.command(
            const.COMMAND_PLAY_NEXT, params,
            raise_for_result=raise_for_result)
        return response.result

    async def play_previous(self, player_id: int,
                            *, raise_for_result=False) -> bool:
        """Play next."""
        params = {
            'pid': player_id
        }
        response = await self._connection.command(
            const.COMMAND_PLAY_PREVIOUS, params,
            raise_for_result=raise_for_result)
        return response.result

    async def get_music_sources(self) -> Sequence[dict]:
        """Get available music sources."""
        response = await self._connection.command(
            const.COMMAND_BROWSE_GET_SOURCES, raise_for_result=True)
        return response.payload

    async def browse(self, source_id: int) -> Sequence[dict]:
        """Browse a music source."""
        params = {
            'sid': source_id
        }
        response = await self._connection.command(
            const.COMMAND_BROWSE_BROWSE, params, raise_for_result=True)
        return response.payload

    async def play_input(self, player_id: int, input_name: str, *,
                         source_player_id: int = None,
                         raise_for_result=False) -> bool:
        """Play the specified input source."""
        if input_name not in const.VALID_INPUTS:
            raise ValueError("Invalid input name: " + input_name)
        params = {
            'pid': player_id,
            'spid': source_player_id or player_id,
            'input': input_name
        }
        response = await self._connection.command(
            const.COMMAND_BROWSE_PLAY_INPUT, params,
            raise_for_result=raise_for_result)
        return response.result

    async def play_preset(self, player_id: int, preset: int,
                          *, raise_for_result=False) -> bool:
        """Play the specified preset by 1-based index."""
        if preset < 1:
            raise ValueError("Invalid preset: " + str(preset))
        params = {
            'pid': player_id,
            'preset': preset
        }
        response = await self._connection.command(
            const.COMMAND_BROWSE_PLAY_PRESET, params,
            raise_for_result=raise_for_result)
        return response.result

    async def play_stream(self, player_id: int, url: str,
                          *, raise_for_result=False) -> bool:
        """Play the specified URL."""
        params = {
            'pid': player_id,
            'url': url
        }
        response = await self._connection.command(
            const.COMMAND_BROWSE_PLAY_STREAM, params,
            raise_for_result=raise_for_result)
        return response.result
