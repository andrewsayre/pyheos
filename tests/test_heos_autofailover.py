"""Define module for testing autofailover functionality."""

from pyheos import command as c
from pyheos.const import EVENT_PLAYERS_CHANGED
from pyheos.heos import Heos
from pyheos.options import HeosOptions
from pyheos.types import ConnectionState, SignalHeosEvent, SignalType
from tests import MockHeosDevice, calls_command, connect_handler


@calls_command("player.get_players")
async def test_failover_hosts_updated_on_connection(
    mock_device: MockHeosDevice,
) -> None:
    """Test failover hosts are populated after connecting."""
    heos = Heos(
        HeosOptions(
            "127.0.0.1",
            timeout=0.1,
            auto_reconnect=True,
            auto_reconnect_delay=0.1,
            auto_failover=True,
            heart_beat=False,
        )
    )
    await heos.connect()
    assert heos.connection_state == ConnectionState.CONNECTED
    assert heos._connection.failover_hosts == ["127.0.0.2"]
    await heos.disconnect()


@calls_command("player.get_players")
async def test_failover_hosts_updated_on_players_changed(
    mock_device: MockHeosDevice,
) -> None:
    """Test failover hosts are updated when players change."""
    heos = Heos(
        HeosOptions(
            "127.0.0.1",
            timeout=0.1,
            auto_reconnect=True,
            auto_reconnect_delay=0.1,
            auto_failover=True,
            heart_beat=False,
        )
    )
    await heos.connect()

    event = connect_handler(heos, SignalType.CONTROLLER_EVENT, EVENT_PLAYERS_CHANGED)
    # Write event through mock device
    mock_device.register(
        c.COMMAND_GET_PLAYERS, None, "player.get_players_changed", replace=True
    )
    await mock_device.write_event("event.players_changed")

    # Wait until the signal is set
    await event.wait()
    assert heos._connection.failover_hosts == ["127.0.0.3", "192.168.0.1"]
    await heos.disconnect()


async def test_failover_hosts_manually_provided_hosts(
    mock_device: MockHeosDevice,
) -> None:
    """Test manually provided hosts are preserved."""
    heos = Heos(
        HeosOptions(
            "127.0.0.1",
            timeout=0.1,
            auto_reconnect=True,
            auto_reconnect_delay=0.1,
            auto_failover=True,
            auto_failover_hosts=["127.0.0.3"],
            heart_beat=False,
        )
    )
    await heos.connect()
    assert heos.connection_state == ConnectionState.CONNECTED
    assert heos._connection.failover_hosts == ["127.0.0.3"]
    await heos.disconnect()


@calls_command("player.get_players")
async def test_failover(mock_device: MockHeosDevice) -> None:
    """Test reconnect while waiting for events/responses."""
    heos = Heos(
        HeosOptions(
            "127.0.0.1",
            timeout=0.1,
            auto_reconnect=True,
            auto_reconnect_delay=0.1,
            heart_beat=False,
            auto_failover=True,
        )
    )

    connect_signal = connect_handler(
        heos, SignalType.HEOS_EVENT, SignalHeosEvent.CONNECTED
    )
    disconnect_signal = connect_handler(
        heos, SignalType.HEOS_EVENT, SignalHeosEvent.DISCONNECTED
    )

    # Assert open and fires connected
    await heos.connect()
    assert connect_signal.is_set()
    assert heos.connection_state == ConnectionState.CONNECTED
    connect_signal.clear()

    # Assert transitions to reconnecting and fires disconnect
    await mock_device.stop()
    await mock_device.start("127.0.0.2")
    await disconnect_signal.wait()
    assert heos.connection_state == ConnectionState.RECONNECTING  # type: ignore[comparison-overlap]

    failover_task = next(  # type: ignore[unreachable]
        task
        for task in heos._connection._running_tasks
        if task.get_name() == "Failover"
    )
    await connect_signal.wait()
    assert heos.connection_state == ConnectionState.CONNECTED
    assert heos.current_host == "127.0.0.2"

    await failover_task  # Ensures task completes, otherwise disconnect cancels it
    await heos.disconnect()


@calls_command("player.get_players")
async def test_failover_retries_current_host(mock_device: MockHeosDevice) -> None:
    """Test failover first attempts to reconnect to the current host."""
    heos = Heos(
        HeosOptions(
            "127.0.0.1",
            timeout=0.1,
            auto_reconnect=True,
            auto_reconnect_delay=0.1,
            heart_beat=False,
            auto_failover=True,
        )
    )

    connect_signal = connect_handler(
        heos, SignalType.HEOS_EVENT, SignalHeosEvent.CONNECTED
    )
    disconnect_signal = connect_handler(
        heos, SignalType.HEOS_EVENT, SignalHeosEvent.DISCONNECTED
    )

    # Assert open and fires connected
    await heos.connect()
    assert connect_signal.is_set()
    assert heos.connection_state == ConnectionState.CONNECTED
    connect_signal.clear()

    # Assert transitions to reconnecting and fires disconnect
    await mock_device.restart()
    await disconnect_signal.wait()
    assert heos.connection_state == ConnectionState.RECONNECTING  # type: ignore[comparison-overlap]

    failover_task = next(  # type: ignore[unreachable]
        task
        for task in heos._connection._running_tasks
        if task.get_name() == "Failover"
    )

    await connect_signal.wait()
    assert heos.connection_state == ConnectionState.CONNECTED
    assert heos.current_host == "127.0.0.1"

    await failover_task  # Ensures task completes, otherwise disconnect cancels it
    await heos.disconnect()
