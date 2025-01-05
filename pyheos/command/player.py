"""
Define the player command module.

This module creates HEOS player commands.

Commands not currently implemented:
    4.2.2 Get Player Info
    4.2.15 Get Queue
    4.2.16 Play Queue Item
    4.2.17 Remove Item(s) from Queue
    4.2.18 Save Queue as Playlist
    4.2.20 Move Queue
    4.2.26 Check for Firmware Update

"""

from pyheos import command, const
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
        return HeosCommand(command.COMMAND_GET_PLAYERS)

    @staticmethod
    def get_play_state(player_id: int) -> HeosCommand:
        """Get the state of the player.

        References:
            4.2.3 Get Play State"""
        return HeosCommand(
            command.COMMAND_GET_PLAY_STATE, {const.ATTR_PLAYER_ID: player_id}
        )

    @staticmethod
    def set_play_state(player_id: int, state: const.PlayState) -> HeosCommand:
        """Set the state of the player.

        References:
            4.2.4 Set Play State"""
        return HeosCommand(
            command.COMMAND_SET_PLAY_STATE,
            {const.ATTR_PLAYER_ID: player_id, const.ATTR_STATE: state},
        )

    @staticmethod
    def get_now_playing_media(player_id: int) -> HeosCommand:
        """Get the now playing media information.

        References:
            4.2.5 Get Now Playing Media"""
        return HeosCommand(
            command.COMMAND_GET_NOW_PLAYING_MEDIA, {const.ATTR_PLAYER_ID: player_id}
        )

    @staticmethod
    def get_volume(player_id: int) -> HeosCommand:
        """Get the volume level of the player.

        References:
            4.2.6 Get Volume"""
        return HeosCommand(
            command.COMMAND_GET_VOLUME, {const.ATTR_PLAYER_ID: player_id}
        )

    @staticmethod
    def set_volume(player_id: int, level: int) -> HeosCommand:
        """Set the volume of the player.

        References:
            4.2.7 Set Volume"""
        if level < 0 or level > 100:
            raise ValueError("'level' must be in the range 0-100")
        return HeosCommand(
            command.COMMAND_SET_VOLUME,
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
            command.COMMAND_VOLUME_UP,
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
            command.COMMAND_VOLUME_DOWN,
            {const.ATTR_PLAYER_ID: player_id, const.ATTR_STEP: step},
        )

    @staticmethod
    def get_mute(player_id: int) -> HeosCommand:
        """Get the mute state of the player.

        References:
            4.2.10 Get Mute"""
        return HeosCommand(command.COMMAND_GET_MUTE, {const.ATTR_PLAYER_ID: player_id})

    @staticmethod
    def set_mute(player_id: int, state: bool) -> HeosCommand:
        """Set the mute state of the player.

        References:
            4.2.11 Set Mute"""
        return HeosCommand(
            command.COMMAND_SET_MUTE,
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
        return HeosCommand(
            command.COMMAND_TOGGLE_MUTE, {const.ATTR_PLAYER_ID: player_id}
        )

    @staticmethod
    def get_play_mode(player_id: int) -> HeosCommand:
        """Get the current play mode.

        References:
            4.2.13 Get Play Mode"""
        return HeosCommand(
            command.COMMAND_GET_PLAY_MODE, {const.ATTR_PLAYER_ID: player_id}
        )

    @staticmethod
    def set_play_mode(
        player_id: int, repeat: const.RepeatType, shuffle: bool
    ) -> HeosCommand:
        """Set the current play mode.

        References:
            4.2.14 Set Play Mode"""
        return HeosCommand(
            command.COMMAND_SET_PLAY_MODE,
            {
                const.ATTR_PLAYER_ID: player_id,
                const.ATTR_REPEAT: repeat,
                const.ATTR_SHUFFLE: const.VALUE_ON if shuffle else const.VALUE_OFF,
            },
        )

    @staticmethod
    def clear_queue(player_id: int) -> HeosCommand:
        """Clear the queue.

        References:
            4.2.19 Clear Queue"""
        return HeosCommand(
            command.COMMAND_CLEAR_QUEUE, {const.ATTR_PLAYER_ID: player_id}
        )

    @staticmethod
    def play_next(player_id: int) -> HeosCommand:
        """Play next.

        References:
            4.2.21 Play Next"""
        return HeosCommand(command.COMMAND_PLAY_NEXT, {const.ATTR_PLAYER_ID: player_id})

    @staticmethod
    def play_previous(player_id: int) -> HeosCommand:
        """Play next.

        References:
            4.2.22 Play Previous"""
        return HeosCommand(
            command.COMMAND_PLAY_PREVIOUS, {const.ATTR_PLAYER_ID: player_id}
        )

    @staticmethod
    def set_quick_select(player_id: int, quick_select_id: int) -> HeosCommand:
        """Play a quick select.

        References:
            4.2.23 Set QuickSelect"""
        if quick_select_id < 1 or quick_select_id > 6:
            raise ValueError("'quick_select_id' must be in the range 1-6")
        return HeosCommand(
            command.COMMAND_SET_QUICK_SELECT,
            {const.ATTR_PLAYER_ID: player_id, const.ATTR_ID: quick_select_id},
        )

    @staticmethod
    def play_quick_select(player_id: int, quick_select_id: int) -> HeosCommand:
        """Play a quick select.

        References:
            4.2.24 Play QuickSelect"""
        if quick_select_id < 1 or quick_select_id > 6:
            raise ValueError("'quick_select_id' must be in the range 1-6")
        return HeosCommand(
            command.COMMAND_PLAY_QUICK_SELECT,
            {const.ATTR_PLAYER_ID: player_id, const.ATTR_ID: quick_select_id},
        )

    @staticmethod
    def get_quick_selects(player_id: int) -> HeosCommand:
        """Get quick selects.

        References:
            4.2.25 Get QuickSelects"""
        return HeosCommand(
            command.COMMAND_GET_QUICK_SELECTS, {const.ATTR_PLAYER_ID: player_id}
        )
