"""Test fixtures for pyheos."""

from collections.abc import AsyncGenerator, Callable, Coroutine
from typing import Any

import pytest
import pytest_asyncio

from pyheos import const
from pyheos.heos import Heos
from pyheos.media import MediaItem, MediaMusicSource

from . import MockHeosDevice


@pytest_asyncio.fixture(name="mock_device")
async def mock_device_fixture() -> AsyncGenerator[MockHeosDevice]:
    """Fixture for mocking a HEOS device connection."""
    device = MockHeosDevice()
    await device.start()
    yield device
    await device.stop()


@pytest_asyncio.fixture(name="heos")
async def heos_fixture() -> AsyncGenerator[Heos]:
    """Fixture for a connected heos."""
    heos = await Heos.create_and_connect(
        "127.0.0.1",
        timeout=0.1,
        auto_reconnect_delay=0.1,
        heart_beat=False,
    )
    yield heos
    await heos.disconnect()


@pytest.fixture
def handler() -> Callable:
    """Fixture handler to mock in the dispatcher."""

    def target(*args: Any, **kwargs: Any) -> None:
        target.fired = True  # type: ignore[attr-defined]
        target.args = args  # type: ignore[attr-defined]
        target.kwargs = kwargs  # type: ignore[attr-defined]

    target.fired = False  # type: ignore[attr-defined]
    return target


@pytest.fixture
def async_handler() -> Callable[..., Coroutine]:
    """Fixture async handler to mock in the dispatcher."""

    async def target(*args: Any, **kwargs: Any) -> None:
        target.fired = True  # type: ignore[attr-defined]
        target.args = args  # type: ignore[attr-defined]
        target.kwargs = kwargs  # type: ignore[attr-defined]

    target.fired = False  # type: ignore[attr-defined]
    return target


@pytest.fixture
def media_item_song_data() -> dict[str, str]:
    return {
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


@pytest.fixture
def media_music_source() -> MediaMusicSource:
    return MediaMusicSource(
        const.MUSIC_SOURCE_FAVORITES,
        "Favorites",
        const.MediaType.HEOS_SERVICE,
        "",
        None,
        True,
        None,
    )


@pytest.fixture
def media_music_source_unavailable() -> MediaMusicSource:
    return MediaMusicSource(
        const.MUSIC_SOURCE_PANDORA,
        "Pandora",
        const.MediaType.MUSIC_SERVICE,
        "",
        None,
        False,
        None,
    )


@pytest.fixture
def media_item_album() -> MediaItem:
    return MediaItem(
        const.MUSIC_SOURCE_TIDAL,
        "After Hours",
        const.MediaType.ALBUM,
        "http://resources.wimpmusic.com/images/bbe7f53c/44f0/41ba/873f/743e3091adde/160x160.jpg",
        None,
        True,
        True,
        "LIBALBUM-134788273",
        None,
        "The Weeknd",
        None,
        None,
    )


@pytest.fixture
def media_item_song() -> MediaItem:
    return MediaItem(
        1025,
        "Imaginary Parties",
        const.MediaType.SONG,
        "http://resources.wimpmusic.com/images/7e7bacc1/3e75/4761/a822/9342239edfa0/640x640.jpg",
        None,
        True,
        False,
        "123",
        "456",
        "Superfruit",
        "Future Friends",
        "78374740",
    )


@pytest.fixture
def media_item_input() -> MediaItem:
    return MediaItem(
        -263109739,
        "HEOS Drive - AUX In 1",
        const.MediaType.STATION,
        "",
        None,
        True,
        False,
        None,
        "inputs/aux_in_1",
        None,
        None,
        None,
    )


@pytest.fixture
def media_item_station() -> MediaItem:
    return MediaItem(
        1,
        "Cooltime Kids (Children's) Radio",
        const.MediaType.STATION,
        "https://content-images.p-cdn.com/images/9d/b9/b9/85/ef1146388a09ecb87153e168/_500W_500H.jpg",
        None,
        True,
        False,
        "A-Z",
        "3853208159976579343",
        None,
        None,
        None,
    )
