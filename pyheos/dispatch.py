"""Defines the dispatch component for notifying others of signals."""

import asyncio
import functools
import logging
from collections import defaultdict
from collections.abc import Callable, Sequence
from typing import Any, Final

_LOGGER: Final = logging.getLogger(__name__)

TargetType = Callable[..., Any]
DisconnectType = Callable[[], None]
ConnectType = Callable[[str, TargetType], DisconnectType]
SendType = Callable[..., Sequence[asyncio.Future]]


class Dispatcher:
    """Define the dispatch class."""

    def __init__(
        self,
        *,
        connect: ConnectType | None = None,
        send: SendType | None = None,
        signal_prefix: str = "",
        loop: asyncio.AbstractEventLoop | None = None,
    ) -> None:
        """Create a new instance of the dispatch component."""
        self._signal_prefix = signal_prefix
        self._signals: dict[str, list] = defaultdict(list)
        self._loop = loop or asyncio.get_running_loop()
        self._connect = connect or self._default_connect
        self._send = send or self._default_send
        self._disconnects: list[Callable] = []
        self._running_tasks: set[asyncio.Future] = set()

    def connect(self, signal: str, target: TargetType) -> DisconnectType:
        """Connect function to signal.  Must be ran in the event loop."""
        disconnect = self._connect(self._signal_prefix + signal, target)
        self._disconnects.append(disconnect)
        return disconnect

    def send(self, signal: str, *args: Any) -> Sequence[asyncio.Future]:
        """Fire a signal.  Must be ran in the event loop."""
        return self._send(self._signal_prefix + signal, *args)

    async def wait_send(
        self,
        signal: str,
        *args: Any,
        return_exceptions: bool = False,
    ) -> list[asyncio.Future[Any] | BaseException]:
        """Fire a signal and wait for all to complete."""
        return await asyncio.gather(  # type: ignore[no-any-return]
            *self.send(signal, *args), return_exceptions=return_exceptions
        )

    def disconnect_all(self) -> None:
        """Disconnect all connected."""
        disconnects = self._disconnects.copy()
        self._disconnects.clear()
        for disconnect in disconnects:
            disconnect()

    async def wait_all(self, cancel: bool = False) -> None:
        """Wait for all targets to complete."""
        if cancel:
            for task in self._running_tasks:
                task.cancel()
        await asyncio.gather(*self._running_tasks, return_exceptions=True)

    def _default_connect(self, signal: str, target: TargetType) -> DisconnectType:
        """Connect function to signal.  Must be ran in the event loop."""
        self._signals[signal].append(target)

        def remove_dispatcher() -> None:
            """Remove signal listener."""
            try:
                self._signals[signal].remove(target)
            except ValueError:
                # signal was already removed
                pass

        return remove_dispatcher

    def _log_target_exception(self, future: asyncio.Future) -> None:
        """Log the exception from the target, if raised."""
        if not future.cancelled() and future.exception():
            _LOGGER.exception(
                "Exception in target callback: %s",
                future,
                exc_info=future.exception(),
            )

    def _default_send(self, signal: str, *args: Any) -> Sequence[asyncio.Future]:
        """Fire a signal.  Must be ran in the event loop."""
        targets = self._signals[signal]
        futures = []
        for target in targets:
            task = self._call_target(target, *args)
            self._running_tasks.add(task)
            task.add_done_callback(self._running_tasks.discard)
            task.add_done_callback(self._log_target_exception)
            futures.append(task)
        return futures

    def _call_target(self, target: Callable, *args: Any) -> asyncio.Future:
        check_target = target
        while isinstance(check_target, functools.partial):
            check_target = check_target.func
        if asyncio.iscoroutinefunction(check_target):
            return self._loop.create_task(target(*args))
        return self._loop.run_in_executor(None, target, *args)

    @property
    def signals(self) -> dict[str, list[TargetType]]:
        """Get the dictionary of registered signals and callbacks."""
        return self._signals
