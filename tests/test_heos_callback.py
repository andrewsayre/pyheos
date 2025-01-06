"""Define tests for the HEOS class callback handlers."""

from pyheos import const
from pyheos.heos import Heos, HeosOptions


async def test_add_on_connected() -> None:
    """Test adding a callback for when the client connects."""

    called = False

    def callback() -> None:
        nonlocal called
        called = True

    heos = Heos(HeosOptions(""))

    disconnect = heos.add_on_connected(callback)

    # Simulate sending event
    await heos.dispatcher.wait_send(const.SIGNAL_HEOS_EVENT, const.EVENT_CONNECTED)
    assert called

    # Test disconnct
    called = False
    disconnect()
    await heos.dispatcher.wait_send(const.SIGNAL_HEOS_EVENT, const.EVENT_CONNECTED)
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
    await heos.dispatcher.wait_send(const.SIGNAL_HEOS_EVENT, const.EVENT_CONNECTED)
    assert called

    # Test disconnct
    called = False
    disconnect()
    await heos.dispatcher.wait_send(const.SIGNAL_HEOS_EVENT, const.EVENT_CONNECTED)
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
    await heos.dispatcher.wait_send(const.SIGNAL_HEOS_EVENT, const.EVENT_DISCONNECTED)
    assert called

    # Test disconnct
    called = False
    disconnect()
    await heos.dispatcher.wait_send(const.SIGNAL_HEOS_EVENT, const.EVENT_DISCONNECTED)
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
    await heos.dispatcher.wait_send(const.SIGNAL_HEOS_EVENT, const.EVENT_DISCONNECTED)
    assert called

    # Test disconnct
    called = False
    disconnect()
    await heos.dispatcher.wait_send(const.SIGNAL_HEOS_EVENT, const.EVENT_DISCONNECTED)
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
        const.SIGNAL_HEOS_EVENT, const.EVENT_USER_CREDENTIALS_INVALID
    )
    assert called

    # Test disconnct
    called = False
    disconnect()
    await heos.dispatcher.wait_send(
        const.SIGNAL_HEOS_EVENT, const.EVENT_USER_CREDENTIALS_INVALID
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
        const.SIGNAL_HEOS_EVENT, const.EVENT_USER_CREDENTIALS_INVALID
    )
    assert called

    # Test disconnct
    called = False
    disconnect()
    await heos.dispatcher.wait_send(
        const.SIGNAL_HEOS_EVENT, const.EVENT_USER_CREDENTIALS_INVALID
    )
    assert not called
