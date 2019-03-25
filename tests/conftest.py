"""Test fixtures for pyheos."""
import pytest

from pyheos.heos import Heos

from . import MockHeosDevice


def pytest_collection_modifyitems(items):
    """Modify collected tests to add timeout."""
    for item in items:
        if item.get_closest_marker('timeout') is None:
            item.add_marker(pytest.mark.timeout(10))


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
    heos = Heos('127.0.0.1', timeout=0.5, heart_beat=None)
    event_loop.run_until_complete(heos.connect())
    yield heos
    event_loop.run_until_complete(heos.disconnect())


@pytest.fixture
def handler():
    """Fixture handler to mock in the dispatcher."""
    def target(*args, **kwargs):
        target.fired = True
        target.args = args
        target.kwargs = kwargs
    target.fired = False
    return target


@pytest.fixture
def async_handler():
    """Fixture async handler to mock in the dispatcher."""
    async def target(*args, **kwargs):
        target.fired = True
        target.args = args
        target.kwargs = kwargs
    target.fired = False
    return target
