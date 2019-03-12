"""Tests for the heos class."""
import pytest
from pyheos.heos import Heos
from pyheos.dispatch import Dispatcher


def test_init():
    """Test init sets properties."""
    heos = Heos('127.0.0.1')
    assert isinstance(heos.dispatcher, Dispatcher)
    assert len(heos.players) == 0
    assert heos.get_player(1) is None


@pytest.mark.asyncio
async def test_connect_loads_players_and_subscribes(mock_device):
    """Test the heos connect method."""
    heos = Heos('127.0.0.1')

    await heos.connect()

    # Assert 1st connection is used for commands
    assert len(mock_device.connections) == 2
    command_log = mock_device.connections[0]
    assert not command_log.is_registered_for_events

    # Assert 2nd connection is registered for events
    event_log = mock_device.connections[1]
    assert event_log.is_registered_for_events

    # Assert players loaded
    assert len(heos.players) == 2
    assert heos.get_player(1) is not None

    await heos.disconnect()
