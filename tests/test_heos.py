"""Tests for the heos class."""
import asyncio

import pytest

from pyheos import const
from pyheos.dispatch import Dispatcher
from pyheos.heos import Heos

from . import get_fixture


def connect_handler(heos: Heos, signal: str, event: str) -> asyncio.Event:
    """Connect a handler to the specific signal and assert event."""
    trigger = asyncio.Event()

    async def handler(target_event: str, *args):
        assert target_event == event
        trigger.set()
    heos.dispatcher.connect(signal, handler)
    return trigger


def test_init():
    """Test init sets properties."""
    heos = Heos('127.0.0.1')
    assert isinstance(heos.dispatcher, Dispatcher)


@pytest.mark.asyncio
async def test_connect(mock_device):
    """Test connect updates state and fires signal."""
    heos = Heos('127.0.0.1')
    signal = connect_handler(heos, const.SIGNAL_HEOS_EVENT,
                             const.EVENT_CONNECTED)
    await heos.connect()
    await signal.wait()
    # Assert 1st connection is used for commands
    assert heos.connection_state == const.STATE_CONNECTED
    assert len(mock_device.connections) == 1
    connection = mock_device.connections[0]
    assert connection.is_registered_for_events

    await heos.disconnect()


@pytest.mark.asyncio
async def test_heart_beat(mock_device):
    """Test heart beat fires at interval."""
    heos = Heos('127.0.0.1', heart_beat=0.5)
    await heos.connect()
    await asyncio.sleep(1.0)

    connection = mock_device.connections[0]
    assert len(connection.commands[const.COMMAND_HEART_BEAT]) == 1

    await heos.disconnect()


@pytest.mark.asyncio
async def test_connect_fails():
    """Test connect fails when host not available."""
    heos = Heos('127.0.0.1')
    with pytest.raises(ConnectionRefusedError):
        await heos.connect()
    # Also fails for initial connection even with reconnect.
    with pytest.raises(ConnectionRefusedError):
        await heos.connect(auto_reconnect=True)


@pytest.mark.asyncio
async def test_connect_timeout():
    """Test connect fails when host not available."""
    heos = Heos('www.google.com', timeout=1)
    with pytest.raises(asyncio.TimeoutError):
        await heos.connect()
    # Also fails for initial connection even with reconnect.
    with pytest.raises(asyncio.TimeoutError):
        await heos.connect(auto_reconnect=True)


@pytest.mark.asyncio
async def test_disconnect(mock_device, heos):
    """Test disconnect updates state and fires signal."""
    # Fixture automatically connects
    signal = connect_handler(heos, const.SIGNAL_HEOS_EVENT,
                             const.EVENT_DISCONNECTED)
    await heos.disconnect()
    await signal.wait()
    assert heos.connection_state == const.STATE_DISCONNECTED


@pytest.mark.asyncio
async def test_connection_error_during_event(mock_device, heos):
    """Test connection error during event results in disconnected."""
    disconnect_signal = connect_handler(
        heos, const.SIGNAL_HEOS_EVENT, const.EVENT_DISCONNECTED)

    # Assert transitions to reconnecting and fires disconnect
    await mock_device.stop()
    await disconnect_signal.wait()
    assert heos.connection_state == const.STATE_DISCONNECTED


@pytest.mark.asyncio
async def test_connection_error_during_command(mock_device, heos):
    """Test connection error during command results in disconnected."""
    disconnect_signal = connect_handler(
        heos, const.SIGNAL_HEOS_EVENT, const.EVENT_DISCONNECTED)

    # Assert transitions to reconnecting and fires disconnect
    await mock_device.stop()
    with pytest.raises(asyncio.TimeoutError):
        await heos.get_players()

    await disconnect_signal.wait()
    assert heos.connection_state == const.STATE_DISCONNECTED


@pytest.mark.asyncio
async def test_reconnect_during_event(mock_device):
    """Test reconnect while waiting for events/responses."""
    heos = Heos('127.0.0.1', timeout=0.1)

    connect_signal = connect_handler(
        heos, const.SIGNAL_HEOS_EVENT, const.EVENT_CONNECTED)
    disconnect_signal = connect_handler(
        heos, const.SIGNAL_HEOS_EVENT, const.EVENT_DISCONNECTED)

    # Assert open and fires connected
    await heos.connect(auto_reconnect=True, reconnect_delay=0)
    await connect_signal.wait()
    assert heos.connection_state == const.STATE_CONNECTED
    connect_signal.clear()

    # Assert transitions to reconnecting and fires disconnect
    await mock_device.stop()
    await disconnect_signal.wait()
    assert heos.connection_state == const.STATE_RECONNECTING

    # Assert reconnects once server is back up and fires connected
    await asyncio.sleep(0.5)  # Force reconnect timeout
    await mock_device.start()
    await connect_signal.wait()
    assert heos.connection_state == const.STATE_CONNECTED

    await heos.disconnect()


@pytest.mark.asyncio
async def test_reconnect_during_command(mock_device):
    """Test reconnect while waiting for events/responses."""
    heos = Heos('127.0.0.1', timeout=1.0)

    connect_signal = connect_handler(
        heos, const.SIGNAL_HEOS_EVENT, const.EVENT_CONNECTED)
    disconnect_signal = connect_handler(
        heos, const.SIGNAL_HEOS_EVENT, const.EVENT_DISCONNECTED)

    # Assert open and fires connected
    await heos.connect(auto_reconnect=True)
    await connect_signal.wait()
    assert heos.connection_state == const.STATE_CONNECTED
    connect_signal.clear()

    # Act
    await mock_device.stop()
    await mock_device.start()
    players = await heos.get_players()

    # Assert signals set
    await disconnect_signal.wait()
    await connect_signal.wait()
    assert heos.connection_state == const.STATE_CONNECTED
    assert len(players) == 2

    await heos.disconnect()


@pytest.mark.asyncio
async def test_reconnect_cancelled(mock_device):
    """Test reconnect is canceled by calling disconnect."""
    heos = Heos('127.0.0.1')

    connect_signal = connect_handler(
        heos, const.SIGNAL_HEOS_EVENT, const.EVENT_CONNECTED)
    disconnect_signal = connect_handler(
        heos, const.SIGNAL_HEOS_EVENT, const.EVENT_DISCONNECTED)

    # Assert open and fires connected
    await heos.connect(auto_reconnect=True)
    await connect_signal.wait()
    assert heos.connection_state == const.STATE_CONNECTED
    connect_signal.clear()

    # Assert transitions to reconnecting and fires disconnect
    await mock_device.stop()
    await disconnect_signal.wait()
    assert heos.connection_state == const.STATE_RECONNECTING

    # Assert reconnects once server is back up and fires connected
    await heos.disconnect()
    assert heos.connection_state == const.STATE_DISCONNECTED


@pytest.mark.asyncio
async def test_get_players(mock_device, heos):
    """Test the get_players method load players."""
    await heos.get_players()
    # Assert players loaded
    assert len(heos.players) == 2
    player = heos.get_player(1)
    assert player.player_id == 1
    assert player.name == 'Back Patio'
    assert player.ip_address == '192.168.0.1'
    assert player.line_out == 1
    assert player.model == 'HEOS Drive'
    assert player.network == 'wired'
    assert player.state == const.PLAY_STATE_STOP
    assert player.version == '1.493.180'
    assert player.volume == 36
    assert not player.is_muted
    assert player.repeat == const.REPEAT_OFF
    assert not player.shuffle


@pytest.mark.asyncio
async def test_player_state_changed_event(mock_device, heos):
    """Test playing state updates when event is received."""
    # assert not playing
    await heos.get_players()
    player = heos.get_player(1)
    assert player.state == const.PLAY_STATE_STOP

    # Attach dispatch handler
    signal = asyncio.Event()

    async def handler(player_id: int, event: str):
        assert player_id == player.player_id
        assert event == const.EVENT_PLAYER_STATE_CHANGED
        signal.set()
    heos.dispatcher.connect(const.SIGNAL_PLAYER_EVENT, handler)

    # Write event through mock device
    event_to_raise = (await get_fixture("event.player_state_changed")) \
        .replace("{player_id}", str(player.player_id)) \
        .replace("{state}", const.PLAY_STATE_PLAY)
    await mock_device.write_event(event_to_raise)

    # Wait until the signal
    await signal.wait()
    # Assert state changed
    assert player.state == const.PLAY_STATE_PLAY
    assert heos.get_player(2).state == const.PLAY_STATE_STOP


@pytest.mark.asyncio
async def test_player_now_playing_changed_event(mock_device, heos):
    """Test now playing updates when event is received."""
    # assert current state
    await heos.get_players()
    player = heos.get_player(1)
    now_playing = player.now_playing_media
    assert now_playing.album == ''
    assert now_playing.type == 'song'
    assert now_playing.album_id == ''
    assert now_playing.artist == ''
    assert now_playing.image_url == ''
    assert now_playing.media_id == 'catalog/playlists/genres'
    assert now_playing.queue_id == 1
    assert now_playing.song_id == 13
    assert now_playing.song == 'Disney Hits'
    assert now_playing.station is None

    # Attach dispatch handler
    signal = asyncio.Event()

    async def handler(player_id: int, event: str):
        assert player_id == player.player_id
        assert event == const.EVENT_PLAYER_NOW_PLAYING_CHANGED
        signal.set()
    heos.dispatcher.connect(const.SIGNAL_PLAYER_EVENT, handler)

    # Write event through mock device
    mock_device.register(const.COMMAND_GET_NOW_PLAYING_MEDIA, None,
                         "player.get_now_playing_media_changed",
                         replace=True)
    event_to_raise = (await get_fixture("event.player_now_playing_changed")) \
        .replace("{player_id}", str(player.player_id))
    await mock_device.write_event(event_to_raise)

    # Wait until the signal is set
    await signal.wait()
    # Assert state changed
    assert now_playing.album == "I've Been Waiting (Single) (Explicit)"
    assert now_playing.type == 'station'
    assert now_playing.album_id == '1'
    assert now_playing.artist == 'Lil Peep & ILoveMakonnen'
    assert now_playing.image_url == 'http://media/url'
    assert now_playing.media_id == '2PxuY99Qty'
    assert now_playing.queue_id == 1
    assert now_playing.song_id == 1
    assert now_playing.song == "I've Been Waiting (feat. Fall Out Boy)"
    assert now_playing.station == "Today's Hits Radio"
    assert now_playing.current_position is None
    assert now_playing.current_position_updated is None
    assert now_playing.duration is None


@pytest.mark.asyncio
async def test_player_volume_changed_event(mock_device, heos):
    """Test volume state updates when event is received."""
    # assert not playing
    await heos.get_players()
    player = heos.get_player(1)
    assert player.volume == 36
    assert not player.is_muted

    # Attach dispatch handler
    signal = asyncio.Event()

    async def handler(player_id: int, event: str):
        assert player_id == player.player_id
        assert event == const.EVENT_PLAYER_VOLUME_CHANGED
        signal.set()
    heos.dispatcher.connect(const.SIGNAL_PLAYER_EVENT, handler)

    # Write event through mock device
    event_to_raise = (await get_fixture("event.player_volume_changed")) \
        .replace("{player_id}", str(player.player_id)) \
        .replace("{level}", '50') \
        .replace("{mute}", 'on')
    await mock_device.write_event(event_to_raise)

    # Wait until the signal is set
    await signal.wait()
    # Assert state changed
    assert player.volume == 50
    assert player.is_muted
    assert heos.get_player(2).volume == 36
    assert not heos.get_player(2).is_muted


@pytest.mark.asyncio
async def test_player_now_playing_progress_event(mock_device, heos):
    """Test now playing progress updates when event received."""
    # assert not playing
    await heos.get_players()
    player = heos.get_player(1)
    assert player.now_playing_media.duration is None
    assert player.now_playing_media.current_position is None
    assert player.now_playing_media.current_position_updated is None

    # Attach dispatch handler
    signal = asyncio.Event()

    async def handler(player_id: int, event: str):
        assert player_id == player.player_id
        assert event == const.EVENT_PLAYER_NOW_PLAYING_PROGRESS
        signal.set()
    heos.dispatcher.connect(const.SIGNAL_PLAYER_EVENT, handler)

    # Write event through mock device
    event_to_raise = (await get_fixture("event.player_now_playing_progress")) \
        .replace("{player_id}", str(player.player_id)) \
        .replace("{cur_pos}", '113000') \
        .replace("{duration}", '210000')
    await mock_device.write_event(event_to_raise)

    # Wait until the signal is set or timeout
    await signal.wait()
    # Assert state changed
    assert player.now_playing_media.duration == 210000
    assert player.now_playing_media.current_position == 113000
    assert player.now_playing_media.current_position_updated is not None
    player2 = heos.get_player(2)
    assert player2.now_playing_media.duration is None
    assert player2.now_playing_media.current_position is None
    assert player2.now_playing_media.current_position_updated is None


@pytest.mark.asyncio
async def test_limited_progress_event_updates(mock_device):
    """Test progress updates only once if no other events."""
    # assert not playing
    heos = Heos('127.0.0.1', all_progress_events=False)
    await heos.connect()
    await heos.get_players()
    player = heos.get_player(1)

    # Attach dispatch handler
    signal = asyncio.Event()

    async def handler(player_id: int, event: str):
        if not signal.is_set():
            signal.set()
        else:
            pytest.fail("Handler invoked more than once.")
    heos.dispatcher.connect(const.SIGNAL_PLAYER_EVENT, handler)

    # Write event through mock device
    event_to_raise = (await get_fixture("event.player_now_playing_progress")) \
        .replace("{player_id}", str(player.player_id)) \
        .replace("{cur_pos}", '113000') \
        .replace("{duration}", '210000')

    # raise it multiple times.
    await mock_device.write_event(event_to_raise)
    await mock_device.write_event(event_to_raise)
    await mock_device.write_event(event_to_raise)
    await signal.wait()


@pytest.mark.asyncio
async def test_repeat_mode_changed_event(mock_device, heos):
    """Test repeat mode changes when event received."""
    # assert not playing
    await heos.get_players()
    player = heos.get_player(1)
    assert player.repeat == const.REPEAT_OFF

    # Attach dispatch handler
    signal = asyncio.Event()

    async def handler(player_id: int, event: str):
        assert player_id == player.player_id
        assert event == const.EVENT_REPEAT_MODE_CHANGED
        signal.set()
    heos.dispatcher.connect(const.SIGNAL_PLAYER_EVENT, handler)

    # Write event through mock device
    event_to_raise = await get_fixture("event.repeat_mode_changed")
    await mock_device.write_event(event_to_raise)

    # Wait until the signal is set
    await signal.wait()
    # Assert state changed
    assert player.repeat == const.REPEAT_ON_ALL


@pytest.mark.asyncio
async def test_shuffle_mode_changed_event(mock_device, heos):
    """Test shuffle mode changes when event received."""
    # assert not playing
    await heos.get_players()
    player = heos.get_player(1)
    assert not player.shuffle

    # Attach dispatch handler
    signal = asyncio.Event()

    async def handler(player_id: int, event: str):
        assert player_id == player.player_id
        assert event == const.EVENT_SHUFFLE_MODE_CHANGED
        signal.set()
    heos.dispatcher.connect(const.SIGNAL_PLAYER_EVENT, handler)

    # Write event through mock device
    event_to_raise = await get_fixture("event.shuffle_mode_changed")
    await mock_device.write_event(event_to_raise)

    # Wait until the signal is set
    await signal.wait()
    # Assert state changed
    assert player.shuffle


@pytest.mark.asyncio
async def test_players_changed_event(mock_device, heos):
    """Test players are resynced when event received."""
    # assert not playing
    old_players = (await heos.get_players()).copy()

    # Attach dispatch handler
    signal = asyncio.Event()

    async def handler(event: str):
        assert event == const.EVENT_PLAYERS_CHANGED
        signal.set()
    heos.dispatcher.connect(const.SIGNAL_CONTROLLER_EVENT, handler)

    # Write event through mock device
    mock_device.register(const.COMMAND_GET_PLAYERS, None,
                         'player.get_players_changed', replace=True)
    event_to_raise = await get_fixture("event.players_changed")
    await mock_device.write_event(event_to_raise)

    # Wait until the signal is set
    await signal.wait()
    assert len(heos.players) == 2
    # Assert 2 (Front Porch) was removed
    assert old_players[2].removed
    assert 2 not in heos.players
    # Assert 3 (Basement) was added
    assert heos.get_player(3) is not None
    # Assert 1 (Bachyard) was updated
    assert heos.get_player(1).name == 'Backyard'


@pytest.mark.asyncio
async def test_sources_changed_event(mock_device, heos):
    """Test sources changed fires dispatcher."""
    mock_device.register(const.COMMAND_BROWSE_GET_SOURCES, None,
                         'browse.get_music_sources')
    await heos.get_music_sources()
    signal = asyncio.Event()

    async def handler(event: str):
        assert event == const.EVENT_SOURCES_CHANGED
        signal.set()
    heos.dispatcher.connect(const.SIGNAL_CONTROLLER_EVENT, handler)

    # Write event through mock device
    mock_device.register(const.COMMAND_BROWSE_GET_SOURCES, None,
                         'browse.get_music_sources_changed', replace=True)
    event_to_raise = await get_fixture("event.sources_changed")
    await mock_device.write_event(event_to_raise)

    # Wait until the signal is set
    await signal.wait()
    assert heos.music_sources[const.MUSIC_SOURCE_TUNEIN].available


@pytest.mark.asyncio
async def test_groups_changed_event(mock_device, heos):
    """Test groups changed fires dispatcher."""
    signal = asyncio.Event()

    async def handler(event: str):
        assert event == const.EVENT_GROUPS_CHANGED
        signal.set()
    heos.dispatcher.connect(const.SIGNAL_CONTROLLER_EVENT, handler)

    # Write event through mock device
    event_to_raise = await get_fixture("event.groups_changed")
    await mock_device.write_event(event_to_raise)

    # Wait until the signal is set
    await signal.wait()


@pytest.mark.asyncio
async def test_player_playback_error_event(mock_device, heos):
    """Test player playback error fires dispatcher."""
    await heos.get_players()
    signal = asyncio.Event()

    async def handler(player_id: int, event: str):
        assert player_id == 1
        assert event == const.EVENT_PLAYER_PLAYBACK_ERROR
        signal.set()
    heos.dispatcher.connect(const.SIGNAL_PLAYER_EVENT, handler)

    # Write event through mock device
    event_to_raise = await get_fixture("event.player_playback_error")
    await mock_device.write_event(event_to_raise)

    # Wait until the signal is set
    await signal.wait()
    assert heos.players[1].playback_error == 'Could Not Download'


@pytest.mark.asyncio
async def test_player_queue_changed_event(mock_device, heos):
    """Test player queue changed fires dispatcher."""
    await heos.get_players()
    signal = asyncio.Event()

    async def handler(player_id: int, event: str):
        assert player_id == 1
        assert event == const.EVENT_PLAYER_QUEUE_CHANGED
        signal.set()
    heos.dispatcher.connect(const.SIGNAL_PLAYER_EVENT, handler)

    # Write event through mock device
    event_to_raise = await get_fixture("event.player_queue_changed")
    await mock_device.write_event(event_to_raise)

    # Wait until the signal is set
    await signal.wait()


@pytest.mark.asyncio
async def test_group_volume_changed_event(mock_device, heos):
    """Test group volume changed fires dispatcher."""
    signal = asyncio.Event()

    async def handler(group_id: int, event: str):
        assert group_id == 1
        assert event == const.EVENT_GROUP_VOLUME_CHANGED
        signal.set()
    heos.dispatcher.connect(const.SIGNAL_GROUP_EVENT, handler)

    # Write event through mock device
    event_to_raise = await get_fixture("event.group_volume_changed")
    await mock_device.write_event(event_to_raise)

    # Wait until the signal is set
    await signal.wait()


@pytest.mark.asyncio
async def test_user_changed_event(mock_device, heos):
    """Test user changed fires dispatcher."""
    signal = asyncio.Event()

    async def handler(event: str):
        assert event == const.EVENT_USER_CHANGED
        signal.set()
    heos.dispatcher.connect(const.SIGNAL_CONTROLLER_EVENT, handler)

    # Write event through mock device
    event_to_raise = await get_fixture("event.user_changed")
    await mock_device.write_event(event_to_raise)

    # Wait until the signal is set
    await signal.wait()


@pytest.mark.asyncio
async def test_get_music_sources(mock_device, heos):
    """Test the heos connect method."""
    mock_device.register(const.COMMAND_BROWSE_GET_SOURCES, None,
                         'browse.get_music_sources')

    sources = await heos.get_music_sources()
    assert len(sources) == 15
    pandora = sources[const.MUSIC_SOURCE_PANDORA]
    assert pandora.source_id == 1
    assert pandora.image_url == 'https://production.ws.skyegloup.com:443/' \
                                'media/images/service/logos/pandora.png'
    assert pandora.type == const.TYPE_MUSIC_SERVICE
    assert pandora.available
    assert pandora.service_username == 'test@test.com'
    assert not pandora.container
    assert not pandora.playable


@pytest.mark.asyncio
async def test_get_input_sources(mock_device, heos):
    """Test the get input sources method."""
    mock_device.register(const.COMMAND_BROWSE_BROWSE, {'sid': '1027'},
                         'browse.browse_aux_input')
    mock_device.register(const.COMMAND_BROWSE_BROWSE, {'sid': '546978854'},
                         'browse.browse_theater_receiver')
    mock_device.register(const.COMMAND_BROWSE_BROWSE, {'sid': '-263109739'},
                         'browse.browse_heos_drive')

    sources = await heos.get_input_sources()
    assert len(sources) == 18
    source = sources[0]
    assert source.name == 'Theater Receiver - CBL/SAT'
    assert source.input_name == const.INPUT_CABLE_SAT
    assert source.player_id == 546978854


@pytest.mark.asyncio
async def test_get_favorites(mock_device, heos):
    """Test the get favorites method."""
    mock_device.register(const.COMMAND_BROWSE_BROWSE, {'sid': '1028'},
                         'browse.browse_favorites')

    sources = await heos.get_favorites()
    assert len(sources) == 3
    assert sorted(sources.keys()) == [1, 2, 3]
    fav = sources[1]
    assert fav.playable
    assert fav.name == 'Thumbprint Radio'
    assert fav.type == const.TYPE_STATION
