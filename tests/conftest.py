"""Test fixtures for pyheos."""

from collections.abc import Callable, Coroutine

import pytest

from pyheos.heos import Heos

from . import MockHeosDevice


@pytest.fixture(name="mock_device")
def mock_device_fixture(event_loop):
    """Fixture for mocking a HEOS device connection."""
    device = MockHeosDevice()
    event_loop.run_until_complete(device.start())
    yield device
    event_loop.run_until_complete(device.stop())


@pytest.fixture(name="heos")
def heos_fixture(event_loop):
    """Fixture for a connected heos."""
    heos = Heos("127.0.0.1", timeout=1, heart_beat=None)
    event_loop.run_until_complete(heos.connect())
    yield heos
    event_loop.run_until_complete(heos.disconnect())


@pytest.fixture
def handler() -> Callable:
    """Fixture handler to mock in the dispatcher."""

    def target(*args, **kwargs):
        target.fired = True  # type: ignore[attr-defined]
        target.args = args  # type: ignore[attr-defined]
        target.kwargs = kwargs  # type: ignore[attr-defined]

    target.fired = False  # type: ignore[attr-defined]
    return target


@pytest.fixture
def async_handler() -> Callable[..., Coroutine]:
    """Fixture async handler to mock in the dispatcher."""

    async def target(*args, **kwargs) -> None:
        target.fired = True  # type: ignore[attr-defined]
        target.args = args  # type: ignore[attr-defined]
        target.kwargs = kwargs  # type: ignore[attr-defined]

    target.fired = False  # type: ignore[attr-defined]
    return target
