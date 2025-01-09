"""
Define the browse command module.

This module creates HEOS browse commands.

Commands not currently implemented:
    4.4.15 Delete HEOS Playlist
    4.4.17 Retrieve Album Metadata
    4.4.19 Set service option
    4.4.20 Universal Search (Multi-Search)

Not implemented:
    4.4.13 Get HEOS Playlists: Refer to Browse Sources and Browse Source Containers

"""

from typing import Any

from pyheos import command, const
from pyheos.message import HeosCommand


class BrowseCommands:
    """Define functions for creating browse commands."""

    @staticmethod
    def browse(
        source_id: int,
        container_id: str | None = None,
        range_start: int | None = None,
        range_end: int | None = None,
    ) -> HeosCommand:
        """Create a HEOS command to browse the provided source.

        References:
            4.4.3 Browse Source
            4.4.4 Browse Source Containers
            4.4.13 Get HEOS Playlists
            4.4.16 Get HEOS History
        """
        params: dict[str, Any] = {const.ATTR_SOURCE_ID: source_id}
        if container_id:
            params[const.ATTR_CONTAINER_ID] = container_id
        if isinstance(range_start, int) and isinstance(range_end, int):
            params[const.ATTR_RANGE] = f"{range_start},{range_end}"
        return HeosCommand(command.COMMAND_BROWSE_BROWSE, params)

    @staticmethod
    def get_music_sources(refresh: bool = False) -> HeosCommand:
        """
        Create a HEOS command to get the music sources.

        References:
            4.4.1 Get Music Sources
        """
        params = {}
        if refresh:
            params[const.ATTR_REFRESH] = const.VALUE_ON
        return HeosCommand(command.COMMAND_BROWSE_GET_SOURCES, params)

    @staticmethod
    def get_music_source_info(source_id: int) -> HeosCommand:
        """
        Create a HEOS command to get information about a music source.

        References:
            4.4.2 Get Source Info
        """
        return HeosCommand(
            command.COMMAND_BROWSE_GET_SOURCE_INFO, {const.ATTR_SOURCE_ID: source_id}
        )

    @staticmethod
    def get_search_criteria(source_id: int) -> HeosCommand:
        """
        Create a HEOS command to get the search criteria.

        References:
            4.4.5 Get Search Criteria
        """
        return HeosCommand(
            command.COMMAND_BROWSE_GET_SEARCH_CRITERIA,
            {const.ATTR_SOURCE_ID: source_id},
        )

    @staticmethod
    def search(
        source_id: int,
        search: str,
        criteria_id: int,
        range_start: int | None = None,
        range_end: int | None = None,
    ) -> HeosCommand:
        """
        Create a HEOS command to search for media.

        References:
            4.4.6 Search
        """
        if search == "":
            raise ValueError("'search' parameter must not be empty")
        if len(search) > 128:
            raise ValueError(
                "'search' parameter must be less than or equal to 128 characters"
            )
        params = {
            const.ATTR_SOURCE_ID: source_id,
            const.ATTR_SEARCH: search,
            const.ATTR_SEARCH_CRITERIA_ID: criteria_id,
        }
        if isinstance(range_start, int) and isinstance(range_end, int):
            params[const.ATTR_RANGE] = f"{range_start},{range_end}"
        return HeosCommand(command.COMMAND_BROWSE_SEARCH, params)

    @staticmethod
    def play_station(
        player_id: int,
        source_id: int,
        container_id: str | None,
        media_id: str,
    ) -> HeosCommand:
        """
        Create a HEOS command to play a station.

        References:
            4.4.7 Play Station

        Note: Parameters 'cid' and 'name' do not appear to be required in testing, however send 'cid' if provided.
        """
        params = {
            const.ATTR_PLAYER_ID: player_id,
            const.ATTR_SOURCE_ID: source_id,
            const.ATTR_MEDIA_ID: media_id,
        }
        if container_id is not None:
            params[const.ATTR_CONTAINER_ID] = container_id
        return HeosCommand(command.COMMAND_BROWSE_PLAY_STREAM, params)

    @staticmethod
    def play_preset_station(player_id: int, preset: int) -> HeosCommand:
        """
        Create a HEOS command to play a preset station.

        References:
            4.4.8 Play Preset Station
        """
        if preset < 1:
            raise ValueError(f"Invalid preset: {preset}")
        return HeosCommand(
            command.COMMAND_BROWSE_PLAY_PRESET,
            {const.ATTR_PLAYER_ID: player_id, const.ATTR_PRESET: preset},
        )

    @staticmethod
    def play_input_source(
        player_id: int, input_name: str, source_player_id: int | None = None
    ) -> HeosCommand:
        """
        Create a HEOS command to play the specified input source.

        References:
            4.4.9 Play Input Source
        """
        params = {
            const.ATTR_PLAYER_ID: player_id,
            const.ATTR_INPUT: input_name,
        }
        if source_player_id is not None:
            params[const.ATTR_SOURCE_PLAYER_ID] = source_player_id
        return HeosCommand(command.COMMAND_BROWSE_PLAY_INPUT, params)

    @staticmethod
    def play_url(player_id: int, url: str) -> HeosCommand:
        """
        Create a HEOS command to play the specified URL.

        References:
            4.4.10 Play URL
        """
        return HeosCommand(
            command.COMMAND_BROWSE_PLAY_STREAM,
            {const.ATTR_PLAYER_ID: player_id, const.ATTR_URL: url},
        )

    @staticmethod
    def add_to_queue(
        player_id: int,
        source_id: int,
        container_id: str,
        media_id: str | None = None,
        add_criteria: const.AddCriteriaType = const.AddCriteriaType.PLAY_NOW,
    ) -> HeosCommand:
        """
        Create a HEOS command to add the specified media to the queue.

        References:
            4.4.11 Add Container to Queue with Options
            4.4.12 Add Track to Queue with Options
        """
        params = {
            const.ATTR_PLAYER_ID: player_id,
            const.ATTR_SOURCE_ID: source_id,
            const.ATTR_CONTAINER_ID: container_id,
            const.ATTR_ADD_CRITERIA_ID: add_criteria,
        }
        if media_id is not None:
            params[const.ATTR_MEDIA_ID] = media_id
        return HeosCommand(command.COMMAND_BROWSE_ADD_TO_QUEUE, params)

    @staticmethod
    def rename_playlist(
        source_id: int, container_id: str, new_name: str
    ) -> HeosCommand:
        """
        Create a HEOS command to rename a playlist.

        References:
            4.4.14 Rename HEOS Playlist
        """
        if new_name == "":
            raise ValueError("'new_name' parameter must not be empty")
        if len(new_name) > 128:
            raise ValueError(
                "'new_name' parameter must be less than or equal to 128 characters"
            )
        return HeosCommand(
            command.COMMAND_BROWSE_RENAME_PLAYLIST,
            {
                const.ATTR_SOURCE_ID: source_id,
                const.ATTR_CONTAINER_ID: container_id,
                const.ATTR_NAME: new_name,
            },
        )
