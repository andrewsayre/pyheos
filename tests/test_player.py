"""Tests for the player module."""
import pytest

from pyheos import const
from pyheos.player import HeosPlayer
from pyheos.source import InputSource


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
    await heos.get_players()
    player = heos.get_player(1)

    mock_device.register(const.COMMAND_SET_PLAY_STATE, None,
                         'player.set_play_state')

    assert await player.play()
    assert await player.pause()
    assert await player.stop()

    with pytest.raises(ValueError):
        await player.set_state("invalid")


@pytest.mark.asyncio
async def test_set_volume_and_mute(mock_device, heos):
    """Test the volume commands."""
    await heos.get_players()
    player = heos.get_player(1)

    mock_device.register(const.COMMAND_SET_VOLUME, None, 'player.set_volume')
    mock_device.register(const.COMMAND_SET_MUTE, None, 'player.set_mute')
    mock_device.register(const.COMMAND_VOLUME_UP, None, 'player.volume_up')
    mock_device.register(const.COMMAND_VOLUME_DOWN, None, 'player.volume_down')
    mock_device.register(const.COMMAND_TOGGLE_MUTE, None, 'player.toggle_mute')

    # Volume
    with pytest.raises(ValueError):
        await player.set_volume(-1)
    with pytest.raises(ValueError):
        await player.set_volume(101)
    assert await player.set_volume(100)

    # Mute
    assert await player.mute()
    assert await player.unmute()
    assert await player.toggle_mute()

    # Up
    assert await player.volume_up(6)
    with pytest.raises(ValueError):
        await player.volume_up(0)
    with pytest.raises(ValueError):
        await player.volume_up(11)

    # Down
    assert await player.volume_down(6)
    with pytest.raises(ValueError):
        await player.volume_down(0)
    with pytest.raises(ValueError):
        await player.volume_down(11)


@pytest.mark.asyncio
async def test_set_play_mode(mock_device, heos):
    """Test the volume commands."""
    await heos.get_players()
    player = heos.get_player(1)
    args = {
        'pid': '1',
        'repeat': const.REPEAT_ON_ALL,
        'shuffle': 'on'
    }
    mock_device.register(const.COMMAND_SET_PLAY_MODE, args,
                         'player.set_play_mode')

    assert await player.set_play_mode(const.REPEAT_ON_ALL, True)
    # Assert invalid mode
    with pytest.raises(ValueError):
        await player.set_play_mode("repeat", True)


@pytest.mark.asyncio
async def test_play_next_previous(mock_device, heos):
    """Test the volume commands."""
    await heos.get_players()
    player = heos.get_player(1)
    args = {'pid': '1'}
    mock_device.register(const.COMMAND_PLAY_NEXT, args, 'player.play_next')
    mock_device.register(const.COMMAND_PLAY_PREVIOUS, args,
                         'player.play_previous')

    assert await player.play_next()
    assert await player.play_previous()


@pytest.mark.asyncio
async def test_clear_queue(mock_device, heos):
    """Test the volume commands."""
    await heos.get_players()
    player = heos.get_player(1)
    args = {'pid': '1'}
    mock_device.register(const.COMMAND_CLEAR_QUEUE, args, 'player.clear_queue')

    assert await player.clear_queue()

    # Also test with a 'command under process' response
    mock_device.register(const.COMMAND_CLEAR_QUEUE, args,
                         ['player.clear_queue',
                          'player.clear_queue_processing'], replace=True)

    assert await player.clear_queue()


@pytest.mark.asyncio
async def test_play_input_source(mock_device, heos):
    """Test the play input source."""
    await heos.get_players()
    player = heos.get_player(1)
    input_source = InputSource(1, "AUX In 1", const.INPUT_AUX_IN_1)
    args = {'pid': '1', 'spid': str(input_source.player_id),
            'input': input_source.input_name}
    mock_device.register(const.COMMAND_BROWSE_PLAY_INPUT, args,
                         'browse.play_input')

    assert await player.play_input_source(input_source)

    # Test invalid input_name
    with pytest.raises(ValueError):
        await player.play_input("Invalid")


@pytest.mark.asyncio
async def test_play_favorite(mock_device, heos):
    """Test the play favorite."""
    await heos.get_players()
    player = heos.get_player(1)
    args = {'pid': '1', 'preset': '1'}
    mock_device.register(const.COMMAND_BROWSE_PLAY_PRESET, args,
                         'browse.play_preset')

    assert await player.play_favorite(1)

    # Test invalid starting index
    with pytest.raises(ValueError):
        await player.play_favorite(0)


@pytest.mark.asyncio
async def test_play_url(mock_device, heos):
    """Test the play favorite."""
    await heos.get_players()
    player = heos.get_player(1)
    url = "https://my.website.com/podcast.mp3"
    args = {'pid': '1', 'url': url}
    mock_device.register(const.COMMAND_BROWSE_PLAY_STREAM,
                         args, 'browse.play_stream')

    assert await player.play_url(url)
