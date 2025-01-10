"""Defines the dispatch component for notifying others of signals."""

import asyncio
import functools
import logging
from collections import defaultdict
from collections.abc import Callable, Sequence
from typing import Any, Final, TypeVar

_LOGGER: Final = logging.getLogger(__name__)

TargetType = Callable[..., Any]
DisconnectType = Callable[[], None]
ConnectType = Callable[[str, TargetType], DisconnectType]
SendType = Callable[..., Sequence[asyncio.Future]]

TEvent = TypeVar("TEvent", bound=str)
TPlayerId = TypeVar("TPlayerId", bound=int)
TGroupId = TypeVar("TGroupId", bound=int)

CallbackType = Callable[[], Any]
EventCallbackType = Callable[[TEvent], Any]
ControllerEventCallbackType = Callable[[TEvent, Any], Any]
PlayerEventCallbackType = Callable[[TPlayerId, TEvent], Any]
GroupEventCallbackType = Callable[[TGroupId, TEvent], Any]


def _is_coroutine_function(func: TargetType) -> bool:
    """Return True if func is a decorated coroutine function."""

    while isinstance(func, functools.partial):
        func = func.func
    return asyncio.iscoroutinefunction(func)


def _filter_args(
    args: tuple[Any], arg_filter: dict[int, Any]
) -> tuple[bool, tuple[Any]]:
    """Filters the supplied args and returns True if matched and the updated args list."""
    for key, value in arg_filter.items():
        resolved_value = value() if callable(value) else value
        if args[key] != resolved_value:
            return False, args
        list_args = list(args)
        list_args.pop(key)
        args = tuple(list_args)
    return True, args


def callback_wrapper(callback: TargetType, args_filter: dict[int, Any]) -> TargetType:
    """Create a wrapper for the callback and filters the arguments supplied."""
    wrapper: TargetType
    if _is_coroutine_function(callback):

        @functools.wraps(callback)
        async def wrapper(*args: Any, **kwargs: Any) -> None:
            match, new_args = _filter_args(args, args_filter)
            if match:
                await callback(*new_args, **kwargs)
    else:

        @functools.wraps(callback)
        def wrapper(*args: Any, **kwargs: Any) -> None:
            match, new_args = _filter_args(args, args_filter)
            if match:
                callback(*new_args, **kwargs)

    return wrapper


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
        if _is_coroutine_function(target):
            return self._loop.create_task(target(*args))
        return self._loop.run_in_executor(None, target, *args)

    @property
    def signals(self) -> dict[str, list[TargetType]]:
        """Get the dictionary of registered signals and callbacks."""
        return self._signals
