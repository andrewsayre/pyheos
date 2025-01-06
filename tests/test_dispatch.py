"""Define tests for the Dispatch module."""

import functools
from collections.abc import Callable
from typing import Any

import pytest

from pyheos.dispatch import Dispatcher


async def test_connect(handler: Callable) -> None:
    """Tests the connect function."""
    # Arrange
    dispatcher = Dispatcher()
    # Act
    dispatcher.connect("TEST", handler)
    # Assert
    assert handler in dispatcher.signals["TEST"]


async def test_disconnect(handler: Callable) -> None:
    """Tests the disconnect function."""
    # Arrange
    dispatcher = Dispatcher()
    disconnect = dispatcher.connect("TEST", handler)
    # Act
    disconnect()
    # Assert
    assert handler not in dispatcher.signals["TEST"]


async def test_disconnect_all(handler: Callable) -> None:
    """Tests the disconnect all function."""
    # Arrange
    dispatcher = Dispatcher()
    dispatcher.connect("TEST", handler)
    dispatcher.connect("TEST", handler)
    dispatcher.connect("TEST2", handler)
    dispatcher.connect("TEST3", handler)
    # Act
    dispatcher.disconnect_all()
    # Assert
    assert handler not in dispatcher.signals["TEST"]
    assert handler not in dispatcher.signals["TEST2"]
    assert handler not in dispatcher.signals["TEST3"]


async def test_already_disconnected(handler: Callable) -> None:
    """Tests that disconnect can be called more than once."""
    # Arrange
    dispatcher = Dispatcher()
    disconnect = dispatcher.connect("TEST", handler)
    disconnect()
    # Act
    disconnect()
    # Assert
    assert handler not in dispatcher.signals["TEST"]


async def test_send_async_handler(async_handler: Callable) -> None:
    """Tests sending to async handlers."""
    # Arrange
    dispatcher = Dispatcher()
    dispatcher.connect("TEST", async_handler)
    # Act
    await dispatcher.wait_send("TEST")
    # Assert
    assert async_handler.fired  # type: ignore[attr-defined]


async def test_send_async_handler_exception_logged(
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Tests sending to async handlers."""
    # Arrange
    dispatcher = Dispatcher()

    async def async_handler_exception() -> None:
        raise ValueError("Error in handler.")

    dispatcher.connect("TEST", async_handler_exception)
    # Act
    dispatcher.send("TEST")
    # Assert
    await dispatcher.wait_all()
    assert "Exception in target callback:" in caplog.text


async def test_send_async_handler_canceled(
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Tests sending to async handlers."""
    # Arrange
    dispatcher = Dispatcher()

    async def async_handler_exception() -> None:
        raise ValueError("Error in handler.")

    dispatcher.connect("TEST", async_handler_exception)
    # Act
    dispatcher.send("TEST")
    # Assert
    await dispatcher.wait_all(True)
    assert "Exception in target callback:" not in caplog.text


async def test_send_async_partial_handler(async_handler: Callable) -> None:
    """Tests sending to async handlers."""
    # Arrange
    partial = functools.partial(async_handler)
    dispatcher = Dispatcher()
    dispatcher.connect("TEST", partial)
    # Act
    await dispatcher.wait_send("TEST")
    # Assert
    assert async_handler.fired  # type: ignore[attr-defined]


async def test_send(handler: Callable) -> None:
    """Tests sending to async handlers."""
    # Arrange
    dispatcher = Dispatcher()
    dispatcher.connect("TEST", handler)
    args = object()
    # Act
    await dispatcher.wait_send("TEST", args)
    # Assert
    assert handler.fired  # type: ignore[attr-defined]
    assert handler.args[0] == args  # type: ignore[attr-defined]


async def test_custom_connect_and_send(handler: Callable) -> None:
    """Tests using the custom connect and send implementations."""
    # Arrange
    test_signal = "PREFIX_TEST"
    stored_target = None

    def connect(signal: str, target: Callable) -> Callable:
        assert signal == test_signal
        nonlocal stored_target
        stored_target = target

        def disconnect() -> None:
            nonlocal stored_target
            stored_target = None

        return disconnect

    def send(signal: str, *args: Any) -> None:
        assert signal == test_signal
        assert stored_target is not None
        stored_target(*args)  # pylint:disable=not-callable

    dispatcher = Dispatcher(connect=connect, send=send, signal_prefix="PREFIX_")  # type: ignore[arg-type]

    # Act
    dispatcher.connect("TEST", handler)
    dispatcher.send("TEST")
    # Assert
    assert handler.fired  # type: ignore[attr-defined]
