"""Tests for the heos class."""

import asyncio
from typing import Any

import pytest

from pyheos import const
from pyheos.credentials import Credentials
from pyheos.dispatch import Dispatcher
from pyheos.error import CommandError, CommandFailedError, HeosError
from pyheos.heos import Heos, HeosOptions

from . import MockHeosDevice, connect_handler, get_fixture


@pytest.mark.asyncio
async def test_init() -> None:
    """Test init sets properties."""
    heos = Heos(HeosOptions("127.0.0.1"))
    assert isinstance(heos.dispatcher, Dispatcher)
    assert len(heos.players) == 0
    assert len(heos.music_sources) == 0
    assert heos.connection_state == const.STATE_DISCONNECTED


@pytest.mark.asyncio
async def test_validate_connection(mock_device: MockHeosDevice) -> None:
    """Test get_system_info method returns system info."""
    system_info = await Heos.validate_connection("127.0.0.1")

    assert system_info.signed_in_username == "example@example.com"
    assert system_info.is_signed_in
    assert system_info.host.ip_address == "127.0.0.1"
    assert system_info.connected_to_preferred_host is True
    assert [system_info.host] == system_info.preferred_hosts

    assert system_info.hosts[0].ip_address == "127.0.0.1"
    assert system_info.hosts[0].model == "HEOS Drive"
    assert system_info.hosts[0].name == "Back Patio"
    assert system_info.hosts[0].network == const.NETWORK_TYPE_WIRED
    assert system_info.hosts[0].serial == "B1A2C3K"
    assert system_info.hosts[0].version == "1.493.180"

    assert system_info.hosts[1].ip_address == "127.0.0.2"
    assert system_info.hosts[1].model == "HEOS Drive"
    assert system_info.hosts[1].name == "Front Porch"
    assert system_info.hosts[1].network == const.NETWORK_TYPE_WIFI
    assert system_info.hosts[1].serial is None
    assert system_info.hosts[1].version == "1.493.180"


@pytest.mark.asyncio
async def test_connect(mock_device: MockHeosDevice) -> None:
    """Test connect updates state and fires signal."""
    heos = Heos(HeosOptions("127.0.0.1", timeout=0.1, auto_reconnect_delay=0.1))
    signal = connect_handler(heos, const.SIGNAL_HEOS_EVENT, const.EVENT_CONNECTED)
    await heos.connect()
    await signal.wait()
    # Assert 1st connection is used for commands
    assert heos.connection_state == const.STATE_CONNECTED
    assert len(mock_device.connections) == 1
    connection = mock_device.connections[0]
    assert connection.is_registered_for_events
    assert heos.is_signed_in
    assert heos.signed_in_username == "example@example.com"
    await heos.disconnect()


@pytest.mark.asyncio
async def test_connect_not_logged_in(mock_device: MockHeosDevice) -> None:
    """Test signed-in status shows correctly when logged out."""
    mock_device.register(
        const.COMMAND_ACCOUNT_CHECK,
        None,
        "system.check_account_logged_out",
        replace=True,
    )
    heos = await Heos.create_and_connect("127.0.0.1")
    assert not heos.is_signed_in
    assert not heos.signed_in_username

    await heos.disconnect()


@pytest.mark.asyncio
async def test_connect_with_credentials_logs_in(mock_device: MockHeosDevice) -> None:
    """Test heos signs-in when credentials provided."""
    data = {
        const.ATTR_USER_NAME: "example@example.com",
        const.ATTR_PASSWORD: "example",
    }
    mock_device.register(const.COMMAND_SIGN_IN, data, "system.sign_in")

    credentials = Credentials("example@example.com", "example")

    heos = await Heos.create_and_connect("127.0.0.1", credentials=credentials)

    assert heos.is_signed_in
    assert heos.signed_in_username == "example@example.com"

    await heos.disconnect()


@pytest.mark.asyncio
async def test_connect_with_bad_credentials_raises_event(
    mock_device: MockHeosDevice,
) -> None:
    """Test event raised when bad credentials supplied."""
    data = {
        const.ATTR_USER_NAME: "example@example.com",
        const.ATTR_PASSWORD: "example",
    }
    mock_device.register(const.COMMAND_SIGN_IN, data, "system.sign_in_failure")
    mock_device.register(
        const.COMMAND_ACCOUNT_CHECK,
        None,
        "system.check_account_logged_out",
        replace=True,
    )
    credentials = Credentials("example@example.com", "example")
    heos = Heos(HeosOptions("127.0.0.1", credentials=credentials))

    signal = asyncio.Event()

    async def handler(event: str) -> None:
        assert event == const.EVENT_USER_CREDENTIALS_INVALID
        signal.set()

    heos.dispatcher.connect(const.SIGNAL_HEOS_EVENT, handler)

    await heos.connect()
    await signal.wait()

    assert not heos.is_signed_in
    assert heos.signed_in_username is None

    await heos.disconnect()


@pytest.mark.asyncio
async def test_heart_beat(mock_device: MockHeosDevice) -> None:
    """Test heart beat fires at interval."""
    heos = await Heos.create_and_connect("127.0.0.1", heart_beat_interval=0.1)

    await asyncio.sleep(0.2)

    connection = mock_device.connections[0]
    assert len(connection.commands[const.COMMAND_HEART_BEAT]) == 1

    await heos.disconnect()


@pytest.mark.asyncio
async def test_connect_fails() -> None:
    """Test connect fails when host not available."""
    heos = Heos(HeosOptions("127.0.0.1", timeout=0.1))
    with pytest.raises(HeosError) as e_info:
        await heos.connect()
    assert isinstance(e_info.value.__cause__, ConnectionRefusedError)
    # Also fails for initial connection even with reconnect.
    with pytest.raises(HeosError) as e_info:
        await heos.connect()
    assert isinstance(e_info.value.__cause__, ConnectionRefusedError)
    await heos.disconnect()


@pytest.mark.asyncio
async def test_connect_timeout() -> None:
    """Test connect fails when host not available."""
    heos = Heos(HeosOptions("172.0.0.1", timeout=0.1))
    with pytest.raises(HeosError) as e_info:
        await heos.connect()
    assert isinstance(e_info.value.__cause__, asyncio.TimeoutError)
    # Also fails for initial connection even with reconnect.
    with pytest.raises(HeosError) as e_info:
        await heos.connect()
    assert isinstance(e_info.value.__cause__, asyncio.TimeoutError)
    await heos.disconnect()


@pytest.mark.asyncio
async def test_disconnect(mock_device: MockHeosDevice, heos: Heos) -> None:
    """Test disconnect updates state and fires signal."""
    # Fixture automatically connects
    signal = connect_handler(heos, const.SIGNAL_HEOS_EVENT, const.EVENT_DISCONNECTED)
    await heos.disconnect()
    await signal.wait()
    assert heos.connection_state == const.STATE_DISCONNECTED


@pytest.mark.asyncio
async def test_commands_fail_when_disconnected(
    mock_device: MockHeosDevice, heos: Heos, caplog: pytest.LogCaptureFixture
) -> None:
    """Test calling commands fail when disconnected."""
    # Fixture automatically connects
    await heos.disconnect()
    assert heos.connection_state == const.STATE_DISCONNECTED

    with pytest.raises(CommandError, match="Not connected to device") as e_info:
        await heos.load_players()
    assert e_info.value.command == const.COMMAND_GET_PLAYERS
    assert (
        "Command failed 'heos://player/get_players': Not connected to device"
        in caplog.text
    )


@pytest.mark.asyncio
async def test_connection_error(mock_device: MockHeosDevice, heos: Heos) -> None:
    """Test connection error during event results in disconnected."""
    disconnect_signal = connect_handler(
        heos, const.SIGNAL_HEOS_EVENT, const.EVENT_DISCONNECTED
    )

    # Assert transitions to disconnected and fires disconnect
    await mock_device.stop()
    await disconnect_signal.wait()
    assert heos.connection_state == const.STATE_DISCONNECTED


@pytest.mark.asyncio
async def test_connection_error_during_command(
    mock_device: MockHeosDevice, heos: Heos
) -> None:
    """Test connection error during command results in disconnected."""
    disconnect_signal = connect_handler(
        heos, const.SIGNAL_HEOS_EVENT, const.EVENT_DISCONNECTED
    )

    # Assert transitions to disconnected and fires disconnect
    await mock_device.stop()
    with pytest.raises(CommandError) as e_info:
        await heos.get_players()
    assert str(e_info.value) == "Command timed out"
    assert isinstance(e_info.value.__cause__, asyncio.TimeoutError)

    await disconnect_signal.wait()
    assert heos.connection_state == const.STATE_DISCONNECTED


@pytest.mark.asyncio
async def test_reconnect_during_event(mock_device: MockHeosDevice) -> None:
    """Test reconnect while waiting for events/responses."""
    heos = Heos(
        HeosOptions(
            "127.0.0.1",
            timeout=0.1,
            auto_reconnect=True,
            auto_reconnect_delay=0.1,
            heart_beat=False,
        )
    )

    connect_signal = connect_handler(
        heos, const.SIGNAL_HEOS_EVENT, const.EVENT_CONNECTED
    )
    disconnect_signal = connect_handler(
        heos, const.SIGNAL_HEOS_EVENT, const.EVENT_DISCONNECTED
    )

    # Assert open and fires connected
    await heos.connect()
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
async def test_reconnect_during_command(mock_device: MockHeosDevice) -> None:
    """Test reconnect while waiting for events/responses."""
    heos = Heos(
        HeosOptions(
            "127.0.0.1",
            timeout=0.1,
            auto_reconnect=True,
            auto_reconnect_delay=0.1,
        )
    )

    connect_signal = connect_handler(
        heos, const.SIGNAL_HEOS_EVENT, const.EVENT_CONNECTED
    )
    disconnect_signal = connect_handler(
        heos, const.SIGNAL_HEOS_EVENT, const.EVENT_DISCONNECTED
    )

    # Assert open and fires connected
    await heos.connect()
    await connect_signal.wait()
    assert heos.connection_state == const.STATE_CONNECTED
    connect_signal.clear()

    # Act
    await mock_device.stop()
    await mock_device.start()
    with pytest.raises(CommandError) as e_info:
        await heos.get_players()
    assert str(e_info.value) == "Command timed out"
    assert isinstance(e_info.value.__cause__, asyncio.TimeoutError)

    # Assert signals set
    await disconnect_signal.wait()
    await connect_signal.wait()
    assert heos.connection_state == const.STATE_CONNECTED

    await heos.disconnect()


@pytest.mark.asyncio
async def test_reconnect_cancelled(mock_device: MockHeosDevice) -> None:
    """Test reconnect is canceled by calling disconnect."""
    heos = Heos(
        HeosOptions(
            "127.0.0.1",
            timeout=0.1,
            auto_reconnect=True,
            auto_reconnect_delay=0.1,
        )
    )

    connect_signal = connect_handler(
        heos, const.SIGNAL_HEOS_EVENT, const.EVENT_CONNECTED
    )
    disconnect_signal = connect_handler(
        heos, const.SIGNAL_HEOS_EVENT, const.EVENT_DISCONNECTED
    )

    # Assert open and fires connected
    await heos.connect()
    await connect_signal.wait()
    assert heos.connection_state == const.STATE_CONNECTED
    connect_signal.clear()

    # Assert transitions to reconnecting and fires disconnect
    await mock_device.stop()
    await disconnect_signal.wait()
    assert heos.connection_state == const.STATE_RECONNECTING

    await asyncio.sleep(0.3)

    # Assert reconnects once server is back up and fires connected
    await heos.disconnect()
    assert heos.connection_state == const.STATE_DISCONNECTED


@pytest.mark.asyncio
async def test_get_players(mock_device: MockHeosDevice, heos: Heos) -> None:
    """Test the get_players method load players."""
    await heos.get_players()
    # Assert players loaded
    assert len(heos.players) == 2
    player = heos.players[1]
    assert player.player_id == 1
    assert player.name == "Back Patio"
    assert player.ip_address == "127.0.0.1"
    assert player.line_out == 1
    assert player.model == "HEOS Drive"
    assert player.network == const.NETWORK_TYPE_WIRED
    assert player.state == const.PLAY_STATE_STOP
    assert player.version == "1.493.180"
    assert player.volume == 36
    assert not player.is_muted
    assert player.repeat == const.REPEAT_OFF
    assert not player.shuffle
    assert player.available
    assert player.heos == heos


@pytest.mark.asyncio
async def test_get_players_error(mock_device: MockHeosDevice, heos: Heos) -> None:
    """Test the get_players method load players."""
    mock_device.register(
        const.COMMAND_GET_PLAYERS, None, "player.get_players_error", replace=True
    )

    with pytest.raises(CommandFailedError) as e_info:
        await heos.get_players()
    assert str(e_info.value) == "System error -519 (12)"
    assert e_info.value.command == const.COMMAND_GET_PLAYERS
    assert e_info.value.error_id == 12
    assert e_info.value.error_text == "System error -519"


@pytest.mark.asyncio
async def test_player_state_changed_event(
    mock_device: MockHeosDevice, heos: Heos
) -> None:
    """Test playing state updates when event is received."""
    # assert not playing
    await heos.get_players()
    player = heos.players[1]
    assert player.state == const.PLAY_STATE_STOP

    # Attach dispatch handler
    signal = asyncio.Event()

    async def handler(player_id: int, event: str) -> None:
        assert player_id == player.player_id
        assert event == const.EVENT_PLAYER_STATE_CHANGED
        signal.set()

    heos.dispatcher.connect(const.SIGNAL_PLAYER_EVENT, handler)

    # Write event through mock device
    event_to_raise = (
        (await get_fixture("event.player_state_changed"))
        .replace("{player_id}", str(player.player_id))
        .replace("{state}", const.PLAY_STATE_PLAY)
    )
    await mock_device.write_event(event_to_raise)

    # Wait until the signal
    await signal.wait()
    # Assert state changed
    assert player.state == const.PLAY_STATE_PLAY
    assert heos.players[2].state == const.PLAY_STATE_STOP


@pytest.mark.asyncio
async def test_player_now_playing_changed_event(
    mock_device: MockHeosDevice, heos: Heos
) -> None:
    """Test now playing updates when event is received."""
    # assert current state
    await heos.get_players()
    player = heos.players[1]
    now_playing = player.now_playing_media
    assert now_playing.album == ""
    assert now_playing.type == "song"
    assert now_playing.album_id == ""
    assert now_playing.artist == ""
    assert now_playing.image_url == ""
    assert now_playing.media_id == "catalog/playlists/genres"
    assert now_playing.queue_id == 1
    assert now_playing.source_id == 13
    assert now_playing.song == "Disney Hits"
    assert now_playing.station is None
    assert now_playing.supported_controls == const.CONTROLS_ALL

    # Attach dispatch handler
    signal = asyncio.Event()

    async def handler(player_id: int, event: str) -> None:
        assert player_id == player.player_id
        assert event == const.EVENT_PLAYER_NOW_PLAYING_CHANGED
        signal.set()

    heos.dispatcher.connect(const.SIGNAL_PLAYER_EVENT, handler)

    # Write event through mock device
    mock_device.register(
        const.COMMAND_GET_NOW_PLAYING_MEDIA,
        None,
        "player.get_now_playing_media_changed",
        replace=True,
    )
    event_to_raise = (await get_fixture("event.player_now_playing_changed")).replace(
        "{player_id}", str(player.player_id)
    )
    await mock_device.write_event(event_to_raise)

    # Wait until the signal is set
    await signal.wait()
    # Assert state changed
    assert now_playing.album == "I've Been Waiting (Single) (Explicit)"
    assert now_playing.type == "station"
    assert now_playing.album_id == "1"
    assert now_playing.artist == "Lil Peep & ILoveMakonnen"
    assert now_playing.image_url == "http://media/url"
    assert now_playing.media_id == "2PxuY99Qty"
    assert now_playing.queue_id == 1
    assert now_playing.source_id == 1
    assert now_playing.song == "I've Been Waiting (feat. Fall Out Boy)"
    assert now_playing.station == "Today's Hits Radio"
    assert now_playing.current_position is None
    assert now_playing.current_position_updated is None
    assert now_playing.duration is None
    assert now_playing.supported_controls == const.CONTROLS_FORWARD_ONLY


@pytest.mark.asyncio
async def test_player_volume_changed_event(
    mock_device: MockHeosDevice, heos: Heos
) -> None:
    """Test volume state updates when event is received."""
    # assert not playing
    await heos.get_players()
    player = heos.players[1]
    assert player.volume == 36
    assert not player.is_muted

    # Attach dispatch handler
    signal = asyncio.Event()

    async def handler(player_id: int, event: str) -> None:
        assert player_id == player.player_id
        assert event == const.EVENT_PLAYER_VOLUME_CHANGED
        signal.set()

    heos.dispatcher.connect(const.SIGNAL_PLAYER_EVENT, handler)

    # Write event through mock device
    event_to_raise = (
        (await get_fixture("event.player_volume_changed"))
        .replace("{player_id}", str(player.player_id))
        .replace("{level}", "50.0")
        .replace("{mute}", "on")
    )
    await mock_device.write_event(event_to_raise)

    # Wait until the signal is set
    await signal.wait()
    # Assert state changed
    assert player.volume == 50
    assert player.is_muted
    assert heos.players[2].volume == 36  # type: ignore[unreachable]
    assert not heos.players[2].is_muted


@pytest.mark.asyncio
async def test_player_now_playing_progress_event(
    mock_device: MockHeosDevice, heos: Heos
) -> None:
    """Test now playing progress updates when event received."""
    # assert not playing
    await heos.get_players()
    player = heos.players[1]
    assert player.now_playing_media.duration is None
    assert player.now_playing_media.current_position is None
    assert player.now_playing_media.current_position_updated is None

    # Attach dispatch handler
    signal = asyncio.Event()

    async def handler(player_id: int, event: str) -> None:
        assert player_id == player.player_id
        assert event == const.EVENT_PLAYER_NOW_PLAYING_PROGRESS
        signal.set()

    heos.dispatcher.connect(const.SIGNAL_PLAYER_EVENT, handler)

    # Write event through mock device
    event_to_raise = (
        (await get_fixture("event.player_now_playing_progress"))
        .replace("{player_id}", str(player.player_id))
        .replace("{cur_pos}", "113000")
        .replace("{duration}", "210000")
    )
    await mock_device.write_event(event_to_raise)

    # Wait until the signal is set or timeout
    await signal.wait()
    # Assert state changed
    assert player.now_playing_media.duration == 210000
    assert player.now_playing_media.current_position == 113000
    assert player.now_playing_media.current_position_updated is not None
    player2 = heos.players.get(2)  # type: ignore[unreachable]
    assert player2.now_playing_media.duration is None
    assert player2.now_playing_media.current_position is None
    assert player2.now_playing_media.current_position_updated is None


@pytest.mark.asyncio
async def test_limited_progress_event_updates(mock_device: MockHeosDevice) -> None:
    """Test progress updates only once if no other events."""
    # assert not playing
    heos = await Heos.create_and_connect("127.0.0.1", all_progress_events=False)
    await heos.get_players()
    player = heos.players[1]

    # Attach dispatch handler
    signal = asyncio.Event()

    async def handler(player_id: int, event: str) -> None:
        if not signal.is_set():
            signal.set()
        else:
            pytest.fail("Handler invoked more than once.")

    heos.dispatcher.connect(const.SIGNAL_PLAYER_EVENT, handler)

    # Write event through mock device
    event_to_raise = (
        (await get_fixture("event.player_now_playing_progress"))
        .replace("{player_id}", str(player.player_id))
        .replace("{cur_pos}", "113000")
        .replace("{duration}", "210000")
    )

    # raise it multiple times.
    await mock_device.write_event(event_to_raise)
    await mock_device.write_event(event_to_raise)
    await mock_device.write_event(event_to_raise)
    await signal.wait()
    await heos.disconnect()


@pytest.mark.asyncio
async def test_repeat_mode_changed_event(
    mock_device: MockHeosDevice, heos: Heos
) -> None:
    """Test repeat mode changes when event received."""
    # assert not playing
    await heos.get_players()
    player = heos.players[1]
    assert player.repeat == const.REPEAT_OFF

    # Attach dispatch handler
    signal = asyncio.Event()

    async def handler(player_id: int, event: str) -> None:
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
async def test_shuffle_mode_changed_event(
    mock_device: MockHeosDevice, heos: Heos
) -> None:
    """Test shuffle mode changes when event received."""
    # assert not playing
    await heos.get_players()
    player = heos.players[1]
    assert not player.shuffle

    # Attach dispatch handler
    signal = asyncio.Event()

    async def handler(player_id: int, event: str) -> None:
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
async def test_players_changed_event(mock_device: MockHeosDevice, heos: Heos) -> None:
    """Test players are resynced when event received."""
    # assert not playing
    old_players = (await heos.get_players()).copy()

    # Attach dispatch handler
    signal = asyncio.Event()

    async def handler(event: str, data: dict[str, Any]) -> None:
        assert event == const.EVENT_PLAYERS_CHANGED
        assert data == {const.DATA_NEW: [3], const.DATA_MAPPED_IDS: {}}
        signal.set()

    heos.dispatcher.connect(const.SIGNAL_CONTROLLER_EVENT, handler)

    # Write event through mock device
    mock_device.register(
        const.COMMAND_GET_PLAYERS, None, "player.get_players_changed", replace=True
    )
    event_to_raise = await get_fixture("event.players_changed")
    await mock_device.write_event(event_to_raise)

    # Wait until the signal is set
    await signal.wait()
    assert len(heos.players) == 3
    # Assert 2 (Front Porch) was marked unavailable
    assert not old_players[2].available
    assert old_players[2] == heos.players[2]
    # Assert 3 (Basement) was added
    assert heos.players.get(3) is not None
    # Assert 1 (Backyard) was updated
    assert heos.players[1].name == "Backyard"


@pytest.mark.asyncio
async def test_players_changed_event_new_ids(
    mock_device: MockHeosDevice, heos: Heos
) -> None:
    """Test players are resynced when event received after firmware update."""
    # assert not playing
    old_players = (await heos.get_players()).copy()
    # Attach dispatch handler
    signal = asyncio.Event()

    async def handler(event: str, data: dict[str, Any]) -> None:
        assert event == const.EVENT_PLAYERS_CHANGED
        assert data == {const.DATA_NEW: [], const.DATA_MAPPED_IDS: {101: 1, 102: 2}}
        signal.set()

    heos.dispatcher.connect(const.SIGNAL_CONTROLLER_EVENT, handler)

    # Write event through mock device
    mock_device.register(
        const.COMMAND_GET_PLAYERS,
        None,
        "player.get_players_firmware_update",
        replace=True,
    )
    await mock_device.write_event(await get_fixture("event.players_changed"))
    await signal.wait()
    # Assert players are the same as before just updated.
    assert len(heos.players) == 2
    assert heos.players[101] == old_players[1]
    assert heos.players[101].available
    assert heos.players[101].name == "Back Patio"
    assert heos.players[102] == old_players[2]
    assert heos.players[102].available
    assert heos.players[102].name == "Front Porch"


@pytest.mark.asyncio
async def test_sources_changed_event(mock_device: MockHeosDevice, heos: Heos) -> None:
    """Test sources changed fires dispatcher."""
    mock_device.register(
        const.COMMAND_BROWSE_GET_SOURCES, None, "browse.get_music_sources"
    )
    await heos.get_music_sources()
    signal = asyncio.Event()

    async def handler(event: str, data: dict[str, Any]) -> None:
        assert event == const.EVENT_SOURCES_CHANGED
        signal.set()

    heos.dispatcher.connect(const.SIGNAL_CONTROLLER_EVENT, handler)

    # Write event through mock device
    mock_device.register(
        const.COMMAND_BROWSE_GET_SOURCES,
        None,
        "browse.get_music_sources_changed",
        replace=True,
    )
    event_to_raise = await get_fixture("event.sources_changed")
    await mock_device.write_event(event_to_raise)

    # Wait until the signal is set
    await signal.wait()
    assert heos.music_sources[const.MUSIC_SOURCE_TUNEIN].available


@pytest.mark.asyncio
async def test_groups_changed_event(mock_device: MockHeosDevice, heos: Heos) -> None:
    """Test groups changed fires dispatcher."""
    groups = await heos.get_groups()
    assert len(groups) == 1
    signal = asyncio.Event()

    async def handler(event: str, data: dict[str, Any]) -> None:
        assert event == const.EVENT_GROUPS_CHANGED
        signal.set()

    heos.dispatcher.connect(const.SIGNAL_CONTROLLER_EVENT, handler)

    # Write event through mock device
    mock_device.register(
        const.COMMAND_GET_GROUPS, None, "group.get_groups_changed", replace=True
    )
    event_to_raise = await get_fixture("event.groups_changed")
    await mock_device.write_event(event_to_raise)

    # Wait until the signal is set
    await signal.wait()
    assert not await heos.get_groups()


@pytest.mark.asyncio
async def test_player_playback_error_event(
    mock_device: MockHeosDevice, heos: Heos
) -> None:
    """Test player playback error fires dispatcher."""
    await heos.get_players()
    signal = asyncio.Event()

    async def handler(player_id: int, event: str) -> None:
        assert player_id == 1
        assert event == const.EVENT_PLAYER_PLAYBACK_ERROR
        signal.set()

    heos.dispatcher.connect(const.SIGNAL_PLAYER_EVENT, handler)

    # Write event through mock device
    event_to_raise = await get_fixture("event.player_playback_error")
    await mock_device.write_event(event_to_raise)

    # Wait until the signal is set
    await signal.wait()
    assert heos.players[1].playback_error == "Could Not Download"


@pytest.mark.asyncio
async def test_player_queue_changed_event(
    mock_device: MockHeosDevice, heos: Heos
) -> None:
    """Test player queue changed fires dispatcher."""
    await heos.get_players()
    signal = asyncio.Event()

    async def handler(player_id: int, event: str) -> None:
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
async def test_group_volume_changed_event(
    mock_device: MockHeosDevice, heos: Heos
) -> None:
    """Test group volume changed fires dispatcher."""
    await heos.get_groups()
    group = heos.groups[1]
    assert group.volume == 42
    assert not group.is_muted

    signal = asyncio.Event()

    async def handler(group_id: int, event: str) -> None:
        assert group_id == 1
        assert event == const.EVENT_GROUP_VOLUME_CHANGED
        signal.set()

    heos.dispatcher.connect(const.SIGNAL_GROUP_EVENT, handler)

    # Write event through mock device
    event_to_raise = await get_fixture("event.group_volume_changed")
    await mock_device.write_event(event_to_raise)

    # Wait until the signal is set
    await signal.wait()
    assert group.volume == 50
    assert group.is_muted


@pytest.mark.asyncio
async def test_user_changed_event(mock_device: MockHeosDevice, heos: Heos) -> None:
    """Test user changed fires dispatcher and updates logged in user."""
    signal = asyncio.Event()

    async def handler(event: str, data: dict[str, Any]) -> None:
        assert event == const.EVENT_USER_CHANGED
        signal.set()

    heos.dispatcher.connect(const.SIGNAL_CONTROLLER_EVENT, handler)

    # Test signed out event
    event_to_raise = await get_fixture("event.user_changed_signed_out")
    await mock_device.write_event(event_to_raise)
    await signal.wait()
    assert not heos.is_signed_in
    assert not heos.signed_in_username

    # Test signed in event
    signal.clear()
    event_to_raise = await get_fixture("event.user_changed_signed_in")
    await mock_device.write_event(event_to_raise)
    await signal.wait()
    assert heos.is_signed_in
    assert heos.signed_in_username == "example@example.com"  # type: ignore[unreachable]


@pytest.mark.asyncio
async def test_get_music_sources(mock_device: MockHeosDevice, heos: Heos) -> None:
    """Test the heos connect method."""
    mock_device.register(
        const.COMMAND_BROWSE_GET_SOURCES, None, "browse.get_music_sources"
    )

    sources = await heos.get_music_sources()
    assert len(sources) == 15
    pandora = sources[const.MUSIC_SOURCE_PANDORA]
    assert pandora.source_id == 1
    assert (
        pandora.image_url
        == "https://production.ws.skyegloup.com:443/media/images/service/logos/pandora.png"
    )
    assert pandora.type == const.TYPE_MUSIC_SERVICE
    assert pandora.available
    assert pandora.service_username == "test@test.com"
    assert not pandora.container
    assert not pandora.playable


@pytest.mark.asyncio
async def test_get_input_sources(mock_device: MockHeosDevice, heos: Heos) -> None:
    """Test the get input sources method."""
    mock_device.register(
        const.COMMAND_BROWSE_BROWSE, {"sid": "1027"}, "browse.browse_aux_input"
    )
    mock_device.register(
        const.COMMAND_BROWSE_BROWSE,
        {"sid": "546978854"},
        "browse.browse_theater_receiver",
    )
    mock_device.register(
        const.COMMAND_BROWSE_BROWSE, {"sid": "-263109739"}, "browse.browse_heos_drive"
    )

    sources = await heos.get_input_sources()
    assert len(sources) == 18
    source = sources[0]
    assert source.name == "Theater Receiver - CBL/SAT"
    assert source.input_name == const.INPUT_CABLE_SAT
    assert source.player_id == 546978854


@pytest.mark.asyncio
async def test_get_favorites(mock_device: MockHeosDevice, heos: Heos) -> None:
    """Test the get favorites method."""
    mock_device.register(
        const.COMMAND_BROWSE_BROWSE, {"sid": "1028"}, "browse.browse_favorites"
    )

    sources = await heos.get_favorites()
    assert len(sources) == 3
    assert sorted(sources.keys()) == [1, 2, 3]
    fav = sources[1]
    assert fav.playable
    assert fav.name == "Thumbprint Radio"
    assert fav.type == const.TYPE_STATION


@pytest.mark.asyncio
async def test_get_playlists(mock_device: MockHeosDevice, heos: Heos) -> None:
    """Test the get playlists method."""
    mock_device.register(
        const.COMMAND_BROWSE_BROWSE, {"sid": "1025"}, "browse.browse_playlists"
    )
    sources = await heos.get_playlists()
    assert len(sources) == 1
    playlist = sources[0]
    assert playlist.playable
    assert playlist.container
    assert playlist.container_id == "171566"
    assert playlist.name == "Rockin Songs"
    assert playlist.type == const.TYPE_PLAYLIST
    assert playlist.source_id == const.MUSIC_SOURCE_PLAYLISTS


@pytest.mark.asyncio
async def test_sign_in_and_out(
    mock_device: MockHeosDevice, heos: Heos, caplog: pytest.LogCaptureFixture
) -> None:
    """Test the sign in and sign out methods and ensure log is masked."""
    # Test sign-out (Heos will already be logged in initially)
    mock_device.register(const.COMMAND_SIGN_OUT, None, "system.sign_out")
    await heos.sign_out()
    assert heos.signed_in_username is None

    data = {
        const.ATTR_USER_NAME: "example@example.com",
        const.ATTR_PASSWORD: "example",
    }

    # Test sign-in failure
    mock_device.register(const.COMMAND_SIGN_IN, data, "system.sign_in_failure")
    with pytest.raises(CommandFailedError, match="User not found"):
        await heos.sign_in("example@example.com", "example")
    assert (
        "Command failed 'heos://system/sign_in?un=example@example.com&pw=********':"
        in caplog.text
    )
    assert heos.signed_in_username is None

    # Test sign-in success
    mock_device.register(const.COMMAND_SIGN_IN, data, "system.sign_in", replace=True)
    await heos.sign_in("example@example.com", "example")
    assert (
        "Command executed 'heos://system/sign_in?un=example@example.com&pw=********':"
        in caplog.text
    )
    assert heos.signed_in_username == data[const.ATTR_USER_NAME]


@pytest.mark.asyncio
async def test_get_groups(mock_device: MockHeosDevice, heos: Heos) -> None:
    """Test the get groups method."""
    groups = await heos.get_groups()
    assert len(groups) == 1
    group = groups[1]
    assert group.name == "Back Patio + Front Porch"
    assert group.group_id == 1
    assert group.leader.player_id == 1
    assert len(group.members) == 1
    assert group.members[0].player_id == 2
    assert group.volume == 42
    assert not group.is_muted


@pytest.mark.asyncio
async def test_create_group(mock_device: MockHeosDevice, heos: Heos) -> None:
    """Test creating a group."""
    data = {const.ATTR_PLAYER_ID: "1,2,3"}
    mock_device.register(const.COMMAND_SET_GROUP, data, "group.set_group_create")
    await heos.create_group(1, [2, 3])


@pytest.mark.asyncio
async def test_remove_group(mock_device: MockHeosDevice, heos: Heos) -> None:
    """Test removing a group."""
    data = {const.ATTR_PLAYER_ID: "1"}
    mock_device.register(const.COMMAND_SET_GROUP, data, "group.set_group_remove")
    await heos.remove_group(1)


@pytest.mark.asyncio
async def test_update_group(mock_device: MockHeosDevice, heos: Heos) -> None:
    """Test removing a group."""
    data = {const.ATTR_PLAYER_ID: "1,2"}
    mock_device.register(const.COMMAND_SET_GROUP, data, "group.set_group_update")
    await heos.update_group(1, [2])
