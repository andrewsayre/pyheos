"""
Define the player command module.

This module creates HEOS player commands.
"""

import asyncio
from collections.abc import Sequence
from typing import TYPE_CHECKING, Any, cast

from pyheos import command as c
from pyheos import const
from pyheos.command.connection import ConnectionMixin
from pyheos.media import QueueItem
from pyheos.message import HeosCommand
from pyheos.player import (
    HeosNowPlayingMedia,
    HeosPlayer,
    PlayerUpdateResult,
    PlayMode,
    PlayState,
)
from pyheos.types import RepeatType

if TYPE_CHECKING:
    from pyheos.heos import Heos


class PlayerCommands(ConnectionMixin):
    """A mixin to provide access to the player commands."""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        """Init a new instance of the BrowseMixin."""
        super(PlayerCommands, self).__init__(*args, **kwargs)

        self._players: dict[int, HeosPlayer] = {}
        self._players_loaded = False

    @property
    def players(self) -> dict[int, HeosPlayer]:
        """Get the loaded players."""
        return self._players

    async def get_players(self, *, refresh: bool = False) -> dict[int, HeosPlayer]:
        """Get available players.

        References:
            4.2.1 Get Players"""
        # get players and pull initial state
        if not self._players_loaded or refresh:
            await self.load_players()
        return self._players

    async def get_player_info(
        self,
        player_id: int | None = None,
        player: HeosPlayer | None = None,
        *,
        refresh: bool = False,
    ) -> HeosPlayer:
        """Get information about a player.

        Only one of player_id or player should be provided.

        Args:
            palyer_id: The identifier of the group to get information about. Only one of player_id or player should be provided.
            player: The HeosPlayer instance to update with the latest information. Only one of player_id or player should be provided.
            refresh: Set to True to force a refresh of the group information.
        Returns:
            A HeosPlayer instance containing the player information.

        References:
            4.2.2 Get Player Info"""
        if player_id is None and player is None:
            raise ValueError("Either player_id or player must be provided")
        if player_id is not None and player is not None:
            raise ValueError("Only one of player_id or player should be provided")

        # if only palyer_id provided, try getting from loaded
        if player is None:
            assert player_id is not None
            player = self._players.get(player_id)
        else:
            player_id = player.player_id

        if player is None or refresh:
            # Get the latest information
            result = await self._connection.command(
                HeosCommand(c.COMMAND_GET_PLAYER_INFO, {c.ATTR_PLAYER_ID: player_id})
            )

            payload = cast(dict[str, Any], result.payload)
            if player is None:
                player = HeosPlayer._from_data(payload, cast("Heos", self))
            else:
                player._update_from_data(payload)
            await player.refresh(refresh_base_info=False)
        return player

    async def load_players(self) -> PlayerUpdateResult:
        """Refresh the players."""
        result = PlayerUpdateResult()

        players: dict[int, HeosPlayer] = {}
        response = await self._connection.command(HeosCommand(c.COMMAND_GET_PLAYERS))
        payload = cast(Sequence[dict], response.payload)
        existing = list(self._players.values())
        for player_data in payload:
            player_id = int(player_data[c.ATTR_PLAYER_ID])
            name = player_data[c.ATTR_NAME]
            version = player_data[c.ATTR_VERSION]
            serial = player_data.get(c.ATTR_SERIAL)
            # Try matching by serial (if available), then try matching by player_id
            # and fallback to matching name when firmware version is different
            player = next(
                (
                    player
                    for player in existing
                    if (player.serial == serial and serial is not None)
                    or player.player_id == player_id
                    or (player.name == name and player.version != version)
                ),
                None,
            )
            if player:
                # Found existing, update
                if player.player_id != player_id:
                    result.updated_player_ids[player.player_id] = player_id
                player._update_from_data(player_data)
                player.available = True
                players[player_id] = player
                existing.remove(player)
            else:
                # New player
                player = HeosPlayer._from_data(player_data, cast("Heos", self))
                result.added_player_ids.append(player_id)
                players[player_id] = player
        # For any item remaining in existing, mark unavailalbe, add to updated
        for player in existing:
            result.removed_player_ids.append(player.player_id)
            player.available = False
            players[player.player_id] = player

        # Pull data for available players
        await asyncio.gather(
            *[
                player.refresh(refresh_base_info=False)
                for player in players.values()
                if player.available
            ]
        )
        self._players = players
        self._players_loaded = True
        return result

    async def player_get_play_state(self, player_id: int) -> PlayState:
        """Get the state of the player.

        References:
            4.2.3 Get Play State"""
        response = await self._connection.command(
            HeosCommand(c.COMMAND_GET_PLAY_STATE, {c.ATTR_PLAYER_ID: player_id})
        )
        return PlayState(response.get_message_value(c.ATTR_STATE))

    async def player_set_play_state(self, player_id: int, state: PlayState) -> None:
        """Set the state of the player.

        References:
            4.2.4 Set Play State"""
        await self._connection.command(
            HeosCommand(
                c.COMMAND_SET_PLAY_STATE,
                {c.ATTR_PLAYER_ID: player_id, c.ATTR_STATE: state},
            )
        )

    async def get_now_playing_media(
        self, player_id: int, update: HeosNowPlayingMedia | None = None
    ) -> HeosNowPlayingMedia:
        """Get the now playing media information.

        Args:
            player_id: The identifier of the player to get the now playing media.
            update: The current now playing media information to update. If not provided, a new instance will be created.

        Returns:
            A HeosNowPlayingMedia instance containing the now playing media information.

        References:
            4.2.5 Get Now Playing Media"""
        result = await self._connection.command(
            HeosCommand(c.COMMAND_GET_NOW_PLAYING_MEDIA, {c.ATTR_PLAYER_ID: player_id})
        )
        instance = update or HeosNowPlayingMedia()
        instance._update_from_message(result)
        return instance

    async def player_get_volume(self, player_id: int) -> int:
        """Get the volume level of the player.

        References:
            4.2.6 Get Volume"""
        result = await self._connection.command(
            HeosCommand(c.COMMAND_GET_VOLUME, {c.ATTR_PLAYER_ID: player_id})
        )
        return result.get_message_value_int(c.ATTR_LEVEL)

    async def player_set_volume(self, player_id: int, level: int) -> None:
        """Set the volume of the player.

        References:
            4.2.7 Set Volume"""
        if level < 0 or level > 100:
            raise ValueError("'level' must be in the range 0-100")
        await self._connection.command(
            HeosCommand(
                c.COMMAND_SET_VOLUME,
                {c.ATTR_PLAYER_ID: player_id, c.ATTR_LEVEL: level},
            )
        )

    async def player_volume_up(
        self, player_id: int, step: int = const.DEFAULT_STEP
    ) -> None:
        """Increase the volume level.

        References:
            4.2.8 Volume Up"""
        if step < 1 or step > 10:
            raise ValueError("'step' must be in the range 1-10")
        await self._connection.command(
            HeosCommand(
                c.COMMAND_VOLUME_UP,
                {c.ATTR_PLAYER_ID: player_id, c.ATTR_STEP: step},
            )
        )

    async def player_volume_down(
        self, player_id: int, step: int = const.DEFAULT_STEP
    ) -> None:
        """Increase the volume level.

        References:
            4.2.9 Volume Down"""
        if step < 1 or step > 10:
            raise ValueError("'step' must be in the range 1-10")
        await self._connection.command(
            HeosCommand(
                c.COMMAND_VOLUME_DOWN,
                {c.ATTR_PLAYER_ID: player_id, c.ATTR_STEP: step},
            )
        )

    async def player_get_mute(self, player_id: int) -> bool:
        """Get the mute state of the player.

        References:
            4.2.10 Get Mute"""
        result = await self._connection.command(
            HeosCommand(c.COMMAND_GET_MUTE, {c.ATTR_PLAYER_ID: player_id})
        )
        return result.get_message_value(c.ATTR_STATE) == c.VALUE_ON

    async def player_set_mute(self, player_id: int, state: bool) -> None:
        """Set the mute state of the player.

        References:
            4.2.11 Set Mute"""
        await self._connection.command(
            HeosCommand(
                c.COMMAND_SET_MUTE,
                {
                    c.ATTR_PLAYER_ID: player_id,
                    c.ATTR_STATE: c.VALUE_ON if state else c.VALUE_OFF,
                },
            )
        )

    async def player_toggle_mute(self, player_id: int) -> None:
        """Toggle the mute state.

        References:
            4.2.12 Toggle Mute"""
        await self._connection.command(
            HeosCommand(c.COMMAND_TOGGLE_MUTE, {c.ATTR_PLAYER_ID: player_id})
        )

    async def player_get_play_mode(self, player_id: int) -> PlayMode:
        """Get the play mode of the player.

        References:
            4.2.13 Get Play Mode"""
        result = await self._connection.command(
            HeosCommand(c.COMMAND_GET_PLAY_MODE, {c.ATTR_PLAYER_ID: player_id})
        )
        return PlayMode._from_data(result)

    async def player_set_play_mode(
        self, player_id: int, repeat: RepeatType, shuffle: bool
    ) -> None:
        """Set the play mode of the player.

        References:
            4.2.14 Set Play Mode"""
        await self._connection.command(
            HeosCommand(
                c.COMMAND_SET_PLAY_MODE,
                {
                    c.ATTR_PLAYER_ID: player_id,
                    c.ATTR_REPEAT: repeat,
                    c.ATTR_SHUFFLE: c.VALUE_ON if shuffle else c.VALUE_OFF,
                },
            )
        )

    async def player_get_queue(
        self,
        player_id: int,
        range_start: int | None = None,
        range_end: int | None = None,
    ) -> list[QueueItem]:
        """Get the queue for the current player.

        References:
            4.2.15 Get Queue
        """
        params: dict[str, Any] = {c.ATTR_PLAYER_ID: player_id}
        if isinstance(range_start, int) and isinstance(range_end, int):
            params[c.ATTR_RANGE] = f"{range_start},{range_end}"
        result = await self._connection.command(
            HeosCommand(c.COMMAND_GET_QUEUE, params)
        )
        payload = cast(list[dict[str, str]], result.payload)
        return [QueueItem.from_data(data) for data in payload]

    async def player_play_queue(self, player_id: int, queue_id: int) -> None:
        """Play a queue item.

        References:
            4.2.16 Play Queue Item"""
        await self._connection.command(
            HeosCommand(
                c.COMMAND_PLAY_QUEUE,
                {c.ATTR_PLAYER_ID: player_id, c.ATTR_QUEUE_ID: queue_id},
            )
        )

    async def player_remove_from_queue(
        self, player_id: int, queue_ids: list[int]
    ) -> None:
        """Remove an item from the queue.

        References:
            4.2.17 Remove Item(s) from Queue"""
        await self._connection.command(
            HeosCommand(
                c.COMMAND_REMOVE_FROM_QUEUE,
                {
                    c.ATTR_PLAYER_ID: player_id,
                    c.ATTR_QUEUE_ID: ",".join(map(str, queue_ids)),
                },
            )
        )

    async def player_save_queue(self, player_id: int, name: str) -> None:
        """Save the queue as a playlist.

        References:
            4.2.18 Save Queue as Playlist"""
        if len(name) > 128:
            raise ValueError("'name' must be less than or equal to 128 characters")
        await self._connection.command(
            HeosCommand(
                c.COMMAND_SAVE_QUEUE,
                {c.ATTR_PLAYER_ID: player_id, c.ATTR_NAME: name},
            )
        )

    async def player_clear_queue(self, player_id: int) -> None:
        """Clear the queue.

        References:
            4.2.19 Clear Queue"""
        await self._connection.command(
            HeosCommand(c.COMMAND_CLEAR_QUEUE, {c.ATTR_PLAYER_ID: player_id})
        )

    async def player_move_queue_item(
        self, player_id: int, source_queue_ids: list[int], destination_queue_id: int
    ) -> None:
        """Move one or more items in the queue.

        References:
            4.2.20 Move Queue"""
        await self._connection.command(
            HeosCommand(
                c.COMMAND_MOVE_QUEUE_ITEM,
                {
                    c.ATTR_PLAYER_ID: player_id,
                    c.ATTR_SOURCE_QUEUE_ID: ",".join(map(str, source_queue_ids)),
                    c.ATTR_DESTINATION_QUEUE_ID: destination_queue_id,
                },
            )
        )

    async def player_play_next(self, player_id: int) -> None:
        """Play next.

        References:
            4.2.21 Play Next"""
        await self._connection.command(
            HeosCommand(c.COMMAND_PLAY_NEXT, {c.ATTR_PLAYER_ID: player_id})
        )

    async def player_play_previous(self, player_id: int) -> None:
        """Play next.

        References:
            4.2.22 Play Previous"""
        await self._connection.command(
            HeosCommand(c.COMMAND_PLAY_PREVIOUS, {c.ATTR_PLAYER_ID: player_id})
        )

    async def player_set_quick_select(
        self, player_id: int, quick_select_id: int
    ) -> None:
        """Play a quick select.

        References:
            4.2.23 Set QuickSelect"""
        if quick_select_id < 1 or quick_select_id > 6:
            raise ValueError("'quick_select_id' must be in the range 1-6")
        await self._connection.command(
            HeosCommand(
                c.COMMAND_SET_QUICK_SELECT,
                {c.ATTR_PLAYER_ID: player_id, c.ATTR_ID: quick_select_id},
            )
        )

    async def player_play_quick_select(
        self, player_id: int, quick_select_id: int
    ) -> None:
        """Play a quick select.

        References:
            4.2.24 Play QuickSelect"""
        if quick_select_id < 1 or quick_select_id > 6:
            raise ValueError("'quick_select_id' must be in the range 1-6")
        await self._connection.command(
            HeosCommand(
                c.COMMAND_PLAY_QUICK_SELECT,
                {c.ATTR_PLAYER_ID: player_id, c.ATTR_ID: quick_select_id},
            )
        )

    async def player_get_quick_selects(self, player_id: int) -> dict[int, str]:
        """Get quick selects.

        References:
            4.2.25 Get QuickSelects"""
        result = await self._connection.command(
            HeosCommand(c.COMMAND_GET_QUICK_SELECTS, {c.ATTR_PLAYER_ID: player_id})
        )
        return {
            int(data[c.ATTR_ID]): data[c.ATTR_NAME]
            for data in cast(list[dict], result.payload)
        }

    async def player_check_update(self, player_id: int) -> bool:
        """Check for a firmware update.

        Args:
            player_id: The identifier of the player to check for a firmware update.
        Returns:
            True if an update is available, otherwise False.

        References:
            4.2.26 Check for Firmware Update"""
        result = await self._connection.command(
            HeosCommand(c.COMMAND_CHECK_UPDATE, {c.ATTR_PLAYER_ID: player_id})
        )
        payload = cast(dict[str, Any], result.payload)
        return bool(payload[c.ATTR_UPDATE] == c.VALUE_UPDATE_EXIST)
