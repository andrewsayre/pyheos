"""
Define the browse command module.

This module creates HEOS browse commands.

Commands not currently implemented:
    4.2.2 Get Player Info

"""

from pyheos import const
from pyheos.message import HeosCommand


class PlayerCommands:
    """Define functions for creating player commands."""

    @staticmethod
    def get_players() -> HeosCommand:
        """
        Get players.

        References:
            4.2.1 Get Players
        """
        return HeosCommand(const.COMMAND_GET_PLAYERS)

    @staticmethod
    def get_player_state(player_id: int) -> HeosCommand:
        """Get the state of the player.

        References:
            4.2.3 Get Play State"""
        return HeosCommand(
            const.COMMAND_GET_PLAY_STATE, {const.ATTR_PLAYER_ID: player_id}
        )

    @staticmethod
    def set_player_state(player_id: int, state: str) -> HeosCommand:
        """Set the state of the player.

        References:
            4.2.4 Set Play State"""
        if state not in const.VALID_PLAY_STATES:
            raise ValueError("Invalid play state: " + state)
        return HeosCommand(
            const.COMMAND_SET_PLAY_STATE,
            {const.ATTR_PLAYER_ID: player_id, const.ATTR_STATE: state},
        )

    @staticmethod
    def get_now_playing_media(player_id: int) -> HeosCommand:
        """Get the now playing media information.

        References:
            4.2.5 Get Now Playing Media"""
        return HeosCommand(
            const.COMMAND_GET_NOW_PLAYING_MEDIA, {const.ATTR_PLAYER_ID: player_id}
        )

    @staticmethod
    def get_volume(player_id: int) -> HeosCommand:
        """Get the volume level of the player.

        References:
            4.2.6 Get Volume"""
        return HeosCommand(const.COMMAND_GET_VOLUME, {const.ATTR_PLAYER_ID: player_id})

    @staticmethod
    def set_volume(player_id: int, level: int) -> HeosCommand:
        """Set the volume of the player.

        References:
            4.2.7 Set Volume"""
        if level < 0 or level > 100:
            raise ValueError("'level' must be in the range 0-100")
        return HeosCommand(
            const.COMMAND_SET_VOLUME,
            {const.ATTR_PLAYER_ID: player_id, const.ATTR_LEVEL: level},
        )

    @staticmethod
    def volume_up(player_id: int, step: int = const.DEFAULT_STEP) -> HeosCommand:
        """Increase the volume level.

        References:
            4.2.8 Volume Up"""
        if step < 1 or step > 10:
            raise ValueError("'step' must be in the range 1-10")
        return HeosCommand(
            const.COMMAND_VOLUME_UP,
            {const.ATTR_PLAYER_ID: player_id, const.ATTR_STEP: step},
        )

    @staticmethod
    def volume_down(player_id: int, step: int = const.DEFAULT_STEP) -> HeosCommand:
        """Increase the volume level.

        References:
            4.2.9 Volume Down"""
        if step < 1 or step > 10:
            raise ValueError("'step' must be in the range 1-10")
        return HeosCommand(
            const.COMMAND_VOLUME_DOWN,
            {const.ATTR_PLAYER_ID: player_id, const.ATTR_STEP: step},
        )

    @staticmethod
    def get_mute(player_id: int) -> HeosCommand:
        """Get the mute state of the player.

        References:
            4.2.10 Get Mute"""
        return HeosCommand(const.COMMAND_GET_MUTE, {const.ATTR_PLAYER_ID: player_id})

    @staticmethod
    def set_mute(player_id: int, state: bool) -> HeosCommand:
        """Set the mute state of the player.

        References:
            4.2.11 Set Mute"""
        return HeosCommand(
            const.COMMAND_SET_MUTE,
            {
                const.ATTR_PLAYER_ID: player_id,
                const.ATTR_STATE: const.VALUE_ON if state else const.VALUE_OFF,
            },
        )

    @staticmethod
    def toggle_mute(player_id: int) -> HeosCommand:
        """Toggle the mute state.

        References:
            4.2.12 Toggle Mute"""
        return HeosCommand(const.COMMAND_TOGGLE_MUTE, {const.ATTR_PLAYER_ID: player_id})

    @staticmethod
    def get_play_mode(player_id: int) -> HeosCommand:
        """Get the current play mode.

        References:
            4.2.13 Get Play Mode"""
        return HeosCommand(
            const.COMMAND_GET_PLAY_MODE, {const.ATTR_PLAYER_ID: player_id}
        )

    @staticmethod
    def set_play_mode(
        player_id: int, repeat: const.RepeatType, shuffle: bool
    ) -> HeosCommand:
        """Set the current play mode.

        References:
            4.2.14 Set Play Mode"""
        return HeosCommand(
            const.COMMAND_SET_PLAY_MODE,
            {
                const.ATTR_PLAYER_ID: player_id,
                const.ATTR_REPEAT: repeat,
                const.ATTR_SHUFFLE: const.VALUE_ON if shuffle else const.VALUE_OFF,
            },
        )
