"""Define the options module."""

from dataclasses import dataclass, field

from pyheos import const
from pyheos.credentials import Credentials
from pyheos.dispatch import Dispatcher


@dataclass(frozen=True)
class HeosOptions:
    """
    The HeosOptions encapsulates options for connecting to a Heos System.

    Args:
        host: A host name or IP address of a HEOS-capable device.
        timeout: The timeout in seconds for opening a connectoin and issuing commands to the device.
        events: Set to True to enable event updates, False to disable. The default is True.
        heart_beat: Set to True to enable heart beat messages, False to disable. Used in conjunction with heart_beat_delay. The default is True.
        heart_beat_interval: The interval in seconds between heart beat messages. Used in conjunction with heart_beat.
        all_progress_events: Set to True to receive media progress events, False to only receive media changed events. The default is True.
        dispatcher: The dispatcher instance to use for event callbacks. If not provided, an internally created instance will be used.
        auto_reconnect: Set to True to automatically reconnect if the connection is lost. The default is False. Used in conjunction with auto_reconnect_delay.
        auto_reconnect_delay: The delay in seconds before attempting to reconnect. The default is 10 seconds. Used in conjunction with auto_reconnect.
        credentials: credentials to use to automatically sign-in to the HEOS account upon successful connection. If not provided, the account will not be signed in.
    """

    host: str
    timeout: float = field(default=const.DEFAULT_TIMEOUT, kw_only=True)
    events: bool = field(default=True, kw_only=True)
    all_progress_events: bool = field(default=True, kw_only=True)
    dispatcher: Dispatcher | None = field(default=None, kw_only=True)
    auto_reconnect: bool = field(default=False, kw_only=True)
    auto_reconnect_delay: float = field(
        default=const.DEFAULT_RECONNECT_DELAY, kw_only=True
    )
    auto_reconnect_max_attempts: int = field(
        default=const.DEFAULT_RECONNECT_ATTEMPTS, kw_only=True
    )
    heart_beat: bool = field(default=True, kw_only=True)
    heart_beat_interval: float = field(default=const.DEFAULT_HEART_BEAT, kw_only=True)
    credentials: Credentials | None = field(default=None, kw_only=True)
