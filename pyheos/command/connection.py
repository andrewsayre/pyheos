"""Define the connection mixin module."""

from pyheos.connection import AutoFailoverConnection
from pyheos.options import HeosOptions
from pyheos.types import ConnectionState


class ConnectionMixin:
    "A mixin to provide access to the connection."

    def __init__(self, options: HeosOptions) -> None:
        """Init a new instance of the ConnectionMixin."""
        self._options = options
        self._connection = AutoFailoverConnection(
            options.host,
            timeout=options.timeout,
            reconnect=options.auto_reconnect,
            reconnect_delay=options.auto_reconnect_delay,
            reconnect_max_attempts=options.auto_reconnect_max_attempts,
            heart_beat=options.heart_beat,
            heart_beat_interval=options.heart_beat_interval,
            failover=options.auto_failover,
            failover_hosts=options.auto_failover_hosts,
        )

    @property
    def connection_state(self) -> ConnectionState:
        """Get the state of the connection."""
        return self._connection.state

    @property
    def current_host(self) -> str:
        """Get the host name or IP address."""
        return self._connection.host
