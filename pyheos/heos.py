"""Define the heos manager module."""

import asyncio
import logging
from collections.abc import Sequence
from dataclasses import dataclass, field
from typing import Any, Final, cast

from pyheos.command import COMMAND_SIGN_IN
from pyheos.command.browse import BrowseCommands
from pyheos.command.group import GroupCommands
from pyheos.command.player import PlayerCommands
from pyheos.command.system import SystemCommands
from pyheos.credentials import Credentials
from pyheos.dispatch import (
    CallbackType,
    ControllerEventCallbackType,
    DisconnectType,
    EventCallbackType,
    callback_wrapper,
)
from pyheos.error import CommandError, CommandFailedError
from pyheos.media import (
    BrowseResult,
    MediaItem,
    MediaMusicSource,
)
from pyheos.message import HeosMessage
from pyheos.system import HeosHost, HeosSystem

from . import const
from .connection import AutoReconnectingConnection
from .dispatch import Dispatcher
from .group import HeosGroup
from .player import HeosNowPlayingMedia, HeosPlayer, PlayMode

_LOGGER: Final = logging.getLogger(__name__)


@dataclass(frozen=True)
class HeosOptions:
    """
    The HeosOptions encapsulates options for connecting to a Heos System.

    Args:
        host: A host name or IP address of a HEOS-capable device.
        timeout: The timeout in seconds for opening a connectoin and issuing commands to the device.
        events: Set to True to enable event updates, False to disable. The default is True.
        heart_beat: Set to True to enable heart beat messages, False to disable. Used in conjunction with heart_beat_delay. The default is True.
        heart_beat_interval: The interval in seconds between heart beat messages. Used in conjunction with heart_beat.
        all_progress_events: Set to True to receive media progress events, False to only receive media changed events. The default is True.
        dispatcher: The dispatcher instance to use for event callbacks. If not provided, an internally created instance will be used.
        auto_reconnect: Set to True to automatically reconnect if the connection is lost. The default is False. Used in conjunction with auto_reconnect_delay.
        auto_reconnect_delay: The delay in seconds before attempting to reconnect. The default is 10 seconds. Used in conjunction with auto_reconnect.
        credentials: credentials to use to automatically sign-in to the HEOS account upon successful connection. If not provided, the account will not be signed in.
    """

    host: str
    timeout: float = field(default=const.DEFAULT_TIMEOUT, kw_only=True)
    events: bool = field(default=True, kw_only=True)
    all_progress_events: bool = field(default=True, kw_only=True)
    dispatcher: Dispatcher | None = field(default=None, kw_only=True)
    auto_reconnect: bool = field(default=False, kw_only=True)
    auto_reconnect_delay: float = field(
        default=const.DEFAULT_RECONNECT_DELAY, kw_only=True
    )
    auto_reconnect_max_attempts: int = field(
        default=const.DEFAULT_RECONNECT_ATTEMPTS, kw_only=True
    )
    heart_beat: bool = field(default=True, kw_only=True)
    heart_beat_interval: float = field(default=const.DEFAULT_HEART_BEAT, kw_only=True)
    credentials: Credentials | None = field(default=None, kw_only=True)


class ConnectionMixin:
    "A mixin to provide access to the connection."

    def __init__(self, options: HeosOptions) -> None:
        """Init a new instance of the ConnectionMixin."""
        self._options = options
        self._connection = AutoReconnectingConnection(
            options.host,
            timeout=options.timeout,
            reconnect=options.auto_reconnect,
            reconnect_delay=options.auto_reconnect_delay,
            reconnect_max_attempts=options.auto_reconnect_max_attempts,
            heart_beat=options.heart_beat,
            heart_beat_interval=options.heart_beat_interval,
        )

    @property
    def connection_state(self) -> str:
        """Get the state of the connection."""
        return self._connection.state


class SystemMixin(ConnectionMixin):
    """A mixin to provide access to the system commands."""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        """Init a new instance of the BrowseMixin."""
        super(SystemMixin, self).__init__(*args, **kwargs)

        self._current_credentials = self._options.credentials
        self._signed_in_username: str | None = None

    @property
    def is_signed_in(self) -> bool:
        """Return True if the HEOS accuont is signed in."""
        return bool(self._signed_in_username)

    @property
    def signed_in_username(self) -> str | None:
        """Return the signed-in username."""
        return self._signed_in_username

    @property
    def current_credentials(self) -> Credentials | None:
        """Return the current credential, if any set."""
        return self._current_credentials

    async def register_for_change_events(self, enable: bool) -> None:
        """Register for change events.

        References:
            4.1.1 Register for Change Events"""
        await self._connection.command(
            SystemCommands.register_for_change_events(enable)
        )

    async def check_account(self) -> str | None:
        """Return the logged in username.

        References:
            4.1.2 HEOS Account Check"""
        result = await self._connection.command(SystemCommands.check_account())
        if const.ATTR_SIGNED_IN in result.message:
            self._signed_in_username = result.get_message_value(const.ATTR_USER_NAME)
        else:
            self._signed_in_username = None
        return self._signed_in_username

    async def sign_in(
        self, username: str, password: str, *, update_credential: bool = True
    ) -> str:
        """Sign in to the HEOS account using the provided credential and return the user name.

        Args:
            username: The username of the HEOS account.
            password: The password of the HEOS account.
            update_credential: Set to True to update the stored credential if login is successful, False to keep the current credential. The default is True. If the credential is updated, it will be used to signed in automatically upon reconnection.

        Returns:
            The username of the signed in account.

        References:
            4.1.3 HEOS Account Sign In"""
        result = await self._connection.command(
            SystemCommands.sign_in(username, password)
        )
        self._signed_in_username = result.get_message_value(const.ATTR_USER_NAME)
        if update_credential:
            self._current_credentials = Credentials(username, password)
        return self._signed_in_username

    async def sign_out(self, *, update_credential: bool = True) -> None:
        """Sign out of the HEOS account.

        Args:
            update_credential: Set to True to clear the stored credential, False to keep it. The default is True. If the credential is cleared, the account will not be signed in automatically upon reconnection.

        References:
            4.1.4 HEOS Account Sign Out"""
        await self._connection.command(SystemCommands.sign_out())
        self._signed_in_username = None
        if update_credential:
            self._current_credentials = None

    async def heart_beat(self) -> None:
        """Send a heart beat message to the HEOS device.

        References:
            4.1.5 HEOS System Heart Beat"""
        await self._connection.command(SystemCommands.heart_beat())

    async def reboot(self) -> None:
        """Reboot the HEOS device.

        References:
            4.1.6 HEOS Speaker Reboot"""
        await self._connection.command(SystemCommands.reboot())

    async def get_system_info(self) -> HeosSystem:
        """Get information about the HEOS system.

        References:
            4.2.1 Get Players"""
        response = await self._connection.command(PlayerCommands.get_players())
        payload = cast(Sequence[dict], response.payload)
        hosts = list([HeosHost.from_data(item) for item in payload])
        host = next(host for host in hosts if host.ip_address == self._options.host)
        return HeosSystem(self._signed_in_username, host, hosts)


class BrowseMixin(ConnectionMixin):
    """A mixin to provide access to the browse commands."""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        """Init a new instance of the BrowseMixin."""
        super(BrowseMixin, self).__init__(*args, **kwargs)

        self._music_sources: dict[int, MediaMusicSource] = {}
        self._music_sources_loaded = False

    @property
    def music_sources(self) -> dict[int, MediaMusicSource]:
        """Get available music sources."""
        return self._music_sources

    async def get_music_sources(
        self, refresh: bool = False
    ) -> dict[int, MediaMusicSource]:
        """
        Get available music sources.

        References:
            4.4.1 Get Music Sources
        """
        if not self._music_sources_loaded or refresh:
            message = await self._connection.command(
                BrowseCommands.get_music_sources(refresh)
            )
            self._music_sources.clear()
            for data in cast(Sequence[dict], message.payload):
                source = MediaMusicSource.from_data(data, cast("Heos", self))
                self._music_sources[source.source_id] = source
            self._music_sources_loaded = True
        return self._music_sources

    async def browse(
        self,
        source_id: int,
        container_id: str | None = None,
        range_start: int | None = None,
        range_end: int | None = None,
    ) -> BrowseResult:
        """Browse the contents of the specified source or container.

        References:
            4.4.3 Browse Source
            4.4.4 Browse Source Containers
            4.4.13 Get HEOS Playlists
            4.4.16 Get HEOS History

        Args:
            source_id: The identifier of the source to browse.
            container_id: The identifier of the container to browse. If not provided, the root of the source will be expanded.
            range_start: The index of the first item to return. Both range_start and range_end must be provided to return a range of items.
            range_end: The index of the last item to return. Both range_start and range_end must be provided to return a range of items.
        Returns:
            A BrowseResult instance containing the items in the source or container.
        """
        message = await self._connection.command(
            BrowseCommands.browse(source_id, container_id, range_start, range_end)
        )
        return BrowseResult.from_data(message, cast("Heos", self))

    async def browse_media(
        self,
        media: MediaItem | MediaMusicSource,
        range_start: int | None = None,
        range_end: int | None = None,
    ) -> BrowseResult:
        """Browse the contents of the specified media item.

        References:
            4.4.3 Browse Source
            4.4.4 Browse Source Containers
            4.4.13 Get HEOS Playlists
            4.4.16 Get HEOS History

        Args:
            media: The media item to browse, must be of type MediaItem or MediaMusicSource.
            range_start: The index of the first item to return. Both range_start and range_end must be provided to return a range of items.
            range_end: The index of the last item to return. Both range_start and range_end must be provided to return a range of items.
        Returns:
            A BrowseResult instance containing the items in the media item.
        """
        if isinstance(media, MediaMusicSource):
            if not media.available:
                raise ValueError("Source is not available to browse")
            return await self.browse(media.source_id)
        else:
            if not media.browsable:
                raise ValueError("Only media sources and containers can be browsed")
            return await self.browse(
                media.source_id, media.container_id, range_start, range_end
            )

    async def play_input_source(
        self, player_id: int, input: str, source_player_id: int | None = None
    ) -> None:
        """
        Play the specified input source on the specified player.

        References:
            4.4.9 Play Input Source

        Args:
            player_id: The identifier of the player to play the input source.
            input: The input source to play.
            source_player_id: The identifier of the player that has the input source, if different than the player_id.
        """
        await self._connection.command(
            BrowseCommands.play_input_source(player_id, input, source_player_id)
        )

    async def play_station(
        self, player_id: int, source_id: int, container_id: str | None, media_id: str
    ) -> None:
        """
        Play the specified station on the specified player.

        References:
            4.4.7 Play Station

        Args:
            player_id: The identifier of the player to play the station.
            source_id: The identifier of the source containing the station.
            container_id: The identifier of the container containing the station.
            media_id: The identifier of the station to play.
        """
        await self._connection.command(
            BrowseCommands.play_station(player_id, source_id, container_id, media_id)
        )

    async def play_preset_station(self, player_id: int, index: int) -> None:
        """
        Play the preset station on the specified player (favorite)

        References:
            4.4.8 Play Preset Station

        Args:
            player_id: The identifier of the player to play the preset station.
            index: The index of the preset station to play.
        """
        await self._connection.command(
            BrowseCommands.play_preset_station(player_id, index)
        )

    async def play_url(self, player_id: int, url: str) -> None:
        """
        Play the specified URL on the specified player.

        References:
            4.4.10 Play URL

        Args:
            player_id: The identifier of the player to play the URL.
            url: The URL to play.
        """
        await self._connection.command(BrowseCommands.play_url(player_id, url))

    async def add_to_queue(
        self,
        player_id: int,
        source_id: int,
        container_id: str,
        media_id: str | None = None,
        add_criteria: const.AddCriteriaType = const.AddCriteriaType.PLAY_NOW,
    ) -> None:
        """
        Add the specified media item to the queue of the specified player.

        References:
            4.4.11 Add Container to Queue with Options
            4.4.12 Add Track to Queue with Options

        Args:
            player_id: The identifier of the player to add the media item.
            source_id: The identifier of the source containing the media item.
            container_id: The identifier of the container containing the media item.
            media_id: The identifier of the media item to add. Required for MediaType.Song.
            add_criteria: Determines how tracks are added to the queue. The default is AddCriteriaType.PLAY_NOW.
        """
        await self._connection.command(
            BrowseCommands.add_to_queue(
                player_id=player_id,
                source_id=source_id,
                container_id=container_id,
                media_id=media_id,
                add_criteria=add_criteria,
            )
        )

    async def play_media(
        self,
        player_id: int,
        media: MediaItem,
        add_criteria: const.AddCriteriaType = const.AddCriteriaType.PLAY_NOW,
    ) -> None:
        """
        Play the specified media item on the specified player.

        Args:
            player_id: The identifier of the player to play the media item.
            media: The media item to play.
            add_criteria: Determines how containers or tracks are added to the queue. The default is AddCriteriaType.PLAY_NOW.
        """
        if not media.playable:
            raise ValueError(f"Media '{media}' is not playable")

        if media.media_id in const.VALID_INPUTS:
            await self.play_input_source(player_id, media.media_id, media.source_id)
        elif media.type == const.MediaType.STATION:
            if media.media_id is None:
                raise ValueError(f"'Media '{media}' cannot have a None media_id")
            await self.play_station(
                player_id=player_id,
                source_id=media.source_id,
                container_id=media.container_id,
                media_id=media.media_id,
            )
        else:
            # Handles both songs and containers
            if media.container_id is None:
                raise ValueError(f"Media '{media}' cannot have a None container_id")
            await self.add_to_queue(
                player_id=player_id,
                source_id=media.source_id,
                container_id=media.container_id,
                media_id=media.media_id,
                add_criteria=add_criteria,
            )

    async def get_input_sources(self) -> Sequence[MediaItem]:
        """
        Get available input sources.

        This will browse all aux input sources and return a list of all available input sources.

        Returns:
            A sequence of MediaItem instances representing the available input sources across all aux input sources.
        """
        result = await self.browse(const.MUSIC_SOURCE_AUX_INPUT)
        input_sources: list[MediaItem] = []
        for item in result.items:
            source_browse_result = await item.browse()
            input_sources.extend(source_browse_result.items)

        return input_sources

    async def get_favorites(self) -> dict[int, MediaItem]:
        """
        Get available favorites.

        This will browse the favorites music source and return a dictionary of all available favorites.

        Returns:
            A dictionary with keys representing the index (1-based) of the favorite and the value being the MediaItem instance.
        """
        result = await self.browse(const.MUSIC_SOURCE_FAVORITES)
        return {index + 1: source for index, source in enumerate(result.items)}

    async def get_playlists(self) -> Sequence[MediaItem]:
        """
        Get available playlists.

        This will browse the playlists music source and return a list of all available playlists.

        Returns:
            A sequence of MediaItem instances representing the available playlists.
        """
        result = await self.browse(const.MUSIC_SOURCE_PLAYLISTS)
        return result.items


class PlayerMixin(ConnectionMixin):
    """A mixin to provide access to the player commands."""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        """Init a new instance of the BrowseMixin."""
        super(PlayerMixin, self).__init__(*args, **kwargs)

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

    async def load_players(self) -> dict[str, list | dict]:
        """Refresh the players."""
        new_player_ids = []
        mapped_player_ids = {}
        players = {}
        response = await self._connection.command(PlayerCommands.get_players())
        payload = cast(Sequence[dict], response.payload)
        existing = list(self._players.values())
        for player_data in payload:
            player_id = player_data[const.ATTR_PLAYER_ID]
            name = player_data[const.ATTR_NAME]
            version = player_data[const.ATTR_VERSION]
            # Try finding existing player by id or match name when firmware
            # version is different because IDs change after a firmware upgrade
            player = next(
                (
                    player
                    for player in existing
                    if player.player_id == player_id
                    or (player.name == name and player.version != version)
                ),
                None,
            )
            if player:
                # Existing player matched - update
                if player.player_id != player_id:
                    mapped_player_ids[player_id] = player.player_id
                player.update_from_data(player_data)
                player.available = True
                players[player_id] = player
                existing.remove(player)
            else:
                # New player
                player = HeosPlayer.from_data(player_data, cast("Heos", self))
                new_player_ids.append(player_id)
                players[player_id] = player
        # For any item remaining in existing, mark unavailalbe, add to updated
        for player in existing:
            player.available = False
            players[player.player_id] = player

        # Update all statuses
        await asyncio.gather(
            *[player.refresh() for player in players.values() if player.available]
        )
        self._players = players
        self._players_loaded = True
        return {
            const.DATA_NEW: new_player_ids,
            const.DATA_MAPPED_IDS: mapped_player_ids,
        }

    async def player_get_play_state(self, player_id: int) -> const.PlayState:
        """Get the state of the player.

        References:
            4.2.3 Get Play State"""
        response = await self._connection.command(
            PlayerCommands.get_play_state(player_id)
        )
        return const.PlayState(response.get_message_value(const.ATTR_STATE))

    async def player_set_play_state(
        self, player_id: int, state: const.PlayState
    ) -> None:
        """Set the state of the player.

        References:
            4.2.4 Set Play State"""
        await self._connection.command(PlayerCommands.set_play_state(player_id, state))

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
            PlayerCommands.get_now_playing_media(player_id)
        )
        instance = update or HeosNowPlayingMedia()
        instance.update_from_message(result)
        return instance

    async def player_get_volume(self, player_id: int) -> int:
        """Get the volume level of the player.

        References:
            4.2.6 Get Volume"""
        result = await self._connection.command(PlayerCommands.get_volume(player_id))
        return result.get_message_value_int(const.ATTR_LEVEL)

    async def player_set_volume(self, player_id: int, level: int) -> None:
        """Set the volume of the player.

        References:
            4.2.7 Set Volume"""
        await self._connection.command(PlayerCommands.set_volume(player_id, level))

    async def player_volume_up(
        self, player_id: int, step: int = const.DEFAULT_STEP
    ) -> None:
        """Increase the volume level.

        References:
            4.2.8 Volume Up"""
        await self._connection.command(PlayerCommands.volume_up(player_id, step))

    async def player_volume_down(
        self, player_id: int, step: int = const.DEFAULT_STEP
    ) -> None:
        """Increase the volume level.

        References:
            4.2.9 Volume Down"""
        await self._connection.command(PlayerCommands.volume_down(player_id, step))

    async def player_get_mute(self, player_id: int) -> bool:
        """Get the mute state of the player.

        References:
            4.2.10 Get Mute"""
        result = await self._connection.command(PlayerCommands.get_mute(player_id))
        return result.get_message_value(const.ATTR_STATE) == const.VALUE_ON

    async def player_set_mute(self, player_id: int, state: bool) -> None:
        """Set the mute state of the player.

        References:
            4.2.11 Set Mute"""
        await self._connection.command(PlayerCommands.set_mute(player_id, state))

    async def player_toggle_mute(self, player_id: int) -> None:
        """Toggle the mute state.

        References:
            4.2.12 Toggle Mute"""
        await self._connection.command(PlayerCommands.toggle_mute(player_id))

    async def player_get_play_mode(self, player_id: int) -> PlayMode:
        """Get the play mode of the player.

        References:
            4.2.13 Get Play Mode"""
        result = await self._connection.command(PlayerCommands.get_play_mode(player_id))
        return PlayMode.from_data(result)

    async def player_set_play_mode(
        self, player_id: int, repeat: const.RepeatType, shuffle: bool
    ) -> None:
        """Set the play mode of the player.

        References:
            4.2.14 Set Play Mode"""
        await self._connection.command(
            PlayerCommands.set_play_mode(player_id, repeat, shuffle)
        )

    async def player_clear_queue(self, player_id: int) -> None:
        """Clear the queue.

        References:
            4.2.19 Clear Queue"""
        await self._connection.command(PlayerCommands.clear_queue(player_id))

    async def player_play_next(self, player_id: int) -> None:
        """Play next.

        References:
            4.2.21 Play Next"""
        await self._connection.command(PlayerCommands.play_next(player_id))

    async def player_play_previous(self, player_id: int) -> None:
        """Play next.

        References:
            4.2.22 Play Previous"""
        await self._connection.command(PlayerCommands.play_previous(player_id))

    async def player_set_quick_select(
        self, player_id: int, quick_select_id: int
    ) -> None:
        """Play a quick select.

        References:
            4.2.23 Set QuickSelect"""
        await self._connection.command(
            PlayerCommands.set_quick_select(player_id, quick_select_id)
        )

    async def player_play_quick_select(
        self, player_id: int, quick_select_id: int
    ) -> None:
        """Play a quick select.

        References:
            4.2.24 Play QuickSelect"""
        await self._connection.command(
            PlayerCommands.play_quick_select(player_id, quick_select_id)
        )

    async def get_player_quick_selects(self, player_id: int) -> dict[int, str]:
        """Get quick selects.

        References:
            4.2.25 Get QuickSelects"""
        result = await self._connection.command(
            PlayerCommands.get_quick_selects(player_id)
        )
        return {
            int(data[const.ATTR_ID]): data[const.ATTR_NAME]
            for data in cast(list[dict], result.payload)
        }


class GroupMixin(PlayerMixin):
    """A mixin to provide access to the group commands."""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        """Init a new instance of the BrowseMixin."""
        super(GroupMixin, self).__init__(*args, **kwargs)
        self._groups: dict[int, HeosGroup] = {}
        self._groups_loaded = False

    @property
    def groups(self) -> dict[int, HeosGroup]:
        """Get the loaded groups."""
        return self._groups

    async def get_groups(self, *, refresh: bool = False) -> dict[int, HeosGroup]:
        """Get available groups."""
        if not self._groups_loaded or refresh:
            groups = {}
            result = await self._connection.command(GroupCommands.get_groups())
            payload = cast(Sequence[dict], result.payload)
            for data in payload:
                group = HeosGroup.from_data(data, cast("Heos", self))
                groups[group.group_id] = group
            self._groups = groups
            # Update all statuses
            await asyncio.gather(*[group.refresh() for group in self._groups.values()])
            self._groups_loaded = True
        return self._groups

    async def set_group(self, player_ids: Sequence[int]) -> None:
        """Create, modify, or ungroup players.

        Args:
            player_ids: The list of player identifiers to group or ungroup. The first player is the group leader.

        References:
            4.3.3 Set Group"""
        await self._connection.command(GroupCommands.set_group(player_ids))

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
            GroupCommands.get_group_volume(group_id)
        )
        return result.get_message_value_int(const.ATTR_LEVEL)

    async def set_group_volume(self, group_id: int, level: int) -> None:
        """Set the volume of the group.

        References:
            4.3.5 Set Group Volume"""
        await self._connection.command(GroupCommands.set_group_volume(group_id, level))

    async def group_volume_up(
        self, group_id: int, step: int = const.DEFAULT_STEP
    ) -> None:
        """Increase the volume level.

        References:
            4.3.6 Group Volume Up"""
        await self._connection.command(GroupCommands.group_volume_up(group_id, step))

    async def group_volume_down(
        self, group_id: int, step: int = const.DEFAULT_STEP
    ) -> None:
        """Increase the volume level.

        References:
            4.2.7 Group Volume Down"""
        await self._connection.command(GroupCommands.group_volume_down(group_id, step))

    async def get_group_mute(self, group_id: int) -> bool:
        """Get the mute status of the group.

        References:
            4.3.8 Get Group Mute"""
        result = await self._connection.command(GroupCommands.get_group_mute(group_id))
        return result.get_message_value(const.ATTR_STATE) == const.VALUE_ON

    async def group_set_mute(self, group_id: int, state: bool) -> None:
        """Set the mute state of the group.

        References:
            4.3.9 Set Group Mute"""
        await self._connection.command(GroupCommands.group_set_mute(group_id, state))

    async def group_toggle_mute(self, group_id: int) -> None:
        """Toggle the mute state.

        References:
            4.3.10 Toggle Group Mute"""
        await self._connection.command(GroupCommands.group_toggle_mute(group_id))


class Heos(SystemMixin, BrowseMixin, GroupMixin, PlayerMixin):
    """The Heos class provides access to the CLI API."""

    @classmethod
    async def create_and_connect(cls, host: str, **kwargs: Any) -> "Heos":
        """
        Create a new instance of the Heos CLI API and connect.

        Args:
            host: A host name or IP address of a HEOS-capable device.
            timeout: The timeout in seconds for opening a connectoin and issuing commands to the device.
            events: Set to True to enable event updates, False to disable. The default is True.
            all_progress_events: Set to True to receive media progress events, False to only receive media changed events. The default is True.
            dispatcher: The dispatcher instance to use for event callbacks. If not provided, an internally created instance will be used.
            auto_reconnect: Set to True to automatically reconnect if the connection is lost. The default is False. Used in conjunction with auto_reconnect_delay.
            auto_reconnect_delay: The delay in seconds before attempting to reconnect. The default is 10 seconds. Used in conjunction with auto_reconnect.
            auto_reconnect_max_attempts: The maximum number of reconnection attempts before giving up. Set to 0 for unlimited attempts. The default is 0 (unlimited).
            heart_beat: Set to True to enable heart beat messages, False to disable. Used in conjunction with heart_beat_delay. The default is True.
            heart_beat_interval: The interval in seconds between heart beat messages. Used in conjunction with heart_beat.
            credentials: credentials to use to automatically sign-in to the HEOS account upon successful connection. If not provided, the account will not be signed in.

        """
        heos = Heos(HeosOptions(host, **kwargs))
        await heos.connect()
        return heos

    @classmethod
    async def validate_connection(cls, host: str) -> HeosSystem:
        """
        Validate the connection to the HEOS device and return information about the HEOS system.

        Args:
            host: A host name or IP address of a HEOS-capable device.
        """
        heos = Heos(HeosOptions(host, events=False, heart_beat=False))
        try:
            await heos.connect()
            return await heos.get_system_info()
        finally:
            await heos.disconnect()

    def __init__(self, options: HeosOptions) -> None:
        """Init a new instance of the Heos CLI API."""
        super(Heos, self).__init__(options)
        self._connection.add_on_connected(self._on_connected)
        self._connection.add_on_disconnected(self._on_disconnected)
        self._connection.add_on_event(self._on_event)
        self._connection.add_on_command_error(self._on_command_error)
        self._dispatcher = options.dispatcher or Dispatcher()

    async def connect(self) -> None:
        """Connect to the CLI."""
        await self._connection.connect()

    async def disconnect(self) -> None:
        """Disconnect from the CLI."""
        await self._connection.disconnect()

    def add_on_controller_event(
        self, callback: ControllerEventCallbackType
    ) -> DisconnectType:
        """Connect a callback to receive controller events.

        Args:
            callback: The callback to receive the controller events.
        Returns:
            A function that disconnects the callback."""
        return self._dispatcher.connect(const.SIGNAL_CONTROLLER_EVENT, callback)

    def add_on_heos_event(self, callback: EventCallbackType) -> DisconnectType:
        """Connect a callback to receive HEOS events.

        Args:
            callback: The callback to receive the HEOS events. The callback should accept a single string argument which will contain the event name.
        Returns:
            A function that disconnects the callback."""
        return self._dispatcher.connect(const.SIGNAL_HEOS_EVENT, callback)

    def add_on_connected(self, callback: CallbackType) -> DisconnectType:
        """Connect a callback to be invoked when connected.

        Args:
            callback: The callback to be invoked.
        Returns:
            A function that disconnects the callback."""
        return self.add_on_heos_event(
            callback_wrapper(callback, {0: const.EVENT_CONNECTED}),
        )

    def add_on_disconnected(self, callback: CallbackType) -> DisconnectType:
        """Connect a callback to be invoked when disconnected.

        Args:
            callback: The callback to be invoked.
        Returns:
            A function that disconnects the callback."""
        return self.add_on_heos_event(
            callback_wrapper(callback, {0: const.EVENT_DISCONNECTED}),
        )

    def add_on_user_credentials_invalid(self, callback: CallbackType) -> DisconnectType:
        """Connect a callback to be invoked when the user credentials are invalid.

        Args:
            callback: The callback to be invoked.
        Returns:
            A function that disconnects the callback."""
        return self.add_on_heos_event(
            callback_wrapper(callback, {0: const.EVENT_USER_CREDENTIALS_INVALID}),
        )

    async def _on_connected(self) -> None:
        """Handle when connected, which may occur more than once."""
        assert self._connection.state == const.STATE_CONNECTED

        await self._dispatcher.wait_send(
            const.SIGNAL_HEOS_EVENT, const.EVENT_CONNECTED, return_exceptions=True
        )

        if self._current_credentials:
            # Sign-in to the account if provided
            try:
                await self.sign_in(
                    self._current_credentials.username,
                    self._current_credentials.password,
                )
            except CommandError as err:
                self._signed_in_username = None
                _LOGGER.debug(
                    "Failed to sign-in to HEOS Account after connection: %s", err
                )
                await self._dispatcher.wait_send(
                    const.SIGNAL_HEOS_EVENT,
                    const.EVENT_USER_CREDENTIALS_INVALID,
                    return_exceptions=True,
                )
        else:
            # Determine the logged in user
            await self.check_account()

        await self.register_for_change_events(self._options.events)

        # Refresh players and mark available
        if self._players_loaded:
            await self.load_players()

    async def _on_disconnected(self, from_error: bool) -> None:
        """Handle when disconnected, which may occur more than once."""
        assert self._connection.state == const.STATE_DISCONNECTED
        # Mark loaded players unavailable
        for player in self.players.values():
            player.available = False
        await self._dispatcher.wait_send(
            const.SIGNAL_HEOS_EVENT, const.EVENT_DISCONNECTED, return_exceptions=True
        )

    async def _on_command_error(self, error: CommandFailedError) -> None:
        """Handle when a command error occurs."""
        if error.is_credential_error and error.command != COMMAND_SIGN_IN:
            self._signed_in_username = None
            _LOGGER.debug(
                "HEOS Account credentials are no longer valid: %s",
                error.error_text,
                exc_info=error,
            )
            await self._dispatcher.wait_send(
                const.SIGNAL_HEOS_EVENT,
                const.EVENT_USER_CREDENTIALS_INVALID,
                return_exceptions=True,
            )

    async def _on_event(self, event: HeosMessage) -> None:
        """Handle a heos event."""
        if event.command in const.HEOS_EVENTS:
            await self._on_event_heos(event)
        elif event.command in const.PLAYER_EVENTS:
            await self._on_event_player(event)
        elif event.command in const.GROUP_EVENTS:
            await self._on_event_group(event)
        else:
            _LOGGER.debug("Unrecognized event: %s", event)

    async def _on_event_heos(self, event: HeosMessage) -> None:
        """Process a HEOS system event."""
        result: dict[str, list | dict] | None = None
        if event.command == const.EVENT_PLAYERS_CHANGED and self._players_loaded:
            result = await self.load_players()
        if event.command == const.EVENT_SOURCES_CHANGED and self._music_sources_loaded:
            await self.get_music_sources(refresh=True)
        elif event.command == const.EVENT_USER_CHANGED:
            if const.ATTR_SIGNED_IN in event.message:
                self._signed_in_username = event.get_message_value(const.ATTR_USER_NAME)
            else:
                self._signed_in_username = None
        elif event.command == const.EVENT_GROUPS_CHANGED and self._groups_loaded:
            await self.get_groups(refresh=True)

        await self._dispatcher.wait_send(
            const.SIGNAL_CONTROLLER_EVENT, event.command, result, return_exceptions=True
        )
        _LOGGER.debug("Event received: %s", event)

    async def _on_event_player(self, event: HeosMessage) -> None:
        """Process an event about a player."""
        player_id = event.get_message_value_int(const.ATTR_PLAYER_ID)
        player = self.players.get(player_id)
        if player and (await player.on_event(event, self._options.all_progress_events)):
            await self.dispatcher.wait_send(
                const.SIGNAL_PLAYER_EVENT,
                player_id,
                event.command,
                return_exceptions=True,
            )
            _LOGGER.debug("Event received for player %s: %s", player, event)

    async def _on_event_group(self, event: HeosMessage) -> None:
        """Process an event about a group."""
        group_id = event.get_message_value_int(const.ATTR_GROUP_ID)
        group = self.groups.get(group_id)
        if group and await group.on_event(event):
            await self.dispatcher.wait_send(
                const.SIGNAL_GROUP_EVENT,
                group_id,
                event.command,
                return_exceptions=True,
            )
            _LOGGER.debug("Event received for group %s: %s", group_id, event)

    @property
    def dispatcher(self) -> Dispatcher:
        """Get the dispatcher instance."""
        return self._dispatcher
