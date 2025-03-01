"""Tests for the system module."""

import itertools

from syrupy.assertion import SnapshotAssertion

from pyheos.system import HeosHost, HeosSystem
from pyheos.types import NetworkType


def test_system_preferred_hosts(snapshot: SnapshotAssertion) -> None:
    """Test the preferred hosts property."""
    serials = ["serial", None]
    ip_address = [True, False]
    network = [NetworkType.WIRED, NetworkType.WIFI]
    supported = [True, False]

    hosts: list[HeosHost] = []
    for index, item in enumerate(
        list(itertools.product(serials, ip_address, network, supported))
    ):
        hosts.insert(
            0,
            HeosHost(
                f"name{index}",
                "model",
                item[0],
                "1.0.0",
                f"127.0.0.{index}" if item[1] else None,
                item[2],
                item[3],
            ),
        )

    system = HeosSystem("username", hosts[0], hosts)

    assert system == snapshot


def test_system_preferred_hosts_with_invalid(snapshot: SnapshotAssertion) -> None:
    """Test the preferred hosts property with an invalid ip address."""
    network = [NetworkType.WIRED, NetworkType.WIFI]
    hosts: list[HeosHost] = []
    for index, item in enumerate(network):
        hosts.insert(
            0,
            HeosHost(f"name{index}", "model", None, "1.0.0", "invalid", item, True),
        )
    system = HeosSystem("username", hosts[0], hosts)

    assert system == snapshot
