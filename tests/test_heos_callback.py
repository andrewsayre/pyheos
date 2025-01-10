"""Define tests for the HEOS class callback handlers."""

from typing import Any

from pyheos.heos import Heos, HeosOptions
from pyheos.types import SignalHeosEvent, SignalType


async def test_add_on_connected() -> None:
    """Test adding a callback for when the client connects."""

    called = False

    def callback() -> None:
        nonlocal called
        called = True

    heos = Heos(HeosOptions(""))

    disconnect = heos.add_on_connected(callback)

    # Simulate sending event
    await heos.dispatcher.wait_send(SignalType.HEOS_EVENT, SignalHeosEvent.CONNECTED)
    assert called
    called = False

    # Test other events don't raise
    #
    await heos.dispatcher.wait_send(SignalType.HEOS_EVENT, SignalHeosEvent.DISCONNECTED)
    assert not called

    # Test disconnct

    disconnect()
    await heos.dispatcher.wait_send(SignalType.HEOS_EVENT, SignalHeosEvent.CONNECTED)
    assert not called


async def test_add_on_connected_coroutine() -> None:
    """Test adding a callback for when the client connects."""

    called = False

    async def callback() -> None:
        nonlocal called
        called = True

    heos = Heos(HeosOptions(""))
    disconnect = heos.add_on_connected(callback)

    # Simulate sending event
    await heos.dispatcher.wait_send(SignalType.HEOS_EVENT, SignalHeosEvent.CONNECTED)
    assert called

    # Test disconnct
    called = False
    disconnect()
    await heos.dispatcher.wait_send(SignalType.HEOS_EVENT, SignalHeosEvent.CONNECTED)
    assert not called


async def test_add_on_disconnected() -> None:
    """Test adding a callback for when the client disconnects."""

    called = False

    def callback() -> None:
        nonlocal called
        called = True

    heos = Heos(HeosOptions(""))
    disconnect = heos.add_on_disconnected(callback)

    # Simulate sending event
    await heos.dispatcher.wait_send(SignalType.HEOS_EVENT, SignalHeosEvent.DISCONNECTED)
    assert called

    # Test disconnct
    called = False
    disconnect()
    await heos.dispatcher.wait_send(SignalType.HEOS_EVENT, SignalHeosEvent.DISCONNECTED)
    assert not called


async def test_add_on_disconnected_coroutine() -> None:
    """Test adding a callback for when the client disconnects."""

    called = False

    async def callback() -> None:
        nonlocal called
        called = True

    heos = Heos(HeosOptions(""))
    disconnect = heos.add_on_disconnected(callback)

    # Simulate sending event
    await heos.dispatcher.wait_send(SignalType.HEOS_EVENT, SignalHeosEvent.DISCONNECTED)
    assert called

    # Test disconnct
    called = False
    disconnect()
    await heos.dispatcher.wait_send(SignalType.HEOS_EVENT, SignalHeosEvent.DISCONNECTED)
    assert not called


async def test_add_on_user_credentials_invalid() -> None:
    """Test adding a callback for when user credentials are invalid."""

    called = False

    def callback() -> None:
        nonlocal called
        called = True

    heos = Heos(HeosOptions(""))
    disconnect = heos.add_on_user_credentials_invalid(callback)

    # Simulate sending event
    await heos.dispatcher.wait_send(
        SignalType.HEOS_EVENT, SignalHeosEvent.USER_CREDENTIALS_INVALID
    )
    assert called

    # Test disconnct
    called = False
    disconnect()
    await heos.dispatcher.wait_send(
        SignalType.HEOS_EVENT, SignalHeosEvent.USER_CREDENTIALS_INVALID
    )
    assert not called


async def test_add_on_user_credentials_invalid_coroutine() -> None:
    """Test adding a callback for when user credentials are invalid."""

    called = False

    async def callback() -> None:
        nonlocal called
        called = True

    heos = Heos(HeosOptions(""))
    disconnect = heos.add_on_user_credentials_invalid(callback)

    # Simulate sending event
    await heos.dispatcher.wait_send(
        SignalType.HEOS_EVENT, SignalHeosEvent.USER_CREDENTIALS_INVALID
    )
    assert called

    # Test disconnct
    called = False
    disconnect()
    await heos.dispatcher.wait_send(
        SignalType.HEOS_EVENT, SignalHeosEvent.USER_CREDENTIALS_INVALID
    )
    assert not called


async def test_add_on_controller_event() -> None:
    """Test adding a callback for controller events."""

    called = False
    target_event = "Test"
    target_data = "Test data"

    def callback(event: str, data: Any) -> None:
        nonlocal called
        called = True
        assert event == target_event
        assert data == target_data

    heos = Heos(HeosOptions(""))

    disconnect = heos.add_on_controller_event(callback)

    # Simulate sending event
    await heos.dispatcher.wait_send(
        SignalType.CONTROLLER_EVENT, target_event, target_data
    )
    assert called
    called = False

    # Test other events don't raise
    #
    await heos.dispatcher.wait_send(SignalType.GROUP_EVENT, target_event, target_data)
    assert not called

    # Test disconnct

    disconnect()
    await heos.dispatcher.wait_send(SignalType.HEOS_EVENT, SignalHeosEvent.CONNECTED)
    assert not called
