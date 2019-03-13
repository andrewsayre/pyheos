"""Test fixtures for pyheos."""
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
    heos = Heos('127.0.0.1')
    event_loop.run_until_complete(heos.connect())
    yield heos
    event_loop.run_until_complete(heos.disconnect())
