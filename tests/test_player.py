"""Tests for the player module."""
import pytest

from pyheos import const
from pyheos.heos import Heos
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
    player = HeosPlayer(Heos('None'), data)
    assert str(player) == '{Back Patio (HEOS Drive)}'
    assert repr(player) == '{Back Patio (HEOS Drive) with id 1 at 192.168.0.1}'


@pytest.mark.asyncio
async def test_set_state(mock_device, heos):
    """Test the play, pause, and stop commands."""
    await heos.get_players()
    player = heos.players.get(1)
    # Invalid
    with pytest.raises(ValueError):
        await player.set_state("invalid")
    # Play
    mock_device.register(const.COMMAND_SET_PLAY_STATE,
                         {"pid": "1", "state": "play"},
                         'player.set_play_state')
    await player.play()
    # Pause
    mock_device.register(const.COMMAND_SET_PLAY_STATE,
                         {"pid": "1", "state": "pause"},
                         'player.set_play_state', replace=True)
    await player.pause()
    # Stop
    mock_device.register(const.COMMAND_SET_PLAY_STATE,
                         {"pid": "1", "state": "stop"},
                         'player.set_play_state', replace=True)
    await player.stop()


@pytest.mark.asyncio
async def test_set_volume(mock_device, heos):
    """Test the set_volume command."""
    await heos.get_players()
    player = heos.players.get(1)

    with pytest.raises(ValueError):
        await player.set_volume(-1)
    with pytest.raises(ValueError):
        await player.set_volume(101)

    mock_device.register(const.COMMAND_SET_VOLUME,
                         {"pid": "1", "level": "100"},
                         'player.set_volume')
    await player.set_volume(100)


@pytest.mark.asyncio
async def test_set_mute(mock_device, heos):
    """Test the set_mute command."""
    await heos.get_players()
    player = heos.players.get(1)
    # Mute
    mock_device.register(const.COMMAND_SET_MUTE,
                         {"pid": "1", "state": "on"},
                         'player.set_mute')
    await player.mute()
    # Unmute
    mock_device.register(const.COMMAND_SET_MUTE,
                         {"pid": "1", "state": "off"},
                         'player.set_mute', replace=True)
    await player.unmute()


@pytest.mark.asyncio
async def test_toggle_mute(mock_device, heos):
    """Test the toggle_mute command."""
    await heos.get_players()
    player = heos.players.get(1)
    mock_device.register(
        const.COMMAND_TOGGLE_MUTE, {"pid": "1"}, 'player.toggle_mute')
    await player.toggle_mute()


@pytest.mark.asyncio
async def test_volume_up(mock_device, heos):
    """Test the volume_up command."""
    await heos.get_players()
    player = heos.players.get(1)
    with pytest.raises(ValueError):
        await player.volume_up(0)
    with pytest.raises(ValueError):
        await player.volume_up(11)
    mock_device.register(
        const.COMMAND_VOLUME_UP, {"pid": "1", "step": "6"}, 'player.volume_up')
    await player.volume_up(6)


@pytest.mark.asyncio
async def test_volume_down(mock_device, heos):
    """Test the volume_down command."""
    await heos.get_players()
    player = heos.players.get(1)
    with pytest.raises(ValueError):
        await player.volume_down(0)
    with pytest.raises(ValueError):
        await player.volume_down(11)
    mock_device.register(
        const.COMMAND_VOLUME_DOWN, {"pid": "1", "step": "6"},
        'player.volume_down')
    await player.volume_down(6)


@pytest.mark.asyncio
async def test_set_play_mode(mock_device, heos):
    """Test the volume commands."""
    await heos.get_players()
    player = heos.players.get(1)
    args = {
        'pid': '1',
        'repeat': const.REPEAT_ON_ALL,
        'shuffle': 'on'
    }
    mock_device.register(const.COMMAND_SET_PLAY_MODE, args,
                         'player.set_play_mode')

    await player.set_play_mode(const.REPEAT_ON_ALL, True)
    # Assert invalid mode
    with pytest.raises(ValueError):
        await player.set_play_mode("repeat", True)


@pytest.mark.asyncio
async def test_play_next_previous(mock_device, heos):
    """Test the volume commands."""
    await heos.get_players()
    player = heos.players.get(1)
    args = {'pid': '1'}
    # Next
    mock_device.register(const.COMMAND_PLAY_NEXT, args, 'player.play_next')
    await player.play_next()
    # Previous
    mock_device.register(const.COMMAND_PLAY_PREVIOUS, args,
                         'player.play_previous')
    await player.play_previous()


@pytest.mark.asyncio
async def test_clear_queue(mock_device, heos):
    """Test the volume commands."""
    await heos.get_players()
    player = heos.players.get(1)
    args = {'pid': '1'}
    mock_device.register(const.COMMAND_CLEAR_QUEUE, args, 'player.clear_queue')
    await player.clear_queue()

    # Also test with a 'command under process' response
    mock_device.register(const.COMMAND_CLEAR_QUEUE, args,
                         ['player.clear_queue',
                          'player.clear_queue_processing'], replace=True)
    await player.clear_queue()


@pytest.mark.asyncio
async def test_play_input_source(mock_device, heos):
    """Test the play input source."""
    await heos.get_players()
    player = heos.players.get(1)

    # Test invalid input_name
    with pytest.raises(ValueError):
        await player.play_input("Invalid")

    input_source = InputSource(1, "AUX In 1", const.INPUT_AUX_IN_1)
    args = {'pid': '1', 'spid': str(input_source.player_id),
            'input': input_source.input_name}
    mock_device.register(const.COMMAND_BROWSE_PLAY_INPUT, args,
                         'browse.play_input')
    await player.play_input_source(input_source)


@pytest.mark.asyncio
async def test_play_favorite(mock_device, heos):
    """Test the play favorite."""
    await heos.get_players()
    player = heos.players.get(1)

    # Test invalid starting index
    with pytest.raises(ValueError):
        await player.play_favorite(0)

    args = {'pid': '1', 'preset': '1'}
    mock_device.register(const.COMMAND_BROWSE_PLAY_PRESET, args,
                         'browse.play_preset')

    await player.play_favorite(1)


@pytest.mark.asyncio
async def test_play_url(mock_device, heos):
    """Test the play favorite."""
    await heos.get_players()
    player = heos.players.get(1)
    url = "https://my.website.com/podcast.mp3"
    args = {'pid': '1', 'url': url}
    mock_device.register(const.COMMAND_BROWSE_PLAY_STREAM,
                         args, 'browse.play_stream')

    await player.play_url(url)
