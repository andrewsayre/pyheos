"""Tests for the browse mixin of the Heos module."""

import pytest

from pyheos import const
from pyheos.heos import Heos
from pyheos.media import MediaMusicSource
from tests import calls_command
from tests.common import MediaMusicSources


@calls_command("browse.get_source_info", {const.ATTR_SOURCE_ID: 123456})
async def test_get_music_source_by_id(heos: Heos) -> None:
    """Test retrieving music source by id."""
    source = await heos.get_music_source_info(123456)
    assert source.source_id == 1
    assert source.name == "Pandora"
    assert (
        source.image_url
        == "https://production.ws.skyegloup.com:443/media/images/service/logos/pandora.png"
    )
    assert source.type == const.MediaType.MUSIC_SERVICE
    assert source.available
    assert source.service_username == "email@email.com"


@calls_command("browse.get_music_sources")
async def test_get_music_source_info_by_id_already_loaded(heos: Heos) -> None:
    """Test retrieving music source info by id for already loaded does not update."""
    sources = await heos.get_music_sources()
    original_source = sources[const.MUSIC_SOURCE_FAVORITES]
    retrived_source = await heos.get_music_source_info(original_source.source_id)
    assert original_source == retrived_source


@calls_command(
    "browse.get_source_info",
    {const.ATTR_SOURCE_ID: MediaMusicSources.FAVORITES.source_id},
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
    heos: Heos, source_id: int | None, music_source: MediaMusicSource | None, error: str
) -> None:
    """Test retrieving player info with invalid parameters raises."""
    with pytest.raises(ValueError, match=error):
        await heos.get_music_source_info(source_id=source_id, music_source=music_source)


@calls_command(
    "browse.get_search_criteria", {const.ATTR_SOURCE_ID: const.MUSIC_SOURCE_TIDAL}
)
async def test_get_search_criteria(heos: Heos) -> None:
    """Test retrieving search criteria."""
    criteria = await heos.get_search_criteria(const.MUSIC_SOURCE_TIDAL)
    assert len(criteria) == 4
    item = criteria[2]
    assert item.name == "Track"
    assert item.search_criteria_id == 3
    assert item.wildcard is False
    assert item.container_id == "SEARCHED_TRACKS-"
    assert item.playable is True
