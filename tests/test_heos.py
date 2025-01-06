"""Tests for the heos class."""

import asyncio
import re
from typing import Any

import pytest

from pyheos import command as commands
from pyheos import const
from pyheos.credentials import Credentials
from pyheos.dispatch import Dispatcher
from pyheos.error import CommandError, CommandFailedError, HeosError
from pyheos.heos import Heos, HeosOptions
from pyheos.media import MediaItem, MediaMusicSource
from tests.common import MediaItems

from . import (
    CallCommand,
    MockHeosDevice,
    calls_command,
    calls_commands,
    calls_group_commands,
    calls_player_commands,
    connect_handler,
)


async def test_init() -> None:
    """Test init sets properties."""
    heos = Heos(HeosOptions("127.0.0.1"))
    assert isinstance(heos.dispatcher, Dispatcher)
    assert len(heos.players) == 0
    assert len(heos.music_sources) == 0
    assert heos.connection_state == const.STATE_DISCONNECTED


@calls_command("player.get_players")
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


async def test_connect(mock_device: MockHeosDevice) -> None:
    """Test connect updates state and fires signal."""
    heos = Heos(
        HeosOptions(
            "127.0.0.1", timeout=0.1, auto_reconnect_delay=0.1, heart_beat=False
        )
    )
    signal = connect_handler(heos, const.SIGNAL_HEOS_EVENT, const.EVENT_CONNECTED)
    await heos.connect()
    assert signal.is_set()
    assert heos.connection_state == const.STATE_CONNECTED
    assert len(mock_device.connections) == 1
    connection = mock_device.connections[0]
    assert connection.is_registered_for_events
    assert heos.is_signed_in
    assert heos.signed_in_username == "example@example.com"
    await heos.disconnect()


@calls_command("system.check_account_logged_out", replace=True)
async def test_connect_not_logged_in(mock_device: MockHeosDevice) -> None:
    """Test signed-in status shows correctly when logged out."""
    heos = await Heos.create_and_connect("127.0.0.1", heart_beat=False)
    assert not heos.is_signed_in
    assert not heos.signed_in_username
    await heos.disconnect()


@calls_command(
    "system.sign_in",
    {const.ATTR_USER_NAME: "example@example.com", const.ATTR_PASSWORD: "example"},
)
async def test_connect_with_credentials_logs_in(mock_device: MockHeosDevice) -> None:
    """Test heos signs-in when credentials provided."""
    credentials = Credentials("example@example.com", "example")
    heos = await Heos.create_and_connect(
        "127.0.0.1", credentials=credentials, heart_beat=False
    )
    assert heos.is_signed_in
    assert heos.signed_in_username == "example@example.com"
    await heos.disconnect()


@calls_command(
    "system.sign_in_failure",
    {const.ATTR_USER_NAME: "example@example.com", const.ATTR_PASSWORD: "example"},
)
async def test_connect_with_bad_credentials_dispatches_event(
    mock_device: MockHeosDevice,
) -> None:
    """Test event raised when bad credentials supplied."""
    credentials = Credentials("example@example.com", "example")
    heos = Heos(HeosOptions("127.0.0.1", credentials=credentials, heart_beat=False))

    signal = connect_handler(
        heos, const.SIGNAL_HEOS_EVENT, const.EVENT_USER_CREDENTIALS_INVALID
    )

    await heos.connect()
    assert signal.is_set()

    assert not heos.is_signed_in
    assert heos.signed_in_username is None

    await heos.disconnect()


@calls_command(
    "browse.browse_fail_user_not_logged_in",
    {const.ATTR_SOURCE_ID: const.MUSIC_SOURCE_FAVORITES},
    add_command_under_process=True,
)
async def test_command_credential_error_dispatches_event(heos: Heos) -> None:
    """Test command error with credential error dispatches event."""
    assert heos.is_signed_in
    assert heos.signed_in_username is not None

    signal = connect_handler(
        heos, const.SIGNAL_HEOS_EVENT, const.EVENT_USER_CREDENTIALS_INVALID
    )

    with pytest.raises(CommandFailedError):
        await heos.get_favorites()

    assert signal.is_set()
    assert not heos.is_signed_in
    assert heos.signed_in_username is None  # type: ignore[unreachable]


@calls_command("system.heart_beat")
async def test_background_heart_beat(mock_device: MockHeosDevice) -> None:
    """Test heart beat fires at interval."""
    heos = await Heos.create_and_connect("127.0.0.1", heart_beat_interval=0.1)
    await asyncio.sleep(0.3)

    mock_device.assert_command_called(commands.COMMAND_HEART_BEAT)

    await heos.disconnect()


async def test_connect_fails() -> None:
    """Test connect fails when host not available."""
    heos = Heos(HeosOptions("127.0.0.1", timeout=0.1, heart_beat=False))
    with pytest.raises(HeosError) as e_info:
        await heos.connect()
    assert isinstance(e_info.value.__cause__, ConnectionRefusedError)
    # Also fails for initial connection even with reconnect.
    with pytest.raises(HeosError) as e_info:
        await heos.connect()
    assert isinstance(e_info.value.__cause__, ConnectionRefusedError)
    await heos.disconnect()


async def test_connect_timeout() -> None:
    """Test connect fails when host not available."""
    heos = Heos(HeosOptions("172.0.0.1", timeout=0.1, heart_beat=False))
    with pytest.raises(HeosError) as e_info:
        await heos.connect()
    assert isinstance(e_info.value.__cause__, asyncio.TimeoutError)
    # Also fails for initial connection even with reconnect.
    with pytest.raises(HeosError) as e_info:
        await heos.connect()
    assert isinstance(e_info.value.__cause__, asyncio.TimeoutError)
    await heos.disconnect()


@pytest.mark.usefixtures("mock_device")
async def test_connect_multiple_succeeds() -> None:
    """Test calling connect multiple times succeeds."""
    heos = Heos(HeosOptions("127.0.0.1", timeout=0.1, heart_beat=False))
    signal = connect_handler(heos, const.SIGNAL_HEOS_EVENT, const.EVENT_CONNECTED)
    try:
        await heos.connect()
        await signal.wait()
        assert heos.connection_state == const.STATE_CONNECTED
        signal.clear()

        # Try calling again
        await heos.connect()
        assert not signal.is_set()
    finally:
        await heos.disconnect()


async def test_disconnect(mock_device: MockHeosDevice, heos: Heos) -> None:
    """Test disconnect updates state and fires signal."""
    # Fixture automatically connects
    signal = connect_handler(heos, const.SIGNAL_HEOS_EVENT, const.EVENT_DISCONNECTED)
    await heos.disconnect()
    assert signal.is_set()
    assert heos.connection_state == const.STATE_DISCONNECTED


async def test_commands_fail_when_disconnected(
    mock_device: MockHeosDevice, heos: Heos, caplog: pytest.LogCaptureFixture
) -> None:
    """Test calling commands fail when disconnected."""
    # Fixture automatically connects
    await heos.disconnect()
    assert heos.connection_state == const.STATE_DISCONNECTED

    with pytest.raises(CommandError, match="Not connected to device") as e_info:
        await heos.load_players()
    assert e_info.value.command == commands.COMMAND_GET_PLAYERS
    assert (
        "Command failed 'heos://player/get_players': Not connected to device"
        in caplog.text
    )


async def test_connection_error(mock_device: MockHeosDevice, heos: Heos) -> None:
    """Test connection error during event results in disconnected."""
    disconnect_signal = connect_handler(
        heos, const.SIGNAL_HEOS_EVENT, const.EVENT_DISCONNECTED
    )

    # Assert transitions to disconnected and fires disconnect
    await mock_device.stop()
    await disconnect_signal.wait()
    assert heos.connection_state == const.STATE_DISCONNECTED


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
    assert connect_signal.is_set()
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


async def test_reconnect_during_command(mock_device: MockHeosDevice) -> None:
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
    assert connect_signal.is_set()
    assert heos.connection_state == const.STATE_CONNECTED
    connect_signal.clear()

    # Act
    await mock_device.stop()
    await mock_device.start()
    with pytest.raises(CommandError, match="Connection lost"):
        await heos.get_players()

    # Assert signals set
    await disconnect_signal.wait()
    await connect_signal.wait()
    assert heos.connection_state == const.STATE_CONNECTED

    await heos.disconnect()


async def test_reconnect_cancelled(mock_device: MockHeosDevice) -> None:
    """Test reconnect is canceled by calling disconnect."""
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
    assert connect_signal.is_set()
    assert heos.connection_state == const.STATE_CONNECTED
    connect_signal.clear()

    # Assert transitions to reconnecting and fires disconnect
    await mock_device.stop()
    await disconnect_signal.wait()
    assert heos.connection_state == const.STATE_RECONNECTING

    await asyncio.sleep(0.3)

    # Assert calling disconnect sets state to disconnected
    await heos.disconnect()
    assert heos.connection_state == const.STATE_DISCONNECTED


@calls_player_commands()
async def test_get_players(heos: Heos) -> None:
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
    assert player.state == const.PlayState.STOP
    assert player.version == "1.493.180"
    assert player.volume == 36
    assert not player.is_muted
    assert player.repeat == const.RepeatType.OFF
    assert not player.shuffle
    assert player.available
    assert player.heos == heos


@calls_player_commands()
async def test_player_availability_matches_connection_state(heos: Heos) -> None:
    """Test that loaded players' availability matches the connection state."""
    await heos.get_players()
    # Assert players loaded
    assert len(heos.players) == 2
    player = heos.players[1]
    assert player.available

    # Disconnect, unavailable
    await heos.disconnect()
    assert not player.available, "Player should be unavailable after disconnect"

    # Reonnected, available
    await heos.connect()  # type: ignore[unreachable]
    assert player.available, "Player should be available after reconnect"


@calls_command("player.get_players_error")
async def test_get_players_error(heos: Heos) -> None:
    """Test the get_players method load players."""
    with pytest.raises(CommandFailedError, match=re.escape("System error -519 (12)")):
        await heos.get_players()


@calls_player_commands()
async def test_player_state_changed_event(
    mock_device: MockHeosDevice, heos: Heos
) -> None:
    """Test playing state updates when event is received."""
    # assert not playing
    await heos.get_players()
    player = heos.players[1]
    assert player.state == const.PlayState.STOP

    # Attach dispatch handler
    signal = asyncio.Event()

    async def handler(event: str) -> None:
        assert event == const.EVENT_PLAYER_STATE_CHANGED
        signal.set()

    player.add_on_player_event(handler)

    # Write event through mock device
    await mock_device.write_event(
        "event.player_state_changed",
        {"player_id": player.player_id, "state": const.PlayState.PLAY},
    )

    # Wait until the signal
    await signal.wait()
    # Assert state changed
    assert player.state == const.PlayState.PLAY  # type: ignore[comparison-overlap]
    assert heos.players[2].state == const.PlayState.STOP  # type: ignore[unreachable]


@calls_player_commands()
async def test_player_now_playing_changed_event(
    mock_device: MockHeosDevice, heos: Heos
) -> None:
    """Test now playing updates when event is received."""
    # assert current state
    await heos.get_players()
    player = heos.players[1]
    now_playing = player.now_playing_media
    assert now_playing.type == "station"
    assert now_playing.song == "Disney (Children's) Radio"
    assert now_playing.station == "Disney (Children's) Radio"
    assert now_playing.album == "Album"
    assert now_playing.artist == "Artist"
    assert (
        now_playing.image_url
        == "http://cont-5.p-cdn.us/images/public/int/6/1/1/9/050087149116_500W_500H.jpg"
    )
    assert now_playing.album_id == "123456"
    assert now_playing.media_id == "4256592506324148495"
    assert now_playing.queue_id == 1
    assert now_playing.source_id == 13
    assert now_playing.supported_controls == const.CONTROLS_ALL

    # Attach dispatch handler
    signal = asyncio.Event()

    async def handler(player_id: int, event: str) -> None:
        assert player_id == player.player_id
        assert event == const.EVENT_PLAYER_NOW_PLAYING_CHANGED
        signal.set()

    heos.dispatcher.connect(const.SIGNAL_PLAYER_EVENT, handler)

    # Write event through mock device
    command = mock_device.register(
        commands.COMMAND_GET_NOW_PLAYING_MEDIA,
        None,
        "player.get_now_playing_media_changed",
        replace=True,
    )
    await mock_device.write_event(
        "event.player_now_playing_changed", {"player_id": player.player_id}
    )

    # Wait until the signal is set
    await signal.wait()
    # Assert state changed
    command.assert_called()
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


@calls_player_commands()
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
    await mock_device.write_event(
        "event.player_volume_changed",
        {
            "player_id": player.player_id,
            "level": 50.0,
            "mute": const.VALUE_ON,
        },
    )

    # Wait until the signal is set
    await signal.wait()
    # Assert state changed
    assert player.volume == 50
    assert player.is_muted
    assert heos.players[2].volume == 36  # type: ignore[unreachable]
    assert not heos.players[2].is_muted


@calls_player_commands()
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
    await mock_device.write_event(
        "event.player_now_playing_progress",
        {
            "player_id": player.player_id,
            "cur_pos": 113000,
            "duration": 210000,
        },
    )

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


@calls_player_commands()
async def test_limited_progress_event_updates(mock_device: MockHeosDevice) -> None:
    """Test progress updates only once if no other events."""
    # assert not playing
    heos = await Heos.create_and_connect(
        "127.0.0.1", all_progress_events=False, heart_beat=False
    )
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

    # raise it multiple times.
    await mock_device.write_event(
        "event.player_now_playing_progress",
        {
            "player_id": player.player_id,
            "cur_pos": 113000,
            "duration": 210000,
        },
    )
    await mock_device.write_event(
        "event.player_now_playing_progress",
        {
            "player_id": player.player_id,
            "cur_pos": 113000,
            "duration": 210000,
        },
    )
    await asyncio.sleep(0.1)  # Ensures the second event is sent through
    await signal.wait()
    await heos.disconnect()


@calls_player_commands()
async def test_repeat_mode_changed_event(
    mock_device: MockHeosDevice, heos: Heos
) -> None:
    """Test repeat mode changes when event received."""
    # assert not playing
    await heos.get_players()
    player = heos.players[1]
    assert player.repeat == const.RepeatType.OFF

    # Attach dispatch handler
    signal = asyncio.Event()

    async def handler(player_id: int, event: str) -> None:
        assert player_id == player.player_id
        assert event == const.EVENT_REPEAT_MODE_CHANGED
        signal.set()

    heos.dispatcher.connect(const.SIGNAL_PLAYER_EVENT, handler)

    # Write event through mock device
    await mock_device.write_event("event.repeat_mode_changed")

    # Wait until the signal is set
    await signal.wait()
    # Assert state changed
    assert player.repeat == const.RepeatType.ON_ALL  # type: ignore[comparison-overlap]


@calls_player_commands()
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
    await mock_device.write_event("event.shuffle_mode_changed")

    # Wait until the signal is set
    await signal.wait()
    # Assert state changed
    assert player.shuffle


@calls_player_commands((1, 2, 3))
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
    command = mock_device.register(
        commands.COMMAND_GET_PLAYERS, None, "player.get_players_changed", replace=True
    )
    await mock_device.write_event("event.players_changed")

    # Wait until the signal is set
    await signal.wait()
    command.assert_called()
    assert len(heos.players) == 3
    # Assert 2 (Front Porch) was marked unavailable
    assert not old_players[2].available
    assert old_players[2] == heos.players[2]
    # Assert 3 (Basement) was added
    assert heos.players.get(3) is not None
    # Assert 1 (Backyard) was updated
    assert heos.players[1].name == "Backyard"


@calls_player_commands((1, 2, 101, 102))
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
    command = mock_device.register(
        commands.COMMAND_GET_PLAYERS,
        None,
        "player.get_players_firmware_update",
        replace=True,
    )
    await mock_device.write_event("event.players_changed")
    await signal.wait()
    # Assert players are the same as before just updated.
    command.assert_called()
    assert len(heos.players) == 2
    assert heos.players[101] == old_players[1]
    assert heos.players[101].available
    assert heos.players[101].name == "Back Patio"
    assert heos.players[102] == old_players[2]
    assert heos.players[102].available
    assert heos.players[102].name == "Front Porch"


@calls_command("browse.get_music_sources", {})
async def test_sources_changed_event(mock_device: MockHeosDevice, heos: Heos) -> None:
    """Test sources changed fires dispatcher."""
    await heos.get_music_sources()
    signal = asyncio.Event()

    async def handler(event: str, data: dict[str, Any]) -> None:
        assert event == const.EVENT_SOURCES_CHANGED
        signal.set()

    heos.dispatcher.connect(const.SIGNAL_CONTROLLER_EVENT, handler)

    # Write event through mock device
    command = mock_device.register(
        commands.COMMAND_BROWSE_GET_SOURCES,
        {const.ATTR_REFRESH: const.VALUE_ON},
        "browse.get_music_sources_changed",
        replace=True,
    )
    await mock_device.write_event("event.sources_changed")

    # Wait until the signal is set
    await signal.wait()
    command.assert_called()
    assert heos.music_sources[const.MUSIC_SOURCE_TUNEIN].available


@calls_group_commands()
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
    command = mock_device.register(
        commands.COMMAND_GET_GROUPS, None, "group.get_groups_changed", replace=True
    )
    await mock_device.write_event("event.groups_changed")

    # Wait until the signal is set
    await signal.wait()
    command.assert_called()
    assert not await heos.get_groups()


@calls_player_commands()
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
    await mock_device.write_event("event.player_playback_error")

    # Wait until the signal is set
    await signal.wait()
    assert heos.players[1].playback_error == "Could Not Download"


@calls_player_commands()
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
    await mock_device.write_event("event.player_queue_changed")

    # Wait until the signal is set
    await signal.wait()


@calls_group_commands()
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
    await mock_device.write_event("event.group_volume_changed")

    # Wait until the signal is set
    await signal.wait()
    assert group.volume == 50
    assert group.is_muted


async def test_user_changed_event(mock_device: MockHeosDevice, heos: Heos) -> None:
    """Test user changed fires dispatcher and updates logged in user."""
    signal = asyncio.Event()

    async def handler(event: str, data: dict[str, Any]) -> None:
        assert event == const.EVENT_USER_CHANGED
        signal.set()

    heos.dispatcher.connect(const.SIGNAL_CONTROLLER_EVENT, handler)

    # Test signed out event
    await mock_device.write_event("event.user_changed_signed_out")
    await signal.wait()
    assert not heos.is_signed_in
    assert not heos.signed_in_username

    # Test signed in event
    signal.clear()
    await mock_device.write_event("event.user_changed_signed_in")
    await signal.wait()
    assert heos.is_signed_in
    assert heos.signed_in_username == "example@example.com"  # type: ignore[unreachable]


@calls_command(
    "browse.browse_favorites", {const.ATTR_SOURCE_ID: const.MUSIC_SOURCE_FAVORITES}
)
async def test_browse_media_music_source(
    heos: Heos,
    media_music_source: MediaMusicSource,
) -> None:
    """Test browse with an unavailable MediaMusicSource raises."""
    result = await heos.browse_media(media_music_source)
    assert result.source_id == const.MUSIC_SOURCE_FAVORITES
    assert result.returned == 3
    assert result.count == 3
    assert len(result.items) == 3


async def test_browse_media_music_source_unavailable_rasises(
    heos: Heos,
    media_music_source_unavailable: MediaMusicSource,
) -> None:
    """Test browse with an unavailable MediaMusicSource raises."""
    with pytest.raises(ValueError, match="Source is not available to browse"):
        await heos.browse_media(media_music_source_unavailable)


@calls_command(
    "browse.browse_album",
    {
        const.ATTR_SOURCE_ID: MediaItems.ALBUM.source_id,
        const.ATTR_CONTAINER_ID: MediaItems.ALBUM.container_id,
        const.ATTR_RANGE: "0,13",
    },
)
async def test_browse_media_item(heos: Heos, media_item_album: MediaItem) -> None:
    """Test browse with an not browsable MediaItem raises."""
    result = await heos.browse_media(media_item_album, 0, 13)

    assert result.source_id == media_item_album.source_id
    assert result.container_id == media_item_album.container_id
    assert result.count == 14
    assert result.returned == 14
    assert len(result.items) == 14


async def test_browse_media_item_not_browsable_raises(
    heos: Heos, media_item_song: MediaItem
) -> None:
    """Test browse with an not browsable MediaItem raises."""
    with pytest.raises(
        ValueError, match="Only media sources and containers can be browsed"
    ):
        await heos.browse_media(media_item_song)


async def test_play_media_unplayable_raises(
    heos: Heos, media_item_album: MediaItem
) -> None:
    """Test play media with unplayable source raises."""
    media_item_album.playable = False

    with pytest.raises(
        ValueError, match=re.escape(f"Media '{media_item_album}' is not playable")
    ):
        await heos.play_media(1, media_item_album, const.AddCriteriaType.PLAY_NOW)


@calls_command(
    "browse.add_to_queue_track",
    {
        const.ATTR_PLAYER_ID: "1",
        const.ATTR_SOURCE_ID: MediaItems.SONG.source_id,
        const.ATTR_CONTAINER_ID: MediaItems.SONG.container_id,
        const.ATTR_MEDIA_ID: MediaItems.SONG.media_id,
        const.ATTR_ADD_CRITERIA_ID: const.AddCriteriaType.PLAY_NOW,
    },
)
async def test_play_media_song(heos: Heos, media_item_song: MediaItem) -> None:
    """Test play song succeeseds."""
    await heos.play_media(1, media_item_song)


async def test_play_media_song_missing_container_raises(
    heos: Heos, media_item_song: MediaItem
) -> None:
    """Test play song succeeseds."""
    media_item_song.container_id = None

    with pytest.raises(
        ValueError,
        match=re.escape(f"Media '{media_item_song}' cannot have a None container_id"),
    ):
        await heos.play_media(1, media_item_song)


@calls_command(
    "browse.play_input",
    {
        const.ATTR_PLAYER_ID: 1,
        const.ATTR_INPUT: MediaItems.INPUT.media_id,
        const.ATTR_SOURCE_PLAYER_ID: MediaItems.INPUT.source_id,
    },
)
async def test_play_media_input(heos: Heos, media_item_input: MediaItem) -> None:
    """Test playing input source succeeds."""
    await heos.play_media(1, media_item_input)


@calls_command(
    "browse.play_stream_station",
    {
        const.ATTR_PLAYER_ID: "1",
        const.ATTR_SOURCE_ID: MediaItems.STATION.source_id,
        const.ATTR_CONTAINER_ID: MediaItems.STATION.container_id,
        const.ATTR_MEDIA_ID: MediaItems.STATION.media_id,
    },
)
async def test_play_media_station(heos: Heos, media_item_station: MediaItem) -> None:
    """Test play song succeeseds."""
    await heos.play_media(1, media_item_station)


async def test_play_media_station_missing_media_id_raises(
    heos: Heos, media_item_station: MediaItem
) -> None:
    """Test play song succeeseds."""
    media_item_station.media_id = None

    with pytest.raises(
        ValueError,
        match=re.escape(f"Media '{media_item_station}' cannot have a None media_id"),
    ):
        await heos.play_media(1, media_item_station)


@calls_command("browse.get_music_sources", {})
async def test_get_music_sources(heos: Heos) -> None:
    """Test the heos connect method."""
    sources = await heos.get_music_sources()
    assert len(sources) == 15
    pandora = sources[const.MUSIC_SOURCE_PANDORA]
    assert pandora.source_id == const.MUSIC_SOURCE_PANDORA
    assert (
        pandora.image_url
        == "https://production.ws.skyegloup.com:443/media/images/service/logos/pandora.png"
    )
    assert pandora.type == const.MediaType.MUSIC_SERVICE
    assert pandora.available
    assert pandora.service_username == "test@test.com"


@calls_commands(
    CallCommand(
        "browse.browse_aux_input", {const.ATTR_SOURCE_ID: const.MUSIC_SOURCE_AUX_INPUT}
    ),
    CallCommand("browse.browse_theater_receiver", {const.ATTR_SOURCE_ID: 546978854}),
    CallCommand("browse.browse_heos_drive", {const.ATTR_SOURCE_ID: -263109739}),
)
async def test_get_input_sources(heos: Heos) -> None:
    """Test the get input sources method."""
    sources = await heos.get_input_sources()
    assert len(sources) == 18
    source = sources[0]
    assert source.playable
    assert source.type == const.MediaType.STATION
    assert source.name == "Theater Receiver - CBL/SAT"
    assert source.media_id == const.INPUT_CABLE_SAT
    assert source.source_id == 546978854


@calls_command(
    "browse.browse_favorites", {const.ATTR_SOURCE_ID: const.MUSIC_SOURCE_FAVORITES}
)
async def test_get_favorites(heos: Heos) -> None:
    """Test the get favorites method."""
    sources = await heos.get_favorites()
    assert len(sources) == 3
    assert sorted(sources.keys()) == [1, 2, 3]
    fav = sources[1]
    assert fav.playable
    assert fav.name == "Thumbprint Radio"
    assert fav.media_id == "3790855220637622543"
    assert (
        fav.image_url
        == "http://mediaserver-cont-ch1-1-v4v6.pandora.com/images/public/devicead/t/r/a/m/daartpralbumart_500W_500H.jpg"
    )
    assert fav.type == const.MediaType.STATION


@calls_command(
    "browse.browse_playlists", {const.ATTR_SOURCE_ID: const.MUSIC_SOURCE_PLAYLISTS}
)
async def test_get_playlists(heos: Heos) -> None:
    """Test the get playlists method."""
    sources = await heos.get_playlists()
    assert len(sources) == 1
    playlist = sources[0]
    assert playlist.playable
    assert playlist.container_id == "171566"
    assert playlist.name == "Rockin Songs"
    assert playlist.image_url == ""
    assert playlist.type == const.MediaType.PLAYLIST
    assert playlist.source_id == const.MUSIC_SOURCE_PLAYLISTS


@calls_command(
    "system.sign_in",
    {const.ATTR_USER_NAME: "example@example.com", const.ATTR_PASSWORD: "example"},
)
async def test_sign_in_does_not_update_credentials(heos: Heos) -> None:
    """Test sign-in does not update existing credentials."""
    assert heos.current_credentials is None
    # Sign-in, do not update credentials
    await heos.sign_in("example@example.com", "example", update_credential=False)
    assert heos.signed_in_username == "example@example.com"
    assert heos.current_credentials is None


@calls_commands(
    CallCommand("system.sign_out"),
    CallCommand(
        "system.sign_in_failure",
        {const.ATTR_USER_NAME: "example@example.com", const.ATTR_PASSWORD: "example"},
    ),
)
async def test_sign_in_and_out(heos: Heos, caplog: pytest.LogCaptureFixture) -> None:
    """Test the sign in and sign out methods and ensure log is masked."""
    # Test sign-out (Heos will already be logged in initially)
    await heos.sign_out()
    assert heos.signed_in_username is None

    # Test sign-in failure
    with pytest.raises(CommandFailedError, match="User not found"):
        await heos.sign_in("example@example.com", "example")
    assert (
        "Command failed 'heos://system/sign_in?un=example@example.com&pw=********':"
        in caplog.text
    )
    assert heos.current_credentials is None
    assert heos.signed_in_username is None


@calls_commands(
    CallCommand("system.sign_out"),
    CallCommand(
        "system.sign_in",
        {const.ATTR_USER_NAME: "example@example.com", const.ATTR_PASSWORD: "example"},
    ),
)
async def test_sign_in_updates_credential(
    heos: Heos, caplog: pytest.LogCaptureFixture
) -> None:
    """Test the credential is updated when indicated."""
    # Test sign-out (Heos will already be logged in initially)
    await heos.sign_out()
    assert heos.current_credentials is None
    assert heos.signed_in_username is None

    # Test sign-in success and credential set
    await heos.sign_in("example@example.com", "example")
    assert (
        "Command executed 'heos://system/sign_in?un=example@example.com&pw=********':"
        in caplog.text
    )
    assert heos.signed_in_username == "example@example.com"
    assert heos.current_credentials is not None
    assert heos.current_credentials.username == "example@example.com"  # type: ignore[unreachable]
    assert heos.current_credentials.password == "example"

    # Test sign-out does not clear credential
    await heos.sign_out(update_credential=False)
    assert heos.signed_in_username is None
    assert heos.current_credentials is not None


@calls_group_commands()
async def test_get_groups(heos: Heos) -> None:
    """Test the get groups method."""
    groups = await heos.get_groups()
    assert len(groups) == 1
    group = groups[1]
    assert group.name == "Back Patio + Front Porch"
    assert group.group_id == 1
    assert group.lead_player_id == 1
    assert len(group.member_player_ids) == 1
    assert group.member_player_ids[0] == 2
    assert group.volume == 42
    assert not group.is_muted


@calls_command("group.set_group_create", {const.ATTR_PLAYER_ID: "1,2,3"})
async def test_create_group(heos: Heos) -> None:
    """Test creating a group."""
    await heos.create_group(1, [2, 3])


@calls_command("group.set_group_remove", {const.ATTR_PLAYER_ID: 1})
async def test_remove_group(heos: Heos) -> None:
    """Test removing a group."""
    await heos.remove_group(1)


@calls_command("group.set_group_update", {const.ATTR_PLAYER_ID: "1,2"})
async def test_update_group(heos: Heos) -> None:
    """Test removing a group."""
    await heos.update_group(1, [2])


@calls_command("player.get_now_playing_media", {const.ATTR_PLAYER_ID: 1})
async def test_get_now_playing_media(heos: Heos) -> None:
    """Test removing a group."""
    media = await heos.get_now_playing_media(1)

    assert media.type == "station"
    assert media.song == "Disney (Children's) Radio"
    assert media.station == "Disney (Children's) Radio"
    assert media.album == "Album"
    assert media.artist == "Artist"
    assert (
        media.image_url
        == "http://cont-5.p-cdn.us/images/public/int/6/1/1/9/050087149116_500W_500H.jpg"
    )
    assert media.album_id == "123456"
    assert media.media_id == "4256592506324148495"
    assert media.queue_id == 1
    assert media.source_id == 13
    assert media.supported_controls == const.CONTROLS_ALL


@calls_command("system.heart_beat")
async def test_heart_beat(heos: Heos) -> None:
    """Test the heart beat command."""
    await heos.heart_beat()


@pytest.mark.usefixtures("mock_device")
async def test_reboot() -> None:
    """Test rebooting the device."""
    heos = await Heos.create_and_connect(
        "127.0.0.1", auto_reconnect=True, auto_reconnect_delay=0.2, heart_beat=False
    )

    try:
        disconnect_signal = connect_handler(
            heos, const.SIGNAL_HEOS_EVENT, const.EVENT_DISCONNECTED
        )
        connect_signal = connect_handler(
            heos, const.SIGNAL_HEOS_EVENT, const.EVENT_CONNECTED
        )

        await heos.reboot()

        # wait for disconnect
        await disconnect_signal.wait()
        assert heos.connection_state == const.STATE_RECONNECTING

        # wait for reconnect
        await connect_signal.wait()
        assert heos.connection_state == const.STATE_CONNECTED
    finally:
        await heos.disconnect()
    assert heos.connection_state == const.STATE_DISCONNECTED


async def test_unrecognized_event_logs(
    mock_device: MockHeosDevice, heos: Heos, caplog: pytest.LogCaptureFixture
) -> None:
    """Test repeat mode changes when event received."""
    # Write event through mock device
    await mock_device.write_event("event.invalid")

    await asyncio.sleep(
        0.2
    )  # Figure out a better way to wait for the log to be written
    await heos.dispatcher.wait_all()

    assert "Unrecognized event: " in caplog.text
