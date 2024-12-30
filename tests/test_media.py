"""Define tests for browsing media."""

import pytest

from pyheos import const
from pyheos.error import CommandFailedError
from pyheos.heos import Heos
from pyheos.media import MediaItem, MediaMusicSource, MediaType
from tests import MockHeosDevice


@pytest.mark.asyncio
async def test_media_music_source_from_data() -> None:
    """Test creating a media music source from data."""
    data = {
        const.ATTR_NAME: "Pandora",
        const.ATTR_IMAGE_URL: "https://production.ws.skyegloup.com:443/media/images/service/logos/pandora.png",
        const.ATTR_TYPE: MediaType.MUSIC_SERVICE,
        const.ATTR_SOURCE_ID: 1,
        const.ATTR_AVAILABLE: const.VALUE_TRUE,
        const.ATTR_SERVICE_USER_NAME: "test@test.com",
    }

    source = MediaMusicSource.from_data(data)

    assert source.name == data[const.ATTR_NAME]
    assert source.image_url == data[const.ATTR_IMAGE_URL]
    assert source.type == MediaType.MUSIC_SERVICE
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
            const.ATTR_TYPE: MediaType.HEOS_SERVICE,
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


@pytest.mark.skip
async def print_source(source: MediaItem, level: int = 0) -> None:
    """Print the source and its contents."""
    if level > 3:
        print(f"{'    ' * (level)}{source}")
        return

    if source.container_id:
        print(
            f"{'    ' * level}{source.name} (sid={source.source_id}&cid={source.container_id}) ->"
        )
    else:
        print(f"{'    ' * level}{source.name} (sid={source.source_id}) ->")

    try:
        result = await source.browse(0, 5)
    except CommandFailedError:
        return

    for item in result.items:
        if item.browsable:
            await print_source(item, level + 1)
        else:
            print(f"{'    ' * (level + 1)}{item}")
    print("")
