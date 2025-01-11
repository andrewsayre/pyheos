"""Define tests for browsing media."""

import re
from unittest.mock import Mock

import pytest

from pyheos import command as c
from pyheos.const import MUSIC_SOURCE_FAVORITES
from pyheos.heos import Heos
from pyheos.media import BrowseResult, MediaItem, MediaMusicSource
from pyheos.message import HeosMessage
from pyheos.types import AddCriteriaType, MediaType
from tests import calls_command
from tests.common import MediaItems, MediaMusicSources


async def test_media_music_source_from_data() -> None:
    """Test creating a media music source from data."""
    data = {
        c.ATTR_NAME: "Pandora",
        c.ATTR_IMAGE_URL: "https://production.ws.skyegloup.com:443/media/images/service/logos/pandora.png",
        c.ATTR_TYPE: MediaType.MUSIC_SERVICE,
        c.ATTR_SOURCE_ID: 1,
        c.ATTR_AVAILABLE: c.VALUE_TRUE,
        c.ATTR_SERVICE_USER_NAME: "test@test.com",
    }

    source = MediaMusicSource.from_data(data)

    assert source.name == data[c.ATTR_NAME]
    assert source.image_url == data[c.ATTR_IMAGE_URL]
    assert source.type == MediaType.MUSIC_SERVICE
    assert source.source_id == data[c.ATTR_SOURCE_ID]
    assert source.available
    assert source.service_username == data[c.ATTR_SERVICE_USER_NAME]
    with pytest.raises(
        AssertionError,
        match="Heos instance not set",
    ):
        await source.browse()


@calls_command("browse.browse_favorites", {c.ATTR_SOURCE_ID: MUSIC_SOURCE_FAVORITES})
async def test_media_music_source_browse(
    media_music_source: MediaMusicSource,
) -> None:
    """Test browsing a media music source."""
    result = await media_music_source.browse()

    assert result.returned == 3
    assert result.source_id == MUSIC_SOURCE_FAVORITES

    assert len(result.options) == 1
    option = result.options[0]
    assert option.context == "browse"
    assert option.name == "Remove from HEOS Favorites"
    assert option.id == 20

    # further testing of the result is done in test_browse_result_from_data


async def test_browse_result_from_data() -> None:
    """Test creating a browse result from data."""
    heos = Mock(Heos)
    message = HeosMessage(
        c.COMMAND_BROWSE_BROWSE,
        True,
        {
            c.ATTR_SOURCE_ID: "1025",
            c.ATTR_RETURNED: "1",
            c.ATTR_COUNT: "1",
        },
        [
            {
                c.ATTR_CONTAINER: c.VALUE_YES,
                c.ATTR_TYPE: str(MediaType.PLAYLIST),
                c.ATTR_CONTAINER_ID: "171566",
                c.ATTR_PLAYABLE: c.VALUE_YES,
                c.ATTR_NAME: "Rockin Songs",
                c.ATTR_IMAGE_URL: "",
            }
        ],
    )

    result = BrowseResult._from_message(message, heos)

    assert result.returned == 1
    assert result.count == 1
    assert result.source_id == 1025
    assert result.heos == heos
    assert len(result.items) == 1
    item = result.items[0]
    assert item.heos == heos


async def test_media_item_from_data() -> None:
    """Test creating a MediaItem from data."""
    source_id = 1
    container_id = "My Music"
    data = {
        c.ATTR_NAME: "Imaginary Parties",
        c.ATTR_IMAGE_URL: "http://resources.wimpmusic.com/images/7e7bacc1/3e75/4761/a822/9342239edfa0/640x640.jpg",
        c.ATTR_TYPE: str(MediaType.SONG),
        c.ATTR_CONTAINER: c.VALUE_NO,
        c.ATTR_MEDIA_ID: "78374741",
        c.ATTR_ARTIST: "Superfruit",
        c.ATTR_ALBUM: "Future Friends",
        c.ATTR_ALBUM_ID: "78374740",
        c.ATTR_PLAYABLE: c.VALUE_YES,
    }

    source = MediaItem.from_data(data, source_id, container_id)

    assert source.name == data[c.ATTR_NAME]
    assert source.image_url == data[c.ATTR_IMAGE_URL]
    assert source.type == MediaType.SONG
    assert source.container_id == container_id
    assert source.source_id == source_id
    assert source.playable is True
    assert source.browsable is False
    assert source.album == data[c.ATTR_ALBUM]
    assert source.artist == data[c.ATTR_ARTIST]
    assert source.album_id == data[c.ATTR_ALBUM_ID]
    assert source.media_id == data[c.ATTR_MEDIA_ID]
    with pytest.raises(
        AssertionError,
        match="Heos instance not set",
    ):
        await source.browse()
    with pytest.raises(
        AssertionError,
        match="Heos instance not set",
    ):
        await source.play_media(1)


async def test_media_item_from_data_source_id_not_present_raises() -> None:
    """Test creating a MediaItem from data."""
    data = {
        c.ATTR_NAME: "Video",
        c.ATTR_IMAGE_URL: "",
        c.ATTR_TYPE: str(MediaType.CONTAINER),
        c.ATTR_CONTAINER: c.VALUE_YES,
        c.ATTR_CONTAINER_ID: "94467912-bd40-4d2f-ad25-7b8423f7b05a",
    }

    with pytest.raises(
        ValueError,
        match=re.escape("'source_id' is required when not present in 'data'"),
    ):
        MediaItem.from_data(data)


async def test_media_item_from_data_source() -> None:
    """Test creating a MediaItem from data."""
    data = {
        c.ATTR_NAME: "Plex Media Server",
        c.ATTR_IMAGE_URL: "https://production.ws.skyegloup.com:443/media/images/service/logos/musicsource_logo_servers.png",
        c.ATTR_TYPE: str(MediaType.HEOS_SERVER),
        c.ATTR_SOURCE_ID: 123456789,
    }

    source = MediaItem.from_data(data)

    assert source.name == data[c.ATTR_NAME]
    assert source.image_url == data[c.ATTR_IMAGE_URL]
    assert source.type == MediaType.HEOS_SERVER
    assert source.source_id == data[c.ATTR_SOURCE_ID]
    assert source.container_id is None
    assert source.playable is False
    assert source.browsable is True
    assert source.album is None
    assert source.artist is None
    assert source.album_id is None
    assert source.media_id is None


async def test_media_item_from_data_container() -> None:
    """Test creating a MediaItem from data."""
    source_id = 123456789
    data = {
        c.ATTR_NAME: "Video",
        c.ATTR_IMAGE_URL: "",
        c.ATTR_TYPE: str(MediaType.CONTAINER),
        c.ATTR_CONTAINER: c.VALUE_YES,
        c.ATTR_CONTAINER_ID: "94467912-bd40-4d2f-ad25-7b8423f7b05a",
    }

    source = MediaItem.from_data(data, source_id)

    assert source.name == data[c.ATTR_NAME]
    assert source.image_url == data[c.ATTR_IMAGE_URL]
    assert source.type == MediaType.CONTAINER
    assert source.container_id == data[c.ATTR_CONTAINER_ID]
    assert source.source_id == source_id
    assert source.playable is False
    assert source.browsable is True
    assert source.album is None
    assert source.artist is None
    assert source.album_id is None
    assert source.media_id is None


@calls_command(
    "browse.browse_heos_drive", {c.ATTR_SOURCE_ID: MediaItems.DEVICE.source_id}
)
async def test_media_item_browse(media_item_device: MediaItem) -> None:
    """Test browsing a media music source."""
    result = await media_item_device.browse()

    assert result.container_id is None
    assert result.source_id == media_item_device.source_id
    assert result.returned == 8
    assert result.count == 8
    assert len(result.items) == 8


@calls_command(
    "browse.get_source_info",
    {c.ATTR_SOURCE_ID: MediaMusicSources.FAVORITES.source_id},
)
async def test_refresh(media_music_source: MediaMusicSource) -> None:
    """Test refresh updates the data."""
    await media_music_source.refresh()
    assert media_music_source.source_id == 1
    assert media_music_source.name == "Pandora"
    assert (
        media_music_source.image_url
        == "https://production.ws.skyegloup.com:443/media/images/service/logos/pandora.png"
    )
    assert media_music_source.type == MediaType.MUSIC_SERVICE
    assert media_music_source.available
    assert media_music_source.service_username == "email@email.com"


@calls_command(
    "browse.add_to_queue_track",
    {
        c.ATTR_PLAYER_ID: 1,
        c.ATTR_SOURCE_ID: MediaItems.SONG.source_id,
        c.ATTR_CONTAINER_ID: MediaItems.SONG.container_id,
        c.ATTR_MEDIA_ID: MediaItems.SONG.media_id,
        c.ATTR_ADD_CRITERIA_ID: AddCriteriaType.REPLACE_AND_PLAY,
    },
    add_command_under_process=True,
)
async def test_media_item_play(media_item_song: MediaItem) -> None:
    """Test playing a media music source."""
    await media_item_song.play_media(1, AddCriteriaType.REPLACE_AND_PLAY)
