"""Tests for the group module."""

import pytest

from pyheos import const
from pyheos.group import HeosGroup
from pyheos.heos import Heos
from tests import calls_command, value


@calls_command("group.set_volume", {const.ATTR_LEVEL: "25", const.ATTR_GROUP_ID: "1"})
async def test_set_volume(group: HeosGroup) -> None:
    """Test the set_volume command."""
    await group.set_volume(25)


@pytest.mark.parametrize("volume", [-1, 101])
async def test_set_volume_invalid_raises(group: HeosGroup, volume: int) -> None:
    """Test the set_volume command."""
    with pytest.raises(ValueError):
        await group.set_volume(volume)


@calls_command("group.volume_down", {const.ATTR_STEP: "6", const.ATTR_GROUP_ID: "1"})
async def test_volume_down(group: HeosGroup) -> None:
    """Test the volume_down command."""
    await group.volume_down(6)


@pytest.mark.parametrize("step", [0, 11])
async def test_volume_down_invalid_raises(
    group: HeosGroup, heos: Heos, step: int
) -> None:
    """Test the volume_down command."""
    with pytest.raises(ValueError):
        await group.volume_down(step)


@calls_command("group.volume_up", {const.ATTR_STEP: "6", const.ATTR_GROUP_ID: "1"})
async def test_volume_up(group: HeosGroup) -> None:
    """Test the volume_up command."""
    await group.volume_up(6)


@pytest.mark.parametrize("step", [0, 11])
async def test_volume_up_invalid_raises(group: HeosGroup, step: int) -> None:
    """Test the volume_up command."""
    with pytest.raises(ValueError):
        await group.volume_up(step)


@calls_command(
    "group.set_mute", {const.ATTR_GROUP_ID: "1", const.ATTR_STATE: const.VALUE_ON}
)
async def test_mute(group: HeosGroup) -> None:
    """Test mute commands."""
    await group.mute()


@pytest.mark.parametrize("mute", [True, False])
@calls_command(
    "group.set_mute",
    {
        const.ATTR_GROUP_ID: "1",
        const.ATTR_STATE: value(arg_name="mute", formatter="on_off"),
    },
)
async def test_set_mute(group: HeosGroup, mute: bool) -> None:
    """Test mute commands."""
    await group.set_mute(mute)


@calls_command(
    "group.set_mute", {const.ATTR_GROUP_ID: "1", const.ATTR_STATE: const.VALUE_OFF}
)
async def test_unmute(group: HeosGroup) -> None:
    """Test mute commands."""
    await group.unmute()


@calls_command("group.toggle_mute", {const.ATTR_GROUP_ID: "1"})
async def test_toggle_mute(group: HeosGroup) -> None:
    """Test toggle mute command."""
    await group.toggle_mute()
