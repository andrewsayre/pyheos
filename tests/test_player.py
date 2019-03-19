"""Tests for the player module."""
import pytest

from pyheos import const
from pyheos.player import HeosPlayer

from . import get_fixture


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

    with pytest.raises(ValueError):
        await player.set_state("invalid")


@pytest.mark.asyncio
async def test_set_volume_and_mute(mock_device, heos):
    """Test the volume commands."""
    player = heos.get_player(1)

    volume_response = await get_fixture('player.set_volume')

    def _volume_callback(command, args):
        assert command == 'player/set_volume'
        return volume_response.replace("{player_id}", str(player.player_id)) \
            .replace("{level}", args['level'])

    mock_device.register_one_time("player/set_volume", _volume_callback)
    with pytest.raises(ValueError):
        await player.set_volume(-1)
    with pytest.raises(ValueError):
        await player.set_volume(101)
    assert await player.set_volume(100)

    mute_response = await get_fixture('player.set_mute')

    def _mute_callback(command, args):
        assert command == 'player/set_mute'
        return mute_response.replace("{player_id}", str(player.player_id)) \
            .replace("{state}", args['state'])

    mock_device.register_one_time("player/set_mute", _mute_callback)
    assert await player.mute()

    mock_device.register_one_time("player/set_mute", _mute_callback)
    assert await player.unmute()

    mock_device.register_one_time("player/volume_up", 'player.volume_up')
    assert await player.volume_up(6)
    with pytest.raises(ValueError):
        await player.volume_up(0)
    with pytest.raises(ValueError):
        await player.volume_up(11)

    mock_device.register_one_time("player/volume_down", 'player.volume_down')
    assert await player.volume_down(6)
    with pytest.raises(ValueError):
        await player.volume_down(0)
    with pytest.raises(ValueError):
        await player.volume_down(11)

    mock_device.register_one_time("player/toggle_mute", 'player.toggle_mute')
    assert await player.toggle_mute()


@pytest.mark.asyncio
async def test_set_play_mode(mock_device, heos):
    """Test the volume commands."""
    player = heos.get_player(1)
    args = {
        'repeat': const.REPEAT_ON_ALL,
        'shuffle': 'on'
    }
    mock_device.register_command(
        'player.set_play_mode', player.player_id, args)
    assert await player.set_play_mode(const.REPEAT_ON_ALL, True)

    # Assert invalid mode
    with pytest.raises(ValueError):
        await player.set_play_mode("repeat", True)


@pytest.mark.asyncio
async def test_play_next_previous(mock_device, heos):
    """Test the volume commands."""
    player = heos.get_player(1)

    mock_device.register_command('player.play_next', player.player_id)
    assert await player.play_next()

    mock_device.register_command('player.play_previous', player.player_id)
    assert await player.play_previous()


@pytest.mark.asyncio
async def test_clear_queue(mock_device, heos):
    """Test the volume commands."""
    player = heos.get_player(1)

    mock_device.register_command('player.clear_queue', player.player_id)
    assert await player.clear_queue()
