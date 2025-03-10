"""Define the System module."""

from dataclasses import dataclass, field
from ipaddress import IPv4Address, IPv6Address, ip_address
from typing import Any

from pyheos import command as c
from pyheos.common import is_supported_version
from pyheos.types import NetworkType


def _safe_ip_address(
    address: str | None,
) -> tuple[bool, IPv4Address | IPv6Address | None]:
    """Safely parse an IP address."""
    if address is None:
        return True, None
    try:
        return False, ip_address(address)
    except ValueError:
        return True, None


@dataclass(frozen=True)
class HeosHost:
    """Represents a HEOS host.

    This class is used to store information about a HEOS host and is not tracked or updated once created.
    """

    name: str
    model: str
    serial: str | None
    version: str | None
    ip_address: str | None
    network: NetworkType
    supported_version: bool
    preferred_host: bool = field(init=False)

    @staticmethod
    def _from_data(data: dict[str, Any]) -> "HeosHost":
        """Create a HeosHost object from a dictionary.

        Args:
            data (dict): The dictionary to create the HeosHost object from.

        Returns:
            HeosHost: The created HeosHost object.
        """
        version = data.get(c.ATTR_VERSION)
        return HeosHost(
            data[c.ATTR_NAME],
            data[c.ATTR_MODEL],
            data.get(c.ATTR_SERIAL),
            version,
            data.get(c.ATTR_IP_ADDRESS),
            c.parse_enum(c.ATTR_NETWORK, data, NetworkType, NetworkType.UNKNOWN),
            is_supported_version(version),
        )

    def __post_init__(self) -> None:
        """Post initialize the host."""
        object.__setattr__(
            self,
            "preferred_host",
            (
                self.network == NetworkType.WIRED
                and self.supported_version
                and _safe_ip_address(self.ip_address)[1] is not None
            ),
        )


@dataclass
class HeosSystem:
    """Represents information about a HEOS system.

    This class is used to store information about a HEOS system and is not tracked or updated once created.
    """

    signed_in_username: str | None
    host: HeosHost | None
    hosts: list[HeosHost]
    is_signed_in: bool = field(init=False)
    preferred_hosts: list[HeosHost] = field(init=False)
    connected_to_preferred_host: bool = field(init=False)

    def __post_init__(self) -> None:
        """Post initialize the system."""
        self.is_signed_in = self.signed_in_username is not None
        self.preferred_hosts = sorted(
            [host for host in self.hosts if host.preferred_host],
            key=lambda x: (
                x.serial is None,
                x.serial,
                *_safe_ip_address(x.ip_address),
            ),
        )
        self.hosts.sort(
            key=lambda x: (
                x.ip_address is None,
                *_safe_ip_address(x.ip_address),
            )
        )
        self.connected_to_preferred_host = (
            self.host is not None and self.host in self.preferred_hosts
        )

    def get_ip_addresses(self) -> list[str]:
        """Get a list of IP addresses for the hosts."""
        hosts = sorted(
            [host for host in self.hosts if host.ip_address is not None],
            key=lambda x: (x.preferred_host, *_safe_ip_address(x.ip_address)),
        )
        return [host.ip_address for host in hosts]  # type: ignore[misc]
