"""Define tests for browsing media."""

import re
from unittest.mock import Mock

import pytest

from pyheos import const
from pyheos.heos import Heos
from pyheos.media import BrowseResult, MediaItem, MediaMusicSource
from pyheos.message import HeosMessage
from tests import MockHeosDevice


@pytest.mark.asyncio
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
        ValueError,
        match="Must be initialized with the 'heos' parameter to browse",
    ):
        await source.browse()


@pytest.mark.asyncio
async def test_media_music_source_browse(
    mock_device: MockHeosDevice, heos: Heos
) -> None:
    """Test browsing a media music source."""
    mock_device.register(
        const.COMMAND_BROWSE_BROWSE,
        {const.ATTR_SOURCE_ID: const.MUSIC_SOURCE_FAVORITES},
        "browse.browse_favorites",
    )
    source = MediaMusicSource.from_data(
        {
            const.ATTR_NAME: "Favorites",
            const.ATTR_IMAGE_URL: "https://production.ws.skyegloup.com:443/media/images/service/logos/musicsource_logo_favorites.png",
            const.ATTR_TYPE: const.MediaType.HEOS_SERVICE,
            const.ATTR_SOURCE_ID: const.MUSIC_SOURCE_FAVORITES,
            const.ATTR_AVAILABLE: const.VALUE_TRUE,
            const.ATTR_SERVICE_USER_NAME: "test@test.com",
        },
        heos,
    )

    result = await source.browse()

    assert result.returned == 3
    assert result.source_id == const.MUSIC_SOURCE_FAVORITES
    # further testing of the result is done in test_browse_result_from_data


@pytest.mark.asyncio
async def test_browse_result_from_data() -> None:
    """Test creating a browse result from data."""
    heos = Mock(Heos)
    message = HeosMessage(
        '{"heos": {"command": "browse/browse", "result": "success", "message": "sid=1025&returned=1&count=1"}, "payload": [{"container": "yes", "type": "playlist", "cid": "171566", "playable": "yes", "name": "Rockin Songs", "image_url": ""}]}'
    )

    result = BrowseResult.from_data(message, heos)

    assert result.returned == 1
    assert result.count == 1
    assert result.source_id == 1025
    assert result._heos == heos
    assert len(result.items) == 1
    item = result.items[0]
    assert item._heos == heos


@pytest.mark.asyncio
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
        ValueError,
        match="Must be initialized with the 'heos' parameter to browse",
    ):
        await source.browse()


@pytest.mark.asyncio
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


@pytest.mark.asyncio
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


@pytest.mark.asyncio
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


@pytest.mark.asyncio
async def test_media_item_browse(mock_device: MockHeosDevice, heos: Heos) -> None:
    """Test browsing a media music source."""
    source_id = -263109739
    mock_device.register(
        const.COMMAND_BROWSE_BROWSE,
        {const.ATTR_SOURCE_ID: source_id},
        "browse.browse_heos_drive",
    )
    media_item = MediaItem.from_data(
        {
            const.ATTR_NAME: "HEOS Drive",
            const.ATTR_IMAGE_URL: "https://production.ws.skyegloup.com:443/media/images/service/logos/musicsource_logo_aux.png",
            const.ATTR_TYPE: str(const.MediaType.HEOS_SERVICE),
            const.ATTR_SOURCE_ID: source_id,
        },
        heos=heos,
    )

    result = await media_item.browse()

    assert result.container_id is None
    assert result.source_id == source_id
    assert result.returned == 8
    assert result.count == 8
    assert len(result.items) == 8
