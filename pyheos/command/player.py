"""
Define the player command module.

This module creates HEOS player commands.
"""

from typing import Any

from pyheos import command as c
from pyheos.const import DEFAULT_STEP
from pyheos.message import HeosCommand
from pyheos.player import PlayState
from pyheos.types import RepeatType


class PlayerCommands:
    """Define functions for creating player commands."""

    @staticmethod
    def get_players() -> HeosCommand:
        """
        Get players.

        References:
            4.2.1 Get Players
        """
        return HeosCommand(c.COMMAND_GET_PLAYERS)

    @staticmethod
    def get_player_info(player_id: int) -> HeosCommand:
        """Get player information.

        References:
            4.2.2 Get Player Info"""
        return HeosCommand(c.COMMAND_GET_PLAYER_INFO, {c.ATTR_PLAYER_ID: player_id})

    @staticmethod
    def get_play_state(player_id: int) -> HeosCommand:
        """Get the state of the player.

        References:
            4.2.3 Get Play State"""
        return HeosCommand(c.COMMAND_GET_PLAY_STATE, {c.ATTR_PLAYER_ID: player_id})

    @staticmethod
    def set_play_state(player_id: int, state: PlayState) -> HeosCommand:
        """Set the state of the player.

        References:
            4.2.4 Set Play State"""
        return HeosCommand(
            c.COMMAND_SET_PLAY_STATE,
            {c.ATTR_PLAYER_ID: player_id, c.ATTR_STATE: state},
        )

    @staticmethod
    def get_now_playing_media(player_id: int) -> HeosCommand:
        """Get the now playing media information.

        References:
            4.2.5 Get Now Playing Media"""
        return HeosCommand(
            c.COMMAND_GET_NOW_PLAYING_MEDIA, {c.ATTR_PLAYER_ID: player_id}
        )

    @staticmethod
    def get_volume(player_id: int) -> HeosCommand:
        """Get the volume level of the player.

        References:
            4.2.6 Get Volume"""
        return HeosCommand(c.COMMAND_GET_VOLUME, {c.ATTR_PLAYER_ID: player_id})

    @staticmethod
    def set_volume(player_id: int, level: int) -> HeosCommand:
        """Set the volume of the player.

        References:
            4.2.7 Set Volume"""
        if level < 0 or level > 100:
            raise ValueError("'level' must be in the range 0-100")
        return HeosCommand(
            c.COMMAND_SET_VOLUME,
            {c.ATTR_PLAYER_ID: player_id, c.ATTR_LEVEL: level},
        )

    @staticmethod
    def volume_up(player_id: int, step: int = DEFAULT_STEP) -> HeosCommand:
        """Increase the volume level.

        References:
            4.2.8 Volume Up"""
        if step < 1 or step > 10:
            raise ValueError("'step' must be in the range 1-10")
        return HeosCommand(
            c.COMMAND_VOLUME_UP,
            {c.ATTR_PLAYER_ID: player_id, c.ATTR_STEP: step},
        )

    @staticmethod
    def volume_down(player_id: int, step: int = DEFAULT_STEP) -> HeosCommand:
        """Increase the volume level.

        References:
            4.2.9 Volume Down"""
        if step < 1 or step > 10:
            raise ValueError("'step' must be in the range 1-10")
        return HeosCommand(
            c.COMMAND_VOLUME_DOWN,
            {c.ATTR_PLAYER_ID: player_id, c.ATTR_STEP: step},
        )

    @staticmethod
    def get_mute(player_id: int) -> HeosCommand:
        """Get the mute state of the player.

        References:
            4.2.10 Get Mute"""
        return HeosCommand(c.COMMAND_GET_MUTE, {c.ATTR_PLAYER_ID: player_id})

    @staticmethod
    def set_mute(player_id: int, state: bool) -> HeosCommand:
        """Set the mute state of the player.

        References:
            4.2.11 Set Mute"""
        return HeosCommand(
            c.COMMAND_SET_MUTE,
            {
                c.ATTR_PLAYER_ID: player_id,
                c.ATTR_STATE: c.VALUE_ON if state else c.VALUE_OFF,
            },
        )

    @staticmethod
    def toggle_mute(player_id: int) -> HeosCommand:
        """Toggle the mute state.

        References:
            4.2.12 Toggle Mute"""
        return HeosCommand(c.COMMAND_TOGGLE_MUTE, {c.ATTR_PLAYER_ID: player_id})

    @staticmethod
    def get_play_mode(player_id: int) -> HeosCommand:
        """Get the current play mode.

        References:
            4.2.13 Get Play Mode"""
        return HeosCommand(c.COMMAND_GET_PLAY_MODE, {c.ATTR_PLAYER_ID: player_id})

    @staticmethod
    def set_play_mode(player_id: int, repeat: RepeatType, shuffle: bool) -> HeosCommand:
        """Set the current play mode.

        References:
            4.2.14 Set Play Mode"""
        return HeosCommand(
            c.COMMAND_SET_PLAY_MODE,
            {
                c.ATTR_PLAYER_ID: player_id,
                c.ATTR_REPEAT: repeat,
                c.ATTR_SHUFFLE: c.VALUE_ON if shuffle else c.VALUE_OFF,
            },
        )

    @staticmethod
    def get_queue(
        player_id: int, range_start: int | None = None, range_end: int | None = None
    ) -> HeosCommand:
        """Get the queue for the current player.

        References:
            4.2.15 Get Queue
        """
        params: dict[str, Any] = {c.ATTR_PLAYER_ID: player_id}
        if isinstance(range_start, int) and isinstance(range_end, int):
            params[c.ATTR_RANGE] = f"{range_start},{range_end}"
        return HeosCommand(c.COMMAND_GET_QUEUE, params)

    @staticmethod
    def play_queue(player_id: int, queue_id: int) -> HeosCommand:
        """Play a queue item.

        References:
            4.2.16 Play Queue Item"""
        return HeosCommand(
            c.COMMAND_PLAY_QUEUE,
            {c.ATTR_PLAYER_ID: player_id, c.ATTR_QUEUE_ID: queue_id},
        )

    @staticmethod
    def remove_from_queue(player_id: int, queue_ids: list[int]) -> HeosCommand:
        """Remove an item from the queue.

        References:
            4.2.17 Remove Item(s) from Queue"""
        return HeosCommand(
            c.COMMAND_REMOVE_FROM_QUEUE,
            {
                c.ATTR_PLAYER_ID: player_id,
                c.ATTR_QUEUE_ID: ",".join(map(str, queue_ids)),
            },
        )

    @staticmethod
    def save_queue(player_id: int, name: str) -> HeosCommand:
        """Save the queue as a playlist.

        References:
            4.2.18 Save Queue as Playlist"""
        if len(name) > 128:
            raise ValueError("'name' must be less than or equal to 128 characters")
        return HeosCommand(
            c.COMMAND_SAVE_QUEUE,
            {c.ATTR_PLAYER_ID: player_id, c.ATTR_NAME: name},
        )

    @staticmethod
    def clear_queue(player_id: int) -> HeosCommand:
        """Clear the queue.

        References:
            4.2.19 Clear Queue"""
        return HeosCommand(c.COMMAND_CLEAR_QUEUE, {c.ATTR_PLAYER_ID: player_id})

    @staticmethod
    def move_queue_item(
        player_id: int, source_queue_ids: list[int], destination_queue_id: int
    ) -> HeosCommand:
        """Move one or more items in the queue.

        References:
            4.2.20 Move Queue"""
        return HeosCommand(
            c.COMMAND_MOVE_QUEUE_ITEM,
            {
                c.ATTR_PLAYER_ID: player_id,
                c.ATTR_SOURCE_QUEUE_ID: ",".join(map(str, source_queue_ids)),
                c.ATTR_DESTINATION_QUEUE_ID: destination_queue_id,
            },
        )

    @staticmethod
    def play_next(player_id: int) -> HeosCommand:
        """Play next.

        References:
            4.2.21 Play Next"""
        return HeosCommand(c.COMMAND_PLAY_NEXT, {c.ATTR_PLAYER_ID: player_id})

    @staticmethod
    def play_previous(player_id: int) -> HeosCommand:
        """Play next.

        References:
            4.2.22 Play Previous"""
        return HeosCommand(c.COMMAND_PLAY_PREVIOUS, {c.ATTR_PLAYER_ID: player_id})

    @staticmethod
    def set_quick_select(player_id: int, quick_select_id: int) -> HeosCommand:
        """Play a quick select.

        References:
            4.2.23 Set QuickSelect"""
        if quick_select_id < 1 or quick_select_id > 6:
            raise ValueError("'quick_select_id' must be in the range 1-6")
        return HeosCommand(
            c.COMMAND_SET_QUICK_SELECT,
            {c.ATTR_PLAYER_ID: player_id, c.ATTR_ID: quick_select_id},
        )

    @staticmethod
    def play_quick_select(player_id: int, quick_select_id: int) -> HeosCommand:
        """Play a quick select.

        References:
            4.2.24 Play QuickSelect"""
        if quick_select_id < 1 or quick_select_id > 6:
            raise ValueError("'quick_select_id' must be in the range 1-6")
        return HeosCommand(
            c.COMMAND_PLAY_QUICK_SELECT,
            {c.ATTR_PLAYER_ID: player_id, c.ATTR_ID: quick_select_id},
        )

    @staticmethod
    def get_quick_selects(player_id: int) -> HeosCommand:
        """Get quick selects.

        References:
            4.2.25 Get QuickSelects"""
        return HeosCommand(c.COMMAND_GET_QUICK_SELECTS, {c.ATTR_PLAYER_ID: player_id})

    @staticmethod
    def check_update(player_id: int) -> HeosCommand:
        """Check for a firmware update.

        References:
            4.2.26 Check for Firmware Update"""
        return HeosCommand(c.COMMAND_CHECK_UPDATE, {c.ATTR_PLAYER_ID: player_id})
