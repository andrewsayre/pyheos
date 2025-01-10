"""Test fixtures for pyheos."""

from collections.abc import AsyncGenerator, Callable, Coroutine
from typing import Any

import pytest
import pytest_asyncio

from pyheos.group import HeosGroup
from pyheos.heos import Heos, HeosOptions
from pyheos.media import MediaItem, MediaMusicSource
from pyheos.player import HeosPlayer, NetworkType
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
    source.heos = heos
    return source


@pytest.fixture
def media_music_source_unavailable(heos: MockHeos) -> MediaMusicSource:
    source = MediaMusicSources.PANDORA.clone()
    source.heos = heos
    return source


@pytest.fixture
def media_music_source_tidal(heos: MockHeos) -> MediaMusicSource:
    source = MediaMusicSources.TIDAL.clone()
    source.heos = heos
    return source


@pytest.fixture
def media_item_album(heos: MockHeos) -> MediaItem:
    source = MediaItems.ALBUM.clone()
    source.heos = heos
    return source


@pytest.fixture
def media_item_song(heos: MockHeos) -> MediaItem:
    source = MediaItems.SONG.clone()
    source.heos = heos
    return source


@pytest.fixture(name="media_item_input")
def media_item_input_fixture(heos: MockHeos) -> MediaItem:
    source = MediaItems.INPUT.clone()
    source.heos = heos
    return source


@pytest.fixture
def media_item_station(heos: MockHeos) -> MediaItem:
    source = MediaItems.STATION.clone()
    source.heos = heos
    return source


@pytest.fixture
def media_item_playlist(heos: MockHeos) -> MediaItem:
    source = MediaItems.PLAYLIST.clone()
    source.heos = heos
    return source


@pytest.fixture
def media_item_device(heos: MockHeos) -> MediaItem:
    source = MediaItems.DEVICE.clone()
    source.heos = heos
    return source


@pytest_asyncio.fixture(name="player")
async def player_fixture(heos: MockHeos) -> HeosPlayer:
    """Fixture for a player."""
    return HeosPlayer(
        name="Back Patio",
        player_id=1,
        model="HEOS Drive",
        serial="B1A2C3K",
        version="1.493.180",
        ip_address="127.0.0.1",
        network=NetworkType.WIRED,
        line_out=1,
        heos=heos,
    )


@pytest_asyncio.fixture(name="player_front_porch")
async def player_front_porch_fixture(heos: MockHeos) -> HeosPlayer:
    """Fixture for a player."""
    return HeosPlayer(
        name="Front Porch",
        player_id=2,
        model="HEOS Drive",
        serial=None,
        version="1.493.180",
        ip_address="127.0.0.2",
        network=NetworkType.WIFI,
        line_out=1,
        heos=heos,
    )


@pytest_asyncio.fixture(name="group")
async def group_fixture(heos: MockHeos) -> HeosGroup:
    return HeosGroup(
        name="Back Patio + Front Porch",
        group_id=1,
        lead_player_id=1,
        member_player_ids=[2],
        heos=heos,
    )
