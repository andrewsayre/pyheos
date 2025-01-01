"""Tests for the group module."""

import pytest

from pyheos import const
from pyheos.heos import Heos
from tests import MockHeosDevice, calls_command


@calls_command("group.set_volume", {const.ATTR_LEVEL: "25", const.ATTR_GROUP_ID: "1"})
async def test_set_volume(heos: Heos) -> None:
    """Test the set_volume command."""
    await heos.get_groups()
    group = heos.groups[1]

    await group.set_volume(25)


@pytest.mark.parametrize("volume", [-1, 101])
async def test_set_volume_invalid_raises(heos: Heos, volume: int) -> None:
    """Test the set_volume command."""
    await heos.get_groups()
    group = heos.groups[1]

    with pytest.raises(ValueError):
        await group.set_volume(volume)


@calls_command("group.volume_down", {const.ATTR_STEP: "6", const.ATTR_GROUP_ID: "1"})
async def test_volume_down(heos: Heos) -> None:
    """Test the volume_down command."""
    await heos.get_groups()
    group = heos.groups[1]

    await group.volume_down(6)


@pytest.mark.parametrize("step", [0, 11])
async def test_volume_down_invalid_raises(heos: Heos, step: int) -> None:
    """Test the volume_down command."""
    await heos.get_groups()
    group = heos.groups[1]

    with pytest.raises(ValueError):
        await group.volume_down(step)


@calls_command("group.volume_up", {const.ATTR_STEP: "6", const.ATTR_GROUP_ID: "1"})
async def test_volume_up(heos: Heos) -> None:
    """Test the volume_up command."""
    await heos.get_groups()
    group = heos.groups[1]

    await group.volume_up(6)


@pytest.mark.parametrize("step", [0, 11])
async def test_volume_up_invalid_raises(heos: Heos, step: int) -> None:
    """Test the volume_up command."""
    await heos.get_groups()
    group = heos.groups[1]

    with pytest.raises(ValueError):
        await group.volume_up(step)


@calls_command(
    "group.set_mute", {const.ATTR_GROUP_ID: "1", const.ATTR_STATE: const.VALUE_ON}
)
async def test_mute(heos: Heos) -> None:
    """Test mute commands."""
    await heos.get_groups()
    group = heos.groups[1]

    await group.mute()


@calls_command(
    "group.set_mute", {const.ATTR_GROUP_ID: "1", const.ATTR_STATE: const.VALUE_OFF}
)
async def test_unmute(heos: Heos) -> None:
    """Test mute commands."""
    await heos.get_groups()
    group = heos.groups[1]

    await group.unmute()


@calls_command("group.toggle_mute", {const.ATTR_GROUP_ID: "1"})
async def test_toggle_mute(heos: Heos) -> None:
    """Test toggle mute command."""
    await heos.get_groups()
    group = heos.groups[1]

    await group.toggle_mute()
