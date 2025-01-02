"""Test fixtures for pyheos."""

from collections.abc import AsyncGenerator, Callable, Coroutine
from typing import Any

import pytest
import pytest_asyncio

from pyheos import const
from pyheos.group import HeosGroup
from pyheos.heos import Heos, HeosOptions
from pyheos.media import MediaItem, MediaMusicSource
from pyheos.player import HeosPlayer
from tests.common import MediaItems, MediaMusicSources

from . import MockHeos, MockHeosDevice


@pytest_asyncio.fixture(name="mock_device")
async def mock_device_fixture() -> AsyncGenerator[MockHeosDevice]:
    """Fixture for mocking a HEOS device connection."""
    device = MockHeosDevice()
    await device.start()
    yield device
    await device.stop()


@pytest_asyncio.fixture(name="heos")
async def heos_fixture(mock_device: MockHeosDevice) -> AsyncGenerator[Heos]:
    """Fixture for a connected heos."""
    heos = MockHeos(
        HeosOptions(
            "127.0.0.1",
            timeout=0.1,
            auto_reconnect_delay=0.1,
            heart_beat=False,
        )
    )
    heos.device = mock_device
    await heos.connect()
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
    return MediaMusicSources.FAVORITES.clone()


@pytest.fixture
def media_music_source_unavailable() -> MediaMusicSource:
    return MediaMusicSources.PANDORA.clone()


@pytest.fixture
def media_item_album() -> MediaItem:
    return MediaItems.ALBUM.clone()


@pytest.fixture
def media_item_song() -> MediaItem:
    return MediaItems.SONG.clone()


@pytest.fixture(name="media_item_input")
def media_item_input_fixture() -> MediaItem:
    return MediaItems.INPUT.clone()


@pytest.fixture
def media_item_station() -> MediaItem:
    return MediaItems.STATION.clone()


@pytest_asyncio.fixture(name="player_back_patio")
async def player_back_patio_fixture(heos: MockHeos) -> HeosPlayer:
    """Fixture for a player."""
    return HeosPlayer(
        heos,
        {
            const.ATTR_NAME: "Back Patio",
            const.ATTR_PLAYER_ID: 1,
            const.ATTR_MODEL: "HEOS Drive",
            const.ATTR_VERSION: "1.493.180",
            const.ATTR_IP_ADDRESS: "127.0.0.1",
            const.ATTR_NETWORK: const.NETWORK_TYPE_WIRED,
            const.ATTR_LINE_OUT: 1,
            const.ATTR_SERIAL: "B1A2C3K",
        },
    )


@pytest_asyncio.fixture(name="player_front_porch")
async def player_front_porch_fixture(heos: MockHeos) -> HeosPlayer:
    """Fixture for a player."""
    return HeosPlayer(
        heos,
        {
            const.ATTR_NAME: "Front Porch",
            const.ATTR_PLAYER_ID: 2,
            const.ATTR_MODEL: "HEOS Drive",
            const.ATTR_VERSION: "1.493.180",
            const.ATTR_IP_ADDRESS: "127.0.0.2",
            const.ATTR_NETWORK: const.NETWORK_TYPE_WIFI,
            const.ATTR_LINE_OUT: 1,
        },
    )


@pytest_asyncio.fixture(name="group")
async def group_fixture(
    heos: MockHeos, player_back_patio: HeosPlayer, player_front_porch: HeosPlayer
) -> HeosGroup:
    return HeosGroup(
        heos,
        "Back Patio + Front Porch",
        1,
        player_back_patio,
        [player_back_patio, player_front_porch],
    )
