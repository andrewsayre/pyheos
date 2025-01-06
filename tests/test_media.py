"""Define tests for browsing media."""

import re
from unittest.mock import Mock

import pytest

from pyheos import command, const
from pyheos.heos import Heos
from pyheos.media import BrowseResult, MediaItem, MediaMusicSource
from pyheos.message import HeosMessage
from tests import calls_command
from tests.common import MediaItems


async def test_media_music_source_from_data() -> None:
    """Test creating a media music source from data."""
    data = {
        const.ATTR_NAME: "Pandora",
        const.ATTR_IMAGE_URL: "https://production.ws.skyegloup.com:443/media/images/service/logos/pandora.png",
        const.ATTR_TYPE: const.MediaType.MUSIC_SERVICE,
        const.ATTR_SOURCE_ID: 1,
        const.ATTR_AVAILABLE: const.VALUE_TRUE,
        const.ATTR_SERVICE_USER_NAME: "test@test.com",
    }

    source = MediaMusicSource.from_data(data)

    assert source.name == data[const.ATTR_NAME]
    assert source.image_url == data[const.ATTR_IMAGE_URL]
    assert source.type == const.MediaType.MUSIC_SERVICE
    assert source.source_id == data[const.ATTR_SOURCE_ID]
    assert source.available
    assert source.service_username == data[const.ATTR_SERVICE_USER_NAME]
    with pytest.raises(
        AssertionError,
        match="Heos instance not set",
    ):
        await source.browse()


@calls_command(
    "browse.browse_favorites", {const.ATTR_SOURCE_ID: const.MUSIC_SOURCE_FAVORITES}
)
async def test_media_music_source_browse(
    media_music_source: MediaMusicSource,
) -> None:
    """Test browsing a media music source."""
    result = await media_music_source.browse()

    assert result.returned == 3
    assert result.source_id == const.MUSIC_SOURCE_FAVORITES
    # further testing of the result is done in test_browse_result_from_data


async def test_browse_result_from_data() -> None:
    """Test creating a browse result from data."""
    heos = Mock(Heos)
    message = HeosMessage(
        command.COMMAND_BROWSE_BROWSE,
        True,
        {const.ATTR_SOURCE_ID: "1025", const.ATTR_RETURNED: "1", const.ATTR_COUNT: "1"},
        [
            {
                const.ATTR_CONTAINER: const.VALUE_YES,
                const.ATTR_TYPE: str(const.MediaType.PLAYLIST),
                const.ATTR_CONTAINER_ID: "171566",
                const.ATTR_PLAYABLE: const.VALUE_YES,
                const.ATTR_NAME: "Rockin Songs",
                const.ATTR_IMAGE_URL: "",
            }
        ],
    )

    result = BrowseResult.from_data(message, heos)

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
        const.ATTR_NAME: "Imaginary Parties",
        const.ATTR_IMAGE_URL: "http://resources.wimpmusic.com/images/7e7bacc1/3e75/4761/a822/9342239edfa0/640x640.jpg",
        const.ATTR_TYPE: str(const.MediaType.SONG),
        const.ATTR_CONTAINER: const.VALUE_NO,
        const.ATTR_MEDIA_ID: "78374741",
        const.ATTR_ARTIST: "Superfruit",
        const.ATTR_ALBUM: "Future Friends",
        const.ATTR_ALBUM_ID: "78374740",
        const.ATTR_PLAYABLE: const.VALUE_YES,
    }

    source = MediaItem.from_data(data, source_id, container_id)

    assert source.name == data[const.ATTR_NAME]
    assert source.image_url == data[const.ATTR_IMAGE_URL]
    assert source.type == const.MediaType.SONG
    assert source.container_id == container_id
    assert source.source_id == source_id
    assert source.playable is True
    assert source.browsable is False
    assert source.album == data[const.ATTR_ALBUM]
    assert source.artist == data[const.ATTR_ARTIST]
    assert source.album_id == data[const.ATTR_ALBUM_ID]
    assert source.media_id == data[const.ATTR_MEDIA_ID]
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
        const.ATTR_NAME: "Video",
        const.ATTR_IMAGE_URL: "",
        const.ATTR_TYPE: str(const.MediaType.CONTAINER),
        const.ATTR_CONTAINER: const.VALUE_YES,
        const.ATTR_CONTAINER_ID: "94467912-bd40-4d2f-ad25-7b8423f7b05a",
    }

    with pytest.raises(
        ValueError,
        match=re.escape("'source_id' is required when not present in 'data'"),
    ):
        MediaItem.from_data(data)


async def test_media_item_from_data_source() -> None:
    """Test creating a MediaItem from data."""
    data = {
        const.ATTR_NAME: "Plex Media Server",
        const.ATTR_IMAGE_URL: "https://production.ws.skyegloup.com:443/media/images/service/logos/musicsource_logo_servers.png",
        const.ATTR_TYPE: str(const.MediaType.HEOS_SERVER),
        const.ATTR_SOURCE_ID: 123456789,
    }

    source = MediaItem.from_data(data)

    assert source.name == data[const.ATTR_NAME]
    assert source.image_url == data[const.ATTR_IMAGE_URL]
    assert source.type == const.MediaType.HEOS_SERVER
    assert source.source_id == data[const.ATTR_SOURCE_ID]
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
        const.ATTR_NAME: "Video",
        const.ATTR_IMAGE_URL: "",
        const.ATTR_TYPE: str(const.MediaType.CONTAINER),
        const.ATTR_CONTAINER: const.VALUE_YES,
        const.ATTR_CONTAINER_ID: "94467912-bd40-4d2f-ad25-7b8423f7b05a",
    }

    source = MediaItem.from_data(data, source_id)

    assert source.name == data[const.ATTR_NAME]
    assert source.image_url == data[const.ATTR_IMAGE_URL]
    assert source.type == const.MediaType.CONTAINER
    assert source.container_id == data[const.ATTR_CONTAINER_ID]
    assert source.source_id == source_id
    assert source.playable is False
    assert source.browsable is True
    assert source.album is None
    assert source.artist is None
    assert source.album_id is None
    assert source.media_id is None


@calls_command(
    "browse.browse_heos_drive", {const.ATTR_SOURCE_ID: MediaItems.DEVICE.source_id}
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
    "browse.add_to_queue_track",
    {
        const.ATTR_PLAYER_ID: 1,
        const.ATTR_SOURCE_ID: MediaItems.SONG.source_id,
        const.ATTR_CONTAINER_ID: MediaItems.SONG.container_id,
        const.ATTR_MEDIA_ID: MediaItems.SONG.media_id,
        const.ATTR_ADD_CRITERIA_ID: const.AddCriteriaType.REPLACE_AND_PLAY,
    },
    add_command_under_process=True,
)
async def test_media_item_play(media_item_song: MediaItem) -> None:
    """Test playing a media music source."""
    await media_item_song.play_media(1, const.AddCriteriaType.REPLACE_AND_PLAY)
