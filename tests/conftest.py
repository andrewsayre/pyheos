"""Test fixtures for pyheos."""

from collections.abc import AsyncGenerator, Callable, Coroutine
from typing import Any

import pytest
import pytest_asyncio

from pyheos.heos import Heos

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
    heos = Heos("127.0.0.1", timeout=1, heart_beat=None)
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
