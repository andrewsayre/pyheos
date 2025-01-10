"""Tests for the browse mixin of the Heos module."""

from typing import Any

import pytest

from pyheos import command as c
from pyheos.const import (
    MUSIC_SOURCE_FAVORITES,
    MUSIC_SOURCE_NAPSTER,
    MUSIC_SOURCE_PANDORA,
    MUSIC_SOURCE_PLAYLISTS,
    MUSIC_SOURCE_TIDAL,
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
)
from pyheos.heos import Heos, HeosOptions
from pyheos.media import MediaMusicSource
from pyheos.types import MediaType
from tests import calls_command, value
from tests.common import MediaMusicSources


@calls_command("browse.get_source_info", {c.ATTR_SOURCE_ID: 123456})
async def test_get_music_source_by_id(heos: Heos) -> None:
    """Test retrieving music source by id."""
    source = await heos.get_music_source_info(123456)
    assert source.source_id == 1
    assert source.name == "Pandora"
    assert (
        source.image_url
        == "https://production.ws.skyegloup.com:443/media/images/service/logos/pandora.png"
    )
    assert source.type == MediaType.MUSIC_SERVICE
    assert source.available
    assert source.service_username == "email@email.com"


@calls_command("browse.get_music_sources")
async def test_get_music_source_info_by_id_already_loaded(heos: Heos) -> None:
    """Test retrieving music source info by id for already loaded does not update."""
    sources = await heos.get_music_sources()
    original_source = sources[MUSIC_SOURCE_FAVORITES]
    retrived_source = await heos.get_music_source_info(original_source.source_id)
    assert original_source == retrived_source


@calls_command(
    "browse.get_source_info",
    {c.ATTR_SOURCE_ID: MediaMusicSources.FAVORITES.source_id},
)
async def test_get_music_source_info_by_id_already_loaded_refresh(
    heos: Heos, media_music_source: MediaMusicSource
) -> None:
    """Test retrieving player info by player id for already loaded player updates."""
    heos.music_sources[media_music_source.source_id] = media_music_source
    media_music_source.available = False
    retrived_source = await heos.get_music_source_info(
        media_music_source.source_id, refresh=True
    )
    assert media_music_source == retrived_source
    assert media_music_source.available


@pytest.mark.parametrize(
    ("source_id", "music_source", "error"),
    [
        (None, None, "Either source_id or music_source must be provided"),
        (
            1,
            object(),
            "Only one of source_id or music_source should be provided",
        ),
    ],
)
async def test_get_music_source_info_invalid_parameters_raises(
    source_id: int | None, music_source: MediaMusicSource | None, error: str
) -> None:
    """Test retrieving player info with invalid parameters raises."""
    heos = Heos(HeosOptions("127.0.0.1"))
    with pytest.raises(ValueError, match=error):
        await heos.get_music_source_info(source_id=source_id, music_source=music_source)


@calls_command("browse.get_search_criteria", {c.ATTR_SOURCE_ID: MUSIC_SOURCE_TIDAL})
async def test_get_search_criteria(heos: Heos) -> None:
    """Test retrieving search criteria."""
    criteria = await heos.get_search_criteria(MUSIC_SOURCE_TIDAL)
    assert len(criteria) == 4
    item = criteria[2]
    assert item.name == "Track"
    assert item.criteria_id == 3
    assert item.wildcard is False
    assert item.container_id == "SEARCHED_TRACKS-"
    assert item.playable is True


@calls_command(
    "browse.search",
    {
        c.ATTR_SOURCE_ID: MUSIC_SOURCE_TIDAL,
        c.ATTR_SEARCH_CRITERIA_ID: 3,
        c.ATTR_SEARCH: "Tangerine Rays",
    },
)
async def test_search(heos: Heos) -> None:
    """Test the search method."""

    result = await heos.search(MUSIC_SOURCE_TIDAL, "Tangerine Rays", 3)

    assert result.source_id == MUSIC_SOURCE_TIDAL
    assert result.criteria_id == 3
    assert result.search == "Tangerine Rays"
    assert result.returned == 15
    assert result.count == 15
    assert len(result.items) == 15


@pytest.mark.parametrize(
    ("search", "error"),
    [
        ("", "'search' parameter must not be empty"),
        ("x" * 129, "'search' parameter must be less than or equal to 128 characters"),
    ],
)
async def test_search_invalid_raises(heos: Heos, search: str, error: str) -> None:
    """Test the search method with an invalid search raises."""

    with pytest.raises(
        ValueError,
        match=error,
    ):
        await heos.search(MUSIC_SOURCE_TIDAL, search, 3)


@calls_command(
    "browse.search",
    {
        c.ATTR_SOURCE_ID: MUSIC_SOURCE_TIDAL,
        c.ATTR_SEARCH_CRITERIA_ID: 3,
        c.ATTR_SEARCH: "Tangerine Rays",
        c.ATTR_RANGE: "0,14",
    },
)
async def test_search_with_range(heos: Heos) -> None:
    """Test the search method."""

    result = await heos.search(
        MUSIC_SOURCE_TIDAL, "Tangerine Rays", 3, range_start=0, range_end=14
    )

    assert result.source_id == MUSIC_SOURCE_TIDAL
    assert result.criteria_id == 3
    assert result.search == "Tangerine Rays"
    assert result.returned == 15
    assert result.count == 15
    assert len(result.items) == 15


@calls_command(
    "browse.rename_playlist",
    {
        c.ATTR_SOURCE_ID: MUSIC_SOURCE_PLAYLISTS,
        c.ATTR_CONTAINER_ID: 171566,
        c.ATTR_NAME: "New Name",
    },
)
async def test_rename_playlist(heos: Heos) -> None:
    """Test renaming a playlist."""
    await heos.rename_playlist(MUSIC_SOURCE_PLAYLISTS, "171566", "New Name")


@pytest.mark.parametrize(
    ("name", "error"),
    [
        ("", "'new_name' parameter must not be empty"),
        (
            "x" * 129,
            "'new_name' parameter must be less than or equal to 128 characters",
        ),
    ],
)
async def test_rename_playlist_invalid_name_raises(
    heos: Heos, name: str, error: str
) -> None:
    """Test renaming a playlist."""
    with pytest.raises(
        ValueError,
        match=error,
    ):
        await heos.rename_playlist(MUSIC_SOURCE_PLAYLISTS, "171566", name)


@calls_command(
    "browse.delete_playlist",
    {
        c.ATTR_SOURCE_ID: MUSIC_SOURCE_PLAYLISTS,
        c.ATTR_CONTAINER_ID: 171566,
    },
)
async def test_delete_playlist(heos: Heos) -> None:
    """Test deleting a playlist."""
    await heos.delete_playlist(MUSIC_SOURCE_PLAYLISTS, "171566")


@calls_command(
    "browse.retrieve_metadata",
    {
        c.ATTR_SOURCE_ID: MUSIC_SOURCE_NAPSTER,
        c.ATTR_CONTAINER_ID: 123456,
    },
)
async def test_retrieve_metadata(heos: Heos) -> None:
    """Test deleting a playlist."""
    result = await heos.retrieve_metadata(MUSIC_SOURCE_NAPSTER, "123456")
    assert result.source_id == MUSIC_SOURCE_NAPSTER
    assert result.container_id == "123456"
    assert result.returned == 1
    assert result.count == 1
    assert len(result.metadata) == 1
    metadata = result.metadata[0]
    assert metadata.album_id == "7890"
    assert len(metadata.images) == 2
    image = metadata.images[0]
    assert (
        image.image_url
        == "http://resources.wimpmusic.com/images/fbfe5e8b/b775/4d97/9053/8f0ac7daf4fd/640x640.jpg"
    )
    assert image.width == 640


@calls_command(
    "browse.set_service_option_add_favorite",
    {
        c.ATTR_OPTION_ID: SERVICE_OPTION_ADD_TO_FAVORITES,
        c.ATTR_PLAYER_ID: 1,
    },
)
async def test_set_service_option_add_favorite_play(heos: Heos) -> None:
    """Test setting a service option for adding to favorites."""
    await heos.set_service_option(SERVICE_OPTION_ADD_TO_FAVORITES, player_id=1)


@calls_command(
    "browse.set_service_option_add_favorite_browse",
    {
        c.ATTR_OPTION_ID: SERVICE_OPTION_ADD_TO_FAVORITES,
        c.ATTR_SOURCE_ID: MUSIC_SOURCE_PANDORA,
        c.ATTR_MEDIA_ID: 123456,
        c.ATTR_NAME: "Test Radio",
    },
)
async def test_set_service_option_add_favorite_browse(heos: Heos) -> None:
    """Test setting a service option for adding to favorites."""
    await heos.set_service_option(
        SERVICE_OPTION_ADD_TO_FAVORITES,
        source_id=MUSIC_SOURCE_PANDORA,
        media_id="123456",
        name="Test Radio",
    )


@calls_command(
    "browse.set_service_option_remove_favorite",
    {
        c.ATTR_OPTION_ID: SERVICE_OPTION_REMOVE_FROM_FAVORITES,
        c.ATTR_MEDIA_ID: 4277097921440801039,
    },
)
async def test_set_service_option_remove_favorite(heos: Heos) -> None:
    """Test setting a service option for adding to favorites."""
    await heos.set_service_option(
        SERVICE_OPTION_REMOVE_FROM_FAVORITES, media_id="4277097921440801039"
    )


@pytest.mark.parametrize(
    "option", [SERVICE_OPTION_THUMBS_UP, SERVICE_OPTION_THUMBS_DOWN]
)
@calls_command(
    "browse.set_service_option_thumbs_up_down",
    {
        c.ATTR_OPTION_ID: value(arg_name="option"),
        c.ATTR_SOURCE_ID: MUSIC_SOURCE_PANDORA,
        c.ATTR_PLAYER_ID: 1,
    },
)
async def test_set_service_option_thumbs_up_down(heos: Heos, option: int) -> None:
    """Test setting thumbs up/down."""
    await heos.set_service_option(
        option,
        source_id=MUSIC_SOURCE_PANDORA,
        player_id=1,
    )


@pytest.mark.parametrize(
    "option",
    [
        SERVICE_OPTION_ADD_TRACK_TO_LIBRARY,
        SERVICE_OPTION_ADD_STATION_TO_LIBRARY,
        SERVICE_OPTION_REMOVE_TRACK_FROM_LIBRARY,
        SERVICE_OPTION_REMOVE_STATION_FROM_LIBRARY,
    ],
)
@calls_command(
    "browse.set_service_option_track_station",
    {
        c.ATTR_OPTION_ID: value(arg_name="option"),
        c.ATTR_SOURCE_ID: MUSIC_SOURCE_PANDORA,
        c.ATTR_MEDIA_ID: 1234,
    },
)
async def test_set_service_option_track_station(heos: Heos, option: int) -> None:
    """Test setting track and station options."""
    await heos.set_service_option(
        option,
        source_id=MUSIC_SOURCE_PANDORA,
        media_id="1234",
    )


@pytest.mark.parametrize(
    "option",
    [
        SERVICE_OPTION_ADD_ALBUM_TO_LIBRARY,
        SERVICE_OPTION_REMOVE_ALBUM_FROM_LIBRARY,
        SERVICE_OPTION_REMOVE_PLAYLIST_FROM_LIBRARY,
    ],
)
@calls_command(
    "browse.set_service_option_album_remove_playlist",
    {
        c.ATTR_OPTION_ID: value(arg_name="option"),
        c.ATTR_SOURCE_ID: MUSIC_SOURCE_PANDORA,
        c.ATTR_CONTAINER_ID: 1234,
    },
)
async def test_set_service_option_album_remove_playlist(
    heos: Heos, option: int
) -> None:
    """Test setting albumn options and remove playlist options."""
    await heos.set_service_option(
        option,
        source_id=MUSIC_SOURCE_PANDORA,
        container_id="1234",
    )


@calls_command(
    "browse.set_service_option_add_playlist",
    {
        c.ATTR_OPTION_ID: SERVICE_OPTION_ADD_PLAYLIST_TO_LIBRARY,
        c.ATTR_SOURCE_ID: MUSIC_SOURCE_PANDORA,
        c.ATTR_CONTAINER_ID: 1234,
        c.ATTR_NAME: "Test Playlist",
    },
)
async def test_set_service_option_add_playlist(heos: Heos) -> None:
    """Test setting albumn options and remove playlist options."""
    await heos.set_service_option(
        SERVICE_OPTION_ADD_PLAYLIST_TO_LIBRARY,
        source_id=MUSIC_SOURCE_PANDORA,
        container_id="1234",
        name="Test Playlist",
    )


@calls_command(
    "browse.set_service_option_new_station",
    {
        c.ATTR_OPTION_ID: SERVICE_OPTION_CREATE_NEW_STATION_BY_SEARCH_CRITERIA,
        c.ATTR_SOURCE_ID: MUSIC_SOURCE_PANDORA,
        c.ATTR_SEARCH_CRITERIA_ID: 1234,
        c.ATTR_NAME: "Test",
        c.ATTR_RANGE: "0,14",
    },
)
async def test_set_service_option_new_station(heos: Heos) -> None:
    """Test setting creating a new station option."""
    await heos.set_service_option(
        SERVICE_OPTION_CREATE_NEW_STATION_BY_SEARCH_CRITERIA,
        source_id=MUSIC_SOURCE_PANDORA,
        criteria_id=1234,
        name="Test",
        range_start=0,
        range_end=14,
    )


@pytest.mark.parametrize(
    ("kwargs", "error"),
    [
        (
            {"option_id": 200},
            "Unknown option_id",
        ),
        # SERVICE_OPTION_ADD_PLAYLIST_TO_LIBRARY
        (
            {"option_id": SERVICE_OPTION_ADD_PLAYLIST_TO_LIBRARY},
            "source_id, container_id, and name parameters are required",
        ),
        (
            {
                "option_id": SERVICE_OPTION_ADD_PLAYLIST_TO_LIBRARY,
                "source_id": 1234,
            },
            "source_id, container_id, and name parameters are required",
        ),
        (
            {
                "option_id": SERVICE_OPTION_ADD_PLAYLIST_TO_LIBRARY,
                "container_id": 1234,
            },
            "source_id, container_id, and name parameters are required",
        ),
        (
            {
                "option_id": SERVICE_OPTION_ADD_PLAYLIST_TO_LIBRARY,
                "name": 1234,
            },
            "source_id, container_id, and name parameters are required",
        ),
        (
            {
                "option_id": SERVICE_OPTION_ADD_PLAYLIST_TO_LIBRARY,
                "source_id": 1234,
                "name": 1234,
                "media_id": 1234,
                "container_id": 1234,
            },
            "parameters are not allowed",
        ),
        # SERVICE_OPTION_CREATE_NEW_STATION_BY_SEARCH_CRITERIA
        (
            {"option_id": SERVICE_OPTION_CREATE_NEW_STATION_BY_SEARCH_CRITERIA},
            "source_id, name, and criteria_id parameters are required",
        ),
        (
            {
                "option_id": SERVICE_OPTION_CREATE_NEW_STATION_BY_SEARCH_CRITERIA,
                "source_id": 1234,
            },
            "source_id, name, and criteria_id parameters are required",
        ),
        (
            {
                "option_id": SERVICE_OPTION_CREATE_NEW_STATION_BY_SEARCH_CRITERIA,
                "name": 1234,
            },
            "source_id, name, and criteria_id parameters are required",
        ),
        (
            {
                "option_id": SERVICE_OPTION_CREATE_NEW_STATION_BY_SEARCH_CRITERIA,
                "criteria_id": 1234,
            },
            "source_id, name, and criteria_id parameters are required",
        ),
        (
            {
                "option_id": SERVICE_OPTION_CREATE_NEW_STATION_BY_SEARCH_CRITERIA,
                "criteria_id": 1234,
                "name": 1234,
            },
            "source_id, name, and criteria_id parameters are required",
        ),
        (
            {
                "option_id": SERVICE_OPTION_CREATE_NEW_STATION_BY_SEARCH_CRITERIA,
                "criteria_id": 1234,
                "source_id": 1234,
            },
            "source_id, name, and criteria_id parameters are required",
        ),
        (
            {
                "option_id": SERVICE_OPTION_CREATE_NEW_STATION_BY_SEARCH_CRITERIA,
                "name": 1234,
                "source_id": 1234,
            },
            "source_id, name, and criteria_id parameters are required",
        ),
        (
            {
                "option_id": SERVICE_OPTION_CREATE_NEW_STATION_BY_SEARCH_CRITERIA,
                "criteria_id": 1234,
                "name": 1234,
                "source_id": 1234,
                "player_id": 1234,
            },
            "parameters are not allowed",
        ),
        # SERVICE_OPTION_REMOVE_FROM_FAVORITES
        (
            {"option_id": SERVICE_OPTION_REMOVE_FROM_FAVORITES},
            "media_id parameter is required",
        ),
        (
            {
                "option_id": SERVICE_OPTION_REMOVE_FROM_FAVORITES,
                "media_id": 1234,
                "container_id": 1234,
            },
            "parameters are not allowed",
        ),
    ],
)
async def test_set_sevice_option_invalid_raises(
    kwargs: dict[str, Any], error: str
) -> None:
    """Test calling with invalid combinations of parameters raises."""
    heos = Heos(HeosOptions("127.0.0.1"))

    with pytest.raises(ValueError, match=error):
        await heos.set_service_option(**kwargs)


@pytest.mark.parametrize(
    "option",
    [
        SERVICE_OPTION_ADD_TRACK_TO_LIBRARY,
        SERVICE_OPTION_ADD_STATION_TO_LIBRARY,
        SERVICE_OPTION_REMOVE_TRACK_FROM_LIBRARY,
        SERVICE_OPTION_REMOVE_STATION_FROM_LIBRARY,
    ],
)
@pytest.mark.parametrize(
    ("kwargs", "error"),
    [
        (
            {},
            "source_id and media_id parameters are required",
        ),
        (
            {"media_id": 1234},
            "source_id and media_id parameters are required",
        ),
        (
            {"source_id": 1234},
            "source_id and media_id parameters are required",
        ),
        (
            {"source_id": 1234, "media_id": 1234, "container_id": 1234},
            "parameters are not allowed for service option_id",
        ),
    ],
)
async def test_set_sevice_option_invalid_track_station_raises(
    option: int, kwargs: dict[str, Any], error: str
) -> None:
    """Test calling with invalid combinations of parameters raises."""
    heos = Heos(HeosOptions("127.0.0.1"))
    with pytest.raises(ValueError, match=error):
        await heos.set_service_option(option_id=option, **kwargs)


@pytest.mark.parametrize(
    "option",
    [
        SERVICE_OPTION_ADD_ALBUM_TO_LIBRARY,
        SERVICE_OPTION_REMOVE_ALBUM_FROM_LIBRARY,
        SERVICE_OPTION_REMOVE_PLAYLIST_FROM_LIBRARY,
    ],
)
@pytest.mark.parametrize(
    ("kwargs", "error"),
    [
        (
            {},
            "source_id and container_id parameters are required",
        ),
        (
            {"source_id": 1234},
            "source_id and container_id parameters are required",
        ),
        (
            {"container_id": 1234},
            "source_id and container_id parameters are required",
        ),
        (
            {"source_id": 1234, "media_id": 1234, "container_id": 1234},
            "parameters are not allowed for service option_id",
        ),
    ],
)
async def test_set_sevice_option_invalid_album_remove_playlist_raises(
    option: int, kwargs: dict[str, Any], error: str
) -> None:
    """Test calling with invalid combinations of parameters raises."""
    heos = Heos(HeosOptions("127.0.0.1"))
    with pytest.raises(ValueError, match=error):
        await heos.set_service_option(option_id=option, **kwargs)


@pytest.mark.parametrize(
    "option",
    [
        SERVICE_OPTION_THUMBS_UP,
        SERVICE_OPTION_THUMBS_DOWN,
    ],
)
@pytest.mark.parametrize(
    ("kwargs", "error"),
    [
        (
            {},
            "source_id and player_id parameters are required",
        ),
        (
            {"source_id": 1234},
            "source_id and player_id parameters are required",
        ),
        (
            {"player_id": 1234},
            "source_id and player_id parameters are required",
        ),
        (
            {"source_id": 1234, "player_id": 1234, "container_id": 1234},
            "parameters are not allowed for service option_id",
        ),
    ],
)
async def test_set_sevice_option_invalid_thumbs_up_down_raises(
    option: int, kwargs: dict[str, Any], error: str
) -> None:
    """Test calling with invalid combinations of parameters raises."""
    heos = Heos(HeosOptions("127.0.0.1"))
    with pytest.raises(ValueError, match=error):
        await heos.set_service_option(option_id=option, **kwargs)


@pytest.mark.parametrize(
    ("kwargs", "error"),
    [
        (
            {},
            "Either parameters player_id OR source_id, media_id, and name are required",
        ),
        (
            {"source_id": 1234},
            "Either parameters player_id OR source_id, media_id, and name are required",
        ),
        (
            {"media_id": 1234},
            "Either parameters player_id OR source_id, media_id, and name are required",
        ),
        (
            {"name": 1234},
            "Either parameters player_id OR source_id, media_id, and name are required",
        ),
        (
            {"source_id": 1234, "media_id": 1234},
            "Either parameters player_id OR source_id, media_id, and name are required",
        ),
        (
            {"source_id": 1234, "name": 1234},
            "Either parameters player_id OR source_id, media_id, and name are required",
        ),
        (
            {"media_id": 1234, "name": 1234},
            "Either parameters player_id OR source_id, media_id, and name are required",
        ),
        (
            {"player_id": 1234, "media_id": 1234},
            "source_id, media_id, and name parameters are not allowed",
        ),
        (
            {"player_id": 1234, "source_id": 1234},
            "source_id, media_id, and name parameters are not allowed",
        ),
        (
            {"player_id": 1234, "name": 1234},
            "source_id, media_id, and name parameters are not allowed",
        ),
        (
            {"source_id": 1234, "media_id": 1234, "name": 1234, "container_id": 1234},
            "parameters are not allowed for service option_id",
        ),
        (
            {"player_id": 1234, "container_id": 1234},
            "parameters are not allowed for service option_id",
        ),
    ],
)
async def test_set_sevice_option_invalid_add_favorite_raises(
    kwargs: dict[str, Any], error: str
) -> None:
    """Test calling with invalid combinations of parameters raises."""
    heos = Heos(HeosOptions("127.0.0.1"))
    with pytest.raises(ValueError, match=error):
        await heos.set_service_option(
            option_id=SERVICE_OPTION_ADD_TO_FAVORITES, **kwargs
        )


@calls_command(
    "browse.multi_search",
    {
        c.ATTR_SEARCH: "Tangerine Rays",
        c.ATTR_SOURCE_ID: "1,4,8,13,10",
        c.ATTR_SEARCH_CRITERIA_ID: "0,1,2,3",
    },
)
async def test_multi_search(heos: Heos) -> None:
    """Test the multi-search c."""
    result = await heos.multi_search(
        "Tangerine Rays",
        [1, 4, 8, 13, 10],
        [0, 1, 2, 3],
    )

    assert result.search == "Tangerine Rays"
    assert result.source_ids == [1, 4, 8, 13, 10]
    assert result.criteria_ids == [0, 1, 2, 3]
    assert result.returned == 74
    assert result.count == 74
    assert len(result.items) == 74
    assert len(result.statistics) == 4
    assert len(result.errors) == 2


async def test_multi_search_invalid_search_rasis() -> None:
    """Test the multi-search c."""
    heos = Heos(HeosOptions("127.0.0.1"))
    with pytest.raises(
        ValueError,
        match="'search' parameter must be less than or equal to 128 characters",
    ):
        await heos.multi_search("x" * 129)
