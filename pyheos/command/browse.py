"""
Define the browse command module.

This module creates HEOS browse commands.

Not implemented (commands do not exist/obsolete):
    4.4.13 Get HEOS Playlists: Refer to Browse Sources and Browse Source Containers
    4.4.16 Get HEOS History: Refer to Browse Sources and Browse Source Containers
    4.4.18 Get Service Options for now playing screen: OBSOLETE
"""

from typing import Any

from pyheos import command, const
from pyheos.message import HeosCommand
from pyheos.types import AddCriteriaType


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
        params: dict[str, Any] = {command.ATTR_SOURCE_ID: source_id}
        if container_id:
            params[command.ATTR_CONTAINER_ID] = container_id
        if isinstance(range_start, int) and isinstance(range_end, int):
            params[command.ATTR_RANGE] = f"{range_start},{range_end}"
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
            params[command.ATTR_REFRESH] = command.VALUE_ON
        return HeosCommand(command.COMMAND_BROWSE_GET_SOURCES, params)

    @staticmethod
    def get_music_source_info(source_id: int) -> HeosCommand:
        """
        Create a HEOS command to get information about a music source.

        References:
            4.4.2 Get Source Info
        """
        return HeosCommand(
            command.COMMAND_BROWSE_GET_SOURCE_INFO, {command.ATTR_SOURCE_ID: source_id}
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
            {command.ATTR_SOURCE_ID: source_id},
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
            command.ATTR_SOURCE_ID: source_id,
            command.ATTR_SEARCH: search,
            command.ATTR_SEARCH_CRITERIA_ID: criteria_id,
        }
        if isinstance(range_start, int) and isinstance(range_end, int):
            params[command.ATTR_RANGE] = f"{range_start},{range_end}"
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
            command.ATTR_PLAYER_ID: player_id,
            command.ATTR_SOURCE_ID: source_id,
            command.ATTR_MEDIA_ID: media_id,
        }
        if container_id is not None:
            params[command.ATTR_CONTAINER_ID] = container_id
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
            {command.ATTR_PLAYER_ID: player_id, command.ATTR_PRESET: preset},
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
            command.ATTR_PLAYER_ID: player_id,
            command.ATTR_INPUT: input_name,
        }
        if source_player_id is not None:
            params[command.ATTR_SOURCE_PLAYER_ID] = source_player_id
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
            {command.ATTR_PLAYER_ID: player_id, command.ATTR_URL: url},
        )

    @staticmethod
    def add_to_queue(
        player_id: int,
        source_id: int,
        container_id: str,
        media_id: str | None = None,
        add_criteria: AddCriteriaType = AddCriteriaType.PLAY_NOW,
    ) -> HeosCommand:
        """
        Create a HEOS command to add the specified media to the queue.

        References:
            4.4.11 Add Container to Queue with Options
            4.4.12 Add Track to Queue with Options
        """
        params = {
            command.ATTR_PLAYER_ID: player_id,
            command.ATTR_SOURCE_ID: source_id,
            command.ATTR_CONTAINER_ID: container_id,
            command.ATTR_ADD_CRITERIA_ID: add_criteria,
        }
        if media_id is not None:
            params[command.ATTR_MEDIA_ID] = media_id
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
                command.ATTR_SOURCE_ID: source_id,
                command.ATTR_CONTAINER_ID: container_id,
                command.ATTR_NAME: new_name,
            },
        )

    @staticmethod
    def delete_playlist(source_id: int, container_id: str) -> HeosCommand:
        """
        Create a HEOS command to delete a playlist.

        References:
            4.4.15 Delete HEOS Playlist"""
        return HeosCommand(
            command.COMMAND_BROWSE_DELETE__PLAYLIST,
            {
                command.ATTR_SOURCE_ID: source_id,
                command.ATTR_CONTAINER_ID: container_id,
            },
        )

    @staticmethod
    def retrieve_metadata(source_it: int, container_id: str) -> HeosCommand:
        """
        Create a HEOS command to retrieve metadata.

        References:
            4.4.17 Retrieve Metadata
        """
        return HeosCommand(
            command.COMMAND_BROWSE_RETRIEVE_METADATA,
            {
                command.ATTR_SOURCE_ID: source_it,
                command.ATTR_CONTAINER_ID: container_id,
            },
        )

    @staticmethod
    def set_service_option(
        option_id: int,
        source_id: int | None,
        container_id: str | None,
        media_id: str | None,
        player_id: int | None,
        name: str | None,
        criteria_id: int | None,
        range_start: int | None = None,
        range_end: int | None = None,
    ) -> HeosCommand:
        """
        Create a HEOS command to set a service option.

        References:
            4.4.19 Set Service Option
        """
        params: dict[str, Any] = {command.ATTR_OPTION_ID: option_id}
        disallowed_params = {}

        if option_id in (
            const.SERVICE_OPTION_ADD_TRACK_TO_LIBRARY,
            const.SERVICE_OPTION_ADD_STATION_TO_LIBRARY,
            const.SERVICE_OPTION_REMOVE_TRACK_FROM_LIBRARY,
            const.SERVICE_OPTION_REMOVE_STATION_FROM_LIBRARY,
        ):
            if source_id is None or media_id is None:
                raise ValueError(
                    f"source_id and media_id parameters are required for service option_id {option_id}"
                )
            disallowed_params = {
                "container_id": container_id,
                "player_id": player_id,
                "name": name,
                "criteria_id": criteria_id,
                "range_start": range_start,
                "range_end": range_end,
            }
            params[command.ATTR_SOURCE_ID] = source_id
            params[command.ATTR_MEDIA_ID] = media_id
        elif option_id in (
            const.SERVICE_OPTION_ADD_ALBUM_TO_LIBRARY,
            const.SERVICE_OPTION_REMOVE_ALBUM_FROM_LIBRARY,
            const.SERVICE_OPTION_REMOVE_PLAYLIST_FROM_LIBRARY,
        ):
            if source_id is None or container_id is None:
                raise ValueError(
                    f"source_id and container_id parameters are required for service option_id {option_id}"
                )
            disallowed_params = {
                "media_id": media_id,
                "player_id": player_id,
                "name": name,
                "criteria_id": criteria_id,
                "range_start": range_start,
                "range_end": range_end,
            }
            params[command.ATTR_SOURCE_ID] = source_id
            params[command.ATTR_CONTAINER_ID] = container_id
        elif option_id == const.SERVICE_OPTION_ADD_PLAYLIST_TO_LIBRARY:
            if source_id is None or container_id is None or name is None:
                raise ValueError(
                    f"source_id, container_id, and name parameters are required for service option_id {option_id}"
                )
            disallowed_params = {
                "media_id": media_id,
                "player_id": player_id,
                "criteria_id": criteria_id,
                "range_start": range_start,
                "range_end": range_end,
            }
            params[command.ATTR_SOURCE_ID] = source_id
            params[command.ATTR_CONTAINER_ID] = container_id
            params[command.ATTR_NAME] = name
        elif option_id in (
            const.SERVICE_OPTION_THUMBS_UP,
            const.SERVICE_OPTION_THUMBS_DOWN,
        ):
            if source_id is None or player_id is None:
                raise ValueError(
                    f"source_id and player_id parameters are required for service option_id {option_id}"
                )
            disallowed_params = {
                "media_id": media_id,
                "container_id": container_id,
                "name": name,
                "criteria_id": criteria_id,
                "range_start": range_start,
                "range_end": range_end,
            }
            params[command.ATTR_SOURCE_ID] = source_id
            params[command.ATTR_PLAYER_ID] = player_id
        elif option_id == const.SERVICE_OPTION_CREATE_NEW_STATION_BY_SEARCH_CRITERIA:
            if source_id is None or name is None or criteria_id is None:
                raise ValueError(
                    f"source_id, name, and criteria_id parameters are required for service option_id {option_id}"
                )
            disallowed_params = {
                "media_id": media_id,
                "container_id": container_id,
                "player_id": player_id,
            }
            params[command.ATTR_SOURCE_ID] = source_id
            params[command.ATTR_SEARCH_CRITERIA_ID] = criteria_id
            params[command.ATTR_NAME] = name
            if isinstance(range_start, int) and isinstance(range_end, int):
                params[command.ATTR_RANGE] = f"{range_start},{range_end}"
        elif option_id == const.SERVICE_OPTION_ADD_TO_FAVORITES:
            if not bool(player_id) ^ (
                source_id is not None and media_id is not None and name is not None
            ):
                raise ValueError(
                    f"Either parameters player_id OR source_id, media_id, and name are required for service option_id {option_id}"
                )
            if player_id is not None:
                if source_id is not None or media_id is not None or name is not None:
                    raise ValueError(
                        f"source_id, media_id, and name parameters are not allowed when using player_id for service option_id {option_id}"
                    )
                params[command.ATTR_PLAYER_ID] = player_id
            else:
                params[command.ATTR_SOURCE_ID] = source_id
                params[command.ATTR_MEDIA_ID] = media_id
                params[command.ATTR_NAME] = name
            disallowed_params = {
                "container_id": container_id,
                "criteria_id": criteria_id,
                "range_start": range_start,
                "range_end": range_end,
            }
        elif option_id == const.SERVICE_OPTION_REMOVE_FROM_FAVORITES:
            if media_id is None:
                raise ValueError(
                    f"media_id parameter is required for service option_id {option_id}"
                )
            params[command.ATTR_MEDIA_ID] = media_id
            disallowed_params = {
                "source_id": source_id,
                "player_id": player_id,
                "container_id": container_id,
                "name": name,
                "criteria_id": criteria_id,
                "range_start": range_start,
                "range_end": range_end,
            }
        else:
            raise ValueError(f"Unknown option_id: {option_id}")

        # Raise if any disallowed parameters are provided
        if any(param is not None for param in disallowed_params.values()):
            raise ValueError(
                f"{', '.join(disallowed_params.keys())} parameters are not allowed for service option_id {option_id}"
            )

        # return the command
        return HeosCommand(command.COMMAND_BROWSE_SET_SERVICE_OPTION, params)

    @staticmethod
    def multi_search(
        search: str, source_ids: list[int] | None, criteria_ids: list[int] | None
    ) -> HeosCommand:
        """
        Create a HEOS command to perform a multi-search.

        References:
            4.4.20 Multi Search
        """
        if len(search) > 128:
            raise ValueError(
                "'search' parameter must be less than or equal to 128 characters"
            )
        params = {command.ATTR_SEARCH: search}
        if source_ids is not None:
            params[command.ATTR_SOURCE_ID] = ",".join(map(str, source_ids))
        if criteria_ids is not None:
            params[command.ATTR_SEARCH_CRITERIA_ID] = ",".join(map(str, criteria_ids))
        return HeosCommand(command.COMMAND_BROWSE_MULTI_SEARCH, params)
