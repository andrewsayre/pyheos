"""
Define the browse command module.

This module creates HEOS browse commands.

Not implemented (commands do not exist/obsolete):
    4.4.13 Get HEOS Playlists: Refer to Browse Sources and Browse Source Containers
    4.4.16 Get HEOS History: Refer to Browse Sources and Browse Source Containers
    4.4.18 Get Service Options for now playing screen: OBSOLETE
"""

from collections.abc import Sequence
from typing import TYPE_CHECKING, Any, cast

from pyheos import command as c
from pyheos.command.connection import ConnectionMixin
from pyheos.const import (
    MUSIC_SOURCE_AUX_INPUT,
    MUSIC_SOURCE_FAVORITES,
    MUSIC_SOURCE_PLAYLISTS,
    SEARCHED_TRACKS,
    SERVICE_OPTION_ADD_ALBUM_TO_LIBRARY,
    SERVICE_OPTION_ADD_PLAYLIST_TO_LIBRARY,
    SERVICE_OPTION_ADD_STATION_TO_LIBRARY,
    SERVICE_OPTION_ADD_TO_FAVORITES,
    SERVICE_OPTION_ADD_TRACK_TO_LIBRARY,
    SERVICE_OPTION_CREATE_NEW_STATION_BY_SEARCH_CRITERIA,
    SERVICE_OPTION_REMOVE_ALBUM_FROM_LIBRARY,
    SERVICE_OPTION_REMOVE_FROM_FAVORITES,
    SERVICE_OPTION_REMOVE_PLAYLIST_FROM_LIBRARY,
    SERVICE_OPTION_REMOVE_STATION_FROM_LIBRARY,
    SERVICE_OPTION_REMOVE_TRACK_FROM_LIBRARY,
    SERVICE_OPTION_THUMBS_DOWN,
    SERVICE_OPTION_THUMBS_UP,
    VALID_INPUTS,
)
from pyheos.media import (
    BrowseResult,
    MediaItem,
    MediaMusicSource,
    RetreiveMetadataResult,
)
from pyheos.message import HeosCommand
from pyheos.search import MultiSearchResult, SearchCriteria, SearchResult
from pyheos.types import AddCriteriaType, MediaType

if TYPE_CHECKING:
    from pyheos.heos import Heos


class BrowseCommands(ConnectionMixin):
    """A mixin to provide access to the browse commands."""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        """Init a new instance of the BrowseMixin."""
        super(BrowseCommands, self).__init__(*args, **kwargs)

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
            params = {}
            if refresh:
                params[c.ATTR_REFRESH] = c.VALUE_ON
            message = await self._connection.command(
                HeosCommand(c.COMMAND_BROWSE_GET_SOURCES, params)
            )
            self._music_sources.clear()
            for data in cast(Sequence[dict], message.payload):
                source = MediaMusicSource.from_data(data, cast("Heos", self))
                self._music_sources[source.source_id] = source
            self._music_sources_loaded = True
        return self._music_sources

    async def get_music_source_info(
        self,
        source_id: int | None = None,
        music_source: MediaMusicSource | None = None,
        *,
        refresh: bool = False,
    ) -> MediaMusicSource:
        """
        Get information about a specific music source.

        References:
            4.4.2 Get Source Info
        """
        if source_id is None and music_source is None:
            raise ValueError("Either source_id or music_source must be provided")
        if source_id is not None and music_source is not None:
            raise ValueError("Only one of source_id or music_source should be provided")

        # if only source_id provided, try getting from loaded
        if music_source is None:
            assert source_id is not None
            music_source = self._music_sources.get(source_id)
        else:
            source_id = music_source.source_id

        if music_source is None or refresh:
            # Get the latest information
            result = await self._connection.command(
                HeosCommand(
                    c.COMMAND_BROWSE_GET_SOURCE_INFO, {c.ATTR_SOURCE_ID: source_id}
                )
            )
            payload = cast(dict[str, Any], result.payload)
            if music_source is None:
                music_source = MediaMusicSource.from_data(payload, cast("Heos", self))
            else:
                music_source._update_from_data(payload)
        return music_source

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
        params: dict[str, Any] = {c.ATTR_SOURCE_ID: source_id}
        if container_id:
            params[c.ATTR_CONTAINER_ID] = container_id
        if isinstance(range_start, int) and isinstance(range_end, int):
            params[c.ATTR_RANGE] = f"{range_start},{range_end}"
        message = await self._connection.command(
            HeosCommand(c.COMMAND_BROWSE_BROWSE, params)
        )
        return BrowseResult._from_message(message, cast("Heos", self))

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

    async def get_search_criteria(self, source_id: int) -> list[SearchCriteria]:
        """
        Create a HEOS command to get the search criteria.

        References:
            4.4.5 Get Search Criteria
        """
        result = await self._connection.command(
            HeosCommand(
                c.COMMAND_BROWSE_GET_SEARCH_CRITERIA,
                {c.ATTR_SOURCE_ID: source_id},
            )
        )
        payload = cast(list[dict[str, str]], result.payload)
        return [SearchCriteria._from_data(data) for data in payload]

    async def search(
        self,
        source_id: int,
        search: str,
        criteria_id: int,
        range_start: int | None = None,
        range_end: int | None = None,
    ) -> SearchResult:
        """
        Create a HEOS command to search for media.

        References:
            4.4.6 Search"""
        if search == "":
            raise ValueError("'search' parameter must not be empty")
        if len(search) > 128:
            raise ValueError(
                "'search' parameter must be less than or equal to 128 characters"
            )
        params = {
            c.ATTR_SOURCE_ID: source_id,
            c.ATTR_SEARCH: search,
            c.ATTR_SEARCH_CRITERIA_ID: criteria_id,
        }
        if isinstance(range_start, int) and isinstance(range_end, int):
            params[c.ATTR_RANGE] = f"{range_start},{range_end}"
        result = await self._connection.command(
            HeosCommand(c.COMMAND_BROWSE_SEARCH, params)
        )
        return SearchResult._from_message(result, cast("Heos", self))

    async def play_input_source(
        self, player_id: int, input_name: str, source_player_id: int | None = None
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
        params = {
            c.ATTR_PLAYER_ID: player_id,
            c.ATTR_INPUT: input_name,
        }
        if source_player_id is not None:
            params[c.ATTR_SOURCE_PLAYER_ID] = source_player_id
        await self._connection.command(HeosCommand(c.COMMAND_BROWSE_PLAY_INPUT, params))

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
        params = {
            c.ATTR_PLAYER_ID: player_id,
            c.ATTR_SOURCE_ID: source_id,
            c.ATTR_MEDIA_ID: media_id,
        }
        if container_id is not None:
            params[c.ATTR_CONTAINER_ID] = container_id
        await self._connection.command(
            HeosCommand(c.COMMAND_BROWSE_PLAY_STREAM, params)
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
        if index < 1:
            raise ValueError(f"Invalid preset: {index}")
        await self._connection.command(
            HeosCommand(
                c.COMMAND_BROWSE_PLAY_PRESET,
                {c.ATTR_PLAYER_ID: player_id, c.ATTR_PRESET: index},
            )
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
        await self._connection.command(
            HeosCommand(
                c.COMMAND_BROWSE_PLAY_STREAM,
                {c.ATTR_PLAYER_ID: player_id, c.ATTR_URL: url},
            )
        )

    async def add_to_queue(
        self,
        player_id: int,
        source_id: int,
        container_id: str,
        media_id: str | None = None,
        add_criteria: AddCriteriaType = AddCriteriaType.PLAY_NOW,
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
        params = {
            c.ATTR_PLAYER_ID: player_id,
            c.ATTR_SOURCE_ID: source_id,
            c.ATTR_CONTAINER_ID: container_id,
            c.ATTR_ADD_CRITERIA_ID: add_criteria,
        }
        if media_id is not None:
            params[c.ATTR_MEDIA_ID] = media_id
        await self._connection.command(
            HeosCommand(c.COMMAND_BROWSE_ADD_TO_QUEUE, params)
        )

    async def add_search_to_queue(
        self,
        player_id: int,
        source_id: int,
        search: str,
        criteria_container_id: str = SEARCHED_TRACKS,
        add_criteria: AddCriteriaType = AddCriteriaType.PLAY_NOW,
    ) -> None:
        """Add searched tracks to the queue of the specified player.

        References:
            4.4.11 Add Container to Queue with Options

        Args:
            player_id: The identifier of the player to add the search results.
            source_id: The identifier of the source to search.
            search: The search string.
            criteria_container_id: the criteria container id prefix.
            add_criteria: Determines how tracks are added to the queue. The default is AddCriteriaType.PLAY_NOW.
        """
        await self.add_to_queue(
            player_id=player_id,
            source_id=source_id,
            container_id=f"{criteria_container_id}{search}",
            add_criteria=add_criteria,
        )

    async def rename_playlist(
        self, source_id: int, container_id: str, new_name: str
    ) -> None:
        """
        Rename a HEOS playlist.

        References:
            4.4.14 Rename HEOS Playlist
        """
        if new_name == "":
            raise ValueError("'new_name' parameter must not be empty")
        if len(new_name) > 128:
            raise ValueError(
                "'new_name' parameter must be less than or equal to 128 characters"
            )
        await self._connection.command(
            HeosCommand(
                c.COMMAND_BROWSE_RENAME_PLAYLIST,
                {
                    c.ATTR_SOURCE_ID: source_id,
                    c.ATTR_CONTAINER_ID: container_id,
                    c.ATTR_NAME: new_name,
                },
            )
        )

    async def delete_playlist(self, source_id: int, container_id: str) -> None:
        """
        Create a HEOS command to delete a playlist.

        References:
            4.4.15 Delete HEOS Playlist"""

        await self._connection.command(
            HeosCommand(
                c.COMMAND_BROWSE_DELETE__PLAYLIST,
                {
                    c.ATTR_SOURCE_ID: source_id,
                    c.ATTR_CONTAINER_ID: container_id,
                },
            )
        )

    async def retrieve_metadata(
        self, source_it: int, container_id: str
    ) -> RetreiveMetadataResult:
        """
        Create a HEOS command to retrieve metadata. Only supported by Rhapsody/Napster music sources.

        References:
            4.4.17 Retrieve Metadata
        """
        result = await self._connection.command(
            HeosCommand(
                c.COMMAND_BROWSE_RETRIEVE_METADATA,
                {
                    c.ATTR_SOURCE_ID: source_it,
                    c.ATTR_CONTAINER_ID: container_id,
                },
            )
        )
        return RetreiveMetadataResult._from_message(result)

    async def set_service_option(
        this,
        option_id: int,
        source_id: int | None = None,
        container_id: str | None = None,
        media_id: str | None = None,
        player_id: int | None = None,
        name: str | None = None,
        criteria_id: int | None = None,
        range_start: int | None = None,
        range_end: int | None = None,
    ) -> None:
        """
        Create a HEOS command to set a service option.

        References:
            4.4.19 Set Service Option
        """
        params: dict[str, Any] = {c.ATTR_OPTION_ID: option_id}
        disallowed_params = {}

        if option_id in (
            SERVICE_OPTION_ADD_TRACK_TO_LIBRARY,
            SERVICE_OPTION_ADD_STATION_TO_LIBRARY,
            SERVICE_OPTION_REMOVE_TRACK_FROM_LIBRARY,
            SERVICE_OPTION_REMOVE_STATION_FROM_LIBRARY,
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
            params[c.ATTR_SOURCE_ID] = source_id
            params[c.ATTR_MEDIA_ID] = media_id
        elif option_id in (
            SERVICE_OPTION_ADD_ALBUM_TO_LIBRARY,
            SERVICE_OPTION_REMOVE_ALBUM_FROM_LIBRARY,
            SERVICE_OPTION_REMOVE_PLAYLIST_FROM_LIBRARY,
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
            params[c.ATTR_SOURCE_ID] = source_id
            params[c.ATTR_CONTAINER_ID] = container_id
        elif option_id == SERVICE_OPTION_ADD_PLAYLIST_TO_LIBRARY:
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
            params[c.ATTR_SOURCE_ID] = source_id
            params[c.ATTR_CONTAINER_ID] = container_id
            params[c.ATTR_NAME] = name
        elif option_id in (
            SERVICE_OPTION_THUMBS_UP,
            SERVICE_OPTION_THUMBS_DOWN,
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
            params[c.ATTR_SOURCE_ID] = source_id
            params[c.ATTR_PLAYER_ID] = player_id
        elif option_id == SERVICE_OPTION_CREATE_NEW_STATION_BY_SEARCH_CRITERIA:
            if source_id is None or name is None or criteria_id is None:
                raise ValueError(
                    f"source_id, name, and criteria_id parameters are required for service option_id {option_id}"
                )
            disallowed_params = {
                "media_id": media_id,
                "container_id": container_id,
                "player_id": player_id,
            }
            params[c.ATTR_SOURCE_ID] = source_id
            params[c.ATTR_SEARCH_CRITERIA_ID] = criteria_id
            params[c.ATTR_NAME] = name
            if isinstance(range_start, int) and isinstance(range_end, int):
                params[c.ATTR_RANGE] = f"{range_start},{range_end}"
        elif option_id == SERVICE_OPTION_ADD_TO_FAVORITES:
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
                params[c.ATTR_PLAYER_ID] = player_id
            else:
                params[c.ATTR_SOURCE_ID] = source_id
                params[c.ATTR_MEDIA_ID] = media_id
                params[c.ATTR_NAME] = name
            disallowed_params = {
                "container_id": container_id,
                "criteria_id": criteria_id,
                "range_start": range_start,
                "range_end": range_end,
            }
        elif option_id == SERVICE_OPTION_REMOVE_FROM_FAVORITES:
            if media_id is None:
                raise ValueError(
                    f"media_id parameter is required for service option_id {option_id}"
                )
            params[c.ATTR_MEDIA_ID] = media_id
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

        await this._connection.command(
            HeosCommand(c.COMMAND_BROWSE_SET_SERVICE_OPTION, params)
        )

    async def play_media(
        self,
        player_id: int,
        media: MediaItem,
        add_criteria: AddCriteriaType = AddCriteriaType.PLAY_NOW,
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

        if media.media_id in VALID_INPUTS:
            await self.play_input_source(player_id, media.media_id, media.source_id)
        elif media.type == MediaType.STATION:
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
        result = await self.browse(MUSIC_SOURCE_AUX_INPUT)
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
        result = await self.browse(MUSIC_SOURCE_FAVORITES)
        return {index + 1: source for index, source in enumerate(result.items)}

    async def get_playlists(self) -> Sequence[MediaItem]:
        """
        Get available playlists.

        This will browse the playlists music source and return a list of all available playlists.

        Returns:
            A sequence of MediaItem instances representing the available playlists.
        """
        result = await self.browse(MUSIC_SOURCE_PLAYLISTS)
        return result.items

    async def multi_search(
        self,
        search: str,
        source_ids: list[int] | None = None,
        criteria_ids: list[int] | None = None,
    ) -> MultiSearchResult:
        """
        Create a HEOS command to perform a multi-search.

        References:
            4.4.20 Multi Search
        """
        if len(search) > 128:
            raise ValueError(
                "'search' parameter must be less than or equal to 128 characters"
            )
        params = {c.ATTR_SEARCH: search}
        if source_ids is not None:
            params[c.ATTR_SOURCE_ID] = ",".join(map(str, source_ids))
        if criteria_ids is not None:
            params[c.ATTR_SEARCH_CRITERIA_ID] = ",".join(map(str, criteria_ids))
        result = await self._connection.command(
            HeosCommand(c.COMMAND_BROWSE_MULTI_SEARCH, params)
        )
        return MultiSearchResult._from_message(result, cast("Heos", self))
