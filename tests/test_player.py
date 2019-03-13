"""Tests for the player module."""
import pytest

from pyheos.player import HeosPlayer

from . import get_fixture


@pytest.mark.asyncio
async def test_set_state(mock_device, heos):
    """Test the play, pause, and stop commands."""
    player = heos.get_player(1)

    response = await get_fixture('player.set_play_state')

    def _response_callback(command, args):
        assert command == 'player/set_play_state'
        return response.replace("{player_id}", str(player.player_id)) \
            .replace("{state}", args['state'])

    mock_device.register_one_time("player/set_play_state", _response_callback)
    assert await player.play()

    mock_device.register_one_time("player/set_play_state", _response_callback)
    assert await player.pause()

    mock_device.register_one_time("player/set_play_state", _response_callback)
    assert await player.stop()


def test_str():
    """Test the __str__ function."""
    data = {
        "name": "Back Patio",
        "pid": 1,
        "model": "HEOS Drive",
        "version": "1.493.180",
        "ip": "192.168.0.1",
        "network": "wired",
        "lineout": 1
    }
    player = HeosPlayer(None, data)
    assert str(player) == '{Back Patio (HEOS Drive)}'
    assert repr(player) == '{Back Patio (HEOS Drive) with id 1 at 192.168.0.1}'
