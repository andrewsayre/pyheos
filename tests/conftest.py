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
def media_music_source(heos: MockHeos) -> MediaMusicSource:
    source = MediaMusicSources.FAVORITES.clone()
    source._heos = heos
    return source


@pytest.fixture
def media_music_source_unavailable(heos: MockHeos) -> MediaMusicSource:
    source = MediaMusicSources.PANDORA.clone()
    source._heos = heos
    return source


@pytest.fixture
def media_music_source_tidal(heos: MockHeos) -> MediaMusicSource:
    source = MediaMusicSources.TIDAL.clone()
    source._heos = heos
    return source


@pytest.fixture
def media_item_album(heos: MockHeos) -> MediaItem:
    source = MediaItems.ALBUM.clone()
    source._heos = heos
    return source


@pytest.fixture
def media_item_song(heos: MockHeos) -> MediaItem:
    source = MediaItems.SONG.clone()
    source._heos = heos
    return source


@pytest.fixture(name="media_item_input")
def media_item_input_fixture(heos: MockHeos) -> MediaItem:
    source = MediaItems.INPUT.clone()
    source._heos = heos
    return source


@pytest.fixture
def media_item_station(heos: MockHeos) -> MediaItem:
    source = MediaItems.STATION.clone()
    source._heos = heos
    return source


@pytest.fixture
def media_item_playlist(heos: MockHeos) -> MediaItem:
    source = MediaItems.PLAYLIST.clone()
    source._heos = heos
    return source


@pytest.fixture
def media_item_device(heos: MockHeos) -> MediaItem:
    source = MediaItems.DEVICE.clone()
    source._heos = heos
    return source


@pytest_asyncio.fixture(name="player")
async def player_fixture(heos: MockHeos) -> HeosPlayer:
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
async def group_fixture(heos: MockHeos) -> HeosGroup:
    return HeosGroup(
        name="Back Patio + Front Porch",
        group_id=1,
        lead_player_id=1,
        member_player_ids=[1, 2],
        _heos=heos,
    )
