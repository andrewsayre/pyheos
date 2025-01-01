"""Tests for the group module."""

import pytest

from pyheos import const
from pyheos.heos import Heos
from tests import MockHeosDevice


async def test_set_volume(mock_device: MockHeosDevice, heos: Heos) -> None:
    """Test the set_volume command."""
    await heos.get_groups()
    group = heos.groups[1]
    mock_device.register(
        const.COMMAND_SET_GROUP_VOLUME,
        {const.ATTR_LEVEL: "25", const.ATTR_GROUP_ID: "1"},
        "group.set_volume",
    )
    with pytest.raises(ValueError):
        await group.set_volume(-1)
    with pytest.raises(ValueError):
        await group.set_volume(101)
    await group.set_volume(25)


async def test_volume_down(mock_device: MockHeosDevice, heos: Heos) -> None:
    """Test the volume_down command."""
    await heos.get_groups()
    group = heos.groups[1]
    mock_device.register(
        const.COMMAND_GROUP_VOLUME_DOWN,
        {const.ATTR_STEP: "6", const.ATTR_GROUP_ID: "1"},
        "group.volume_down",
    )

    with pytest.raises(ValueError):
        await group.volume_down(0)
    with pytest.raises(ValueError):
        await group.volume_down(11)
    await group.volume_down(6)


async def test_volume_up(mock_device: MockHeosDevice, heos: Heos) -> None:
    """Test the volume_up command."""
    await heos.get_groups()
    group = heos.groups[1]
    mock_device.register(
        const.COMMAND_GROUP_VOLUME_UP,
        {const.ATTR_STEP: "6", const.ATTR_GROUP_ID: "1"},
        "group.volume_up",
    )
    with pytest.raises(ValueError):
        await group.volume_up(0)
    with pytest.raises(ValueError):
        await group.volume_up(11)
    await group.volume_up(6)


async def test_set_mute(mock_device: MockHeosDevice, heos: Heos) -> None:
    """Test mute and unmute commands."""
    await heos.get_groups()
    group = heos.groups[1]

    mock_device.register(
        const.COMMAND_SET_GROUP_MUTE,
        {const.ATTR_GROUP_ID: "1", const.ATTR_STATE: const.VALUE_ON},
        "group.set_mute",
    )
    await group.mute()

    mock_device.register(
        const.COMMAND_SET_GROUP_MUTE,
        {const.ATTR_GROUP_ID: "1", const.ATTR_STATE: const.VALUE_OFF},
        "group.set_mute",
        replace=True,
    )
    await group.unmute()


async def test_toggle_mute(mock_device: MockHeosDevice, heos: Heos) -> None:
    """Test toggle mute command."""
    await heos.get_groups()
    group = heos.groups[1]
    mock_device.register(
        const.COMMAND_GROUP_TOGGLE_MUTE, {const.ATTR_GROUP_ID: "1"}, "group.toggle_mute"
    )
    await group.toggle_mute()
