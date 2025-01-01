"""Define tests for browsing media."""

import re
from unittest.mock import Mock

import pytest

from pyheos import const
from pyheos.heos import Heos
from pyheos.media import BrowseResult, MediaItem, MediaMusicSource
from pyheos.message import HeosMessage
from tests import MockHeosDevice


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


@pytest.mark.parametrize(
    "raw_message",
    [
        (
            '{"heos": {"command": "browse/browse", "result": "success", "message": "sid=1025&returned=1&count=1"}, '
            '"payload": [{"container": "yes", "type": "playlist", "cid": "171566", "playable": "yes", "name": "Rockin Songs", "image_url": ""}]}'
        )
    ],
)
async def test_browse_result_from_data(raw_message: str) -> None:
    """Test creating a browse result from data."""
    heos = Mock(Heos)
    message = HeosMessage(raw_message)

    result = BrowseResult.from_data(message, heos)

    assert result.returned == 1
    assert result.count == 1
    assert result.source_id == 1025
    assert result._heos == heos
    assert len(result.items) == 1
    item = result.items[0]
    assert item._heos == heos


async def test_media_item_from_data(media_item_song_data: dict[str, str]) -> None:
    """Test creating a MediaItem from data."""

    source_id = 1
    container_id = "My Music"

    source = MediaItem.from_data(media_item_song_data, source_id, container_id)

    assert source.name == media_item_song_data[const.ATTR_NAME]
    assert source.image_url == media_item_song_data[const.ATTR_IMAGE_URL]
    assert source.type == const.MediaType.SONG
    assert source.container_id == container_id
    assert source.source_id == source_id
    assert source.playable is True
    assert source.browsable is False
    assert source.album == media_item_song_data[const.ATTR_ALBUM]
    assert source.artist == media_item_song_data[const.ATTR_ARTIST]
    assert source.album_id == media_item_song_data[const.ATTR_ALBUM_ID]
    assert source.media_id == media_item_song_data[const.ATTR_MEDIA_ID]
    with pytest.raises(
        ValueError,
        match="Must be initialized with the 'heos' parameter to browse",
    ):
        await source.browse()
    with pytest.raises(
        ValueError,
        match="Must be initialized with the 'heos' parameter to play",
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


async def test_media_item_play(
    mock_device: MockHeosDevice, heos: Heos, media_item_song_data: dict[str, str]
) -> None:
    """Test playing a media music source."""
    media = MediaItem.from_data(
        media_item_song_data,
        source_id=const.MUSIC_SOURCE_PLAYLISTS,
        container_id="321",
        heos=heos,
    )
    args = {
        const.ATTR_PLAYER_ID: "1",
        const.ATTR_SOURCE_ID: media.source_id,
        const.ATTR_CONTAINER_ID: media.container_id,
        const.ATTR_MEDIA_ID: media.media_id,
        const.ATTR_ADD_CRITERIA_ID: str(const.AddCriteriaType.REPLACE_AND_PLAY),
    }
    mock_device.register(
        const.COMMAND_BROWSE_ADD_TO_QUEUE, args, "browse.add_to_queue_track"
    )

    await media.play_media(1, const.AddCriteriaType.REPLACE_AND_PLAY)
