"""Define the System module."""

from dataclasses import dataclass
from functools import cached_property

from pyheos import const


@dataclass(frozen=True)
class HeosHost:
    """Represents a HEOS host.

    This class is used to store information about a HEOS host and is not tracked or updated once created.
    """

    name: str
    model: str
    serial: str | None
    version: str
    ip_address: str
    network: str

    @classmethod
    def from_data(cls, data: dict[str, str]) -> "HeosHost":
        """Create a HeosHost object from a dictionary.

        Args:
            data (dict): The dictionary to create the HeosHost object from.

        Returns:
            HeosHost: The created HeosHost object.
        """
        return HeosHost(
            data[const.ATTR_NAME],
            data[const.ATTR_MODEL],
            data.get(const.ATTR_SERIAL),
            data[const.ATTR_VERSION],
            data[const.ATTR_IP_ADDRESS],
            data[const.ATTR_NETWORK],
        )


@dataclass
class HeosSystem:
    """Represents information about a HEOS system.

    This class is used to store information about a HEOS system and is not tracked or updated once created.
    """

    signed_in_username: str | None
    host: HeosHost
    hosts: list[HeosHost]

    @property
    def is_signed_in(self) -> bool:
        """Return whether the system is signed in."""
        return self.signed_in_username is not None

    @cached_property
    def preferred_hosts(self) -> list[HeosHost]:
        """Return the preferred hosts."""
        return list(
            [host for host in self.hosts if host.network == const.NETWORK_TYPE_WIRED]
        )

    @cached_property
    def connected_to_preferred_host(self) -> bool:
        """Return whether the system is connected to a host."""
        return self.host in self.preferred_hosts
