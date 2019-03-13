"""Tests for the heos class."""
import asyncio

import pytest

from pyheos import const
from pyheos.dispatch import Dispatcher

from . import get_fixture


def test_init(heos):
    """Test init sets properties."""
    assert isinstance(heos.dispatcher, Dispatcher)
    assert not heos.players
    assert heos.get_player(1) is None


@pytest.mark.asyncio
async def test_connect_loads_players_and_subscribes(mock_device, heos):
    """Test the heos connect method."""
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


@pytest.mark.asyncio
async def test_player_state_updates_on_event(mock_device, connected_heos):
    """Test playing state updates when event is received."""
    # assert not playing
    player = connected_heos.get_player(1)
    assert player.state == const.PLAY_STATE_STOP

    # Attach dispatch handler
    signal = asyncio.Event()

    async def handler(player_id: int, event: str):
        assert player_id == player.player_id
        assert event == const.EVENT_PLAYER_STATE_CHANGED
        signal.set()
    connected_heos.dispatcher.connect(const.SIGNAL_PLAYER_UPDATED, handler)

    # Write event through mock device
    event_to_raise = get_fixture("event.player_state_changed") \
        .replace("{player_id}", str(player.player_id)) \
        .replace("{state}", const.PLAY_STATE_PLAY)
    await mock_device.write_event(event_to_raise)

    # Wait until the signal is set or timeout
    await asyncio.wait_for(signal.wait(), 1)
    # Assert state changed
    assert player.state == const.PLAY_STATE_PLAY
