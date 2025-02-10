"""Test fixtures for pyheos."""

import dataclasses
from collections.abc import AsyncGenerator, Callable, Coroutine
from typing import Any

import pytest
import pytest_asyncio
from syrupy.assertion import SnapshotAssertion

from pyheos.group import HeosGroup
from pyheos.heos import Heos
from pyheos.media import MediaItem, MediaMusicSource
from pyheos.options import HeosOptions
from pyheos.player import HeosPlayer
from pyheos.types import LineOutLevelType, NetworkType
from tests.common import MediaItems, MediaMusicSources
from tests.syrupy import HeosSnapshotExtension

from . import MockHeos, MockHeosDevice


@pytest.fixture
def snapshot(snapshot: SnapshotAssertion) -> SnapshotAssertion:
    """Return snapshot assertion fixture with the Heos extension."""
    return snapshot.use_extension(HeosSnapshotExtension)


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
def handler() -> Callable[..., Any]:
    """Fixture handler to mock in the dispatcher."""

    def target(*args: Any, **kwargs: Any) -> None:
        target.fired = True  # type: ignore[attr-defined]
        target.args = args  # type: ignore[attr-defined]
        target.kwargs = kwargs  # type: ignore[attr-defined]

    target.fired = False  # type: ignore[attr-defined]
    return target


@pytest.fixture
def async_handler() -> Callable[..., Coroutine[Any, Any, None]]:
    """Fixture async handler to mock in the dispatcher."""

    async def target(*args: Any, **kwargs: Any) -> None:
        target.fired = True  # type: ignore[attr-defined]
        target.args = args  # type: ignore[attr-defined]
        target.kwargs = kwargs  # type: ignore[attr-defined]

    target.fired = False  # type: ignore[attr-defined]
    return target


@pytest.fixture
def media_music_source(heos: MockHeos) -> MediaMusicSource:
    return dataclasses.replace(MediaMusicSources.FAVORITES, heos=heos)


@pytest.fixture
def media_music_source_unavailable(heos: MockHeos) -> MediaMusicSource:
    return dataclasses.replace(MediaMusicSources.PANDORA, heos=heos)


@pytest.fixture
def media_music_source_tidal(heos: MockHeos) -> MediaMusicSource:
    return dataclasses.replace(MediaMusicSources.TIDAL, heos=heos)


@pytest.fixture
def media_item_album(heos: MockHeos) -> MediaItem:
    return dataclasses.replace(MediaItems.ALBUM, heos=heos)


@pytest.fixture
def media_item_song(heos: MockHeos) -> MediaItem:
    return dataclasses.replace(MediaItems.SONG, heos=heos)


@pytest.fixture(name="media_item_input")
def media_item_input_fixture(heos: MockHeos) -> MediaItem:
    return dataclasses.replace(MediaItems.INPUT, heos=heos)


@pytest.fixture
def media_item_station(heos: MockHeos) -> MediaItem:
    return dataclasses.replace(MediaItems.STATION, heos=heos)


@pytest.fixture
def media_item_playlist(heos: MockHeos) -> MediaItem:
    return dataclasses.replace(MediaItems.PLAYLIST, heos=heos)


@pytest.fixture
def media_item_device(heos: MockHeos) -> MediaItem:
    return dataclasses.replace(MediaItems.DEVICE, heos=heos)


@pytest_asyncio.fixture(name="player")
async def player_fixture(heos: MockHeos) -> HeosPlayer:
    """Fixture for a player."""
    return HeosPlayer(
        name="Back Patio",
        player_id=1,
        model="HEOS Drive",
        serial="B1A2C3K",
        version="3.34.240",
        supported_version=True,
        ip_address="127.0.0.1",
        network=NetworkType.WIRED,
        line_out=LineOutLevelType.FIXED,
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
        version="3.34.240",
        supported_version=True,
        ip_address="127.0.0.2",
        network=NetworkType.WIFI,
        line_out=LineOutLevelType.FIXED,
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
