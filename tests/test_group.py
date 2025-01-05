"""Tests for the group module."""

import pytest

from pyheos import const
from pyheos.group import HeosGroup
from pyheos.heos import Heos
from pyheos.message import HeosMessage
from tests import calls_command, value


def test_group_from_data_no_leader_raises() -> None:
    """Test creating a group from data with no leader."""
    data = {
        const.ATTR_NAME: "Test Group",
        const.ATTR_GROUP_ID: "1",
        const.ATTR_PLAYERS: [
            {const.ATTR_PLAYER_ID: "1", const.ATTR_ROLE: const.VALUE_MEMBER},
            {const.ATTR_PLAYER_ID: "2", const.ATTR_ROLE: const.VALUE_MEMBER},
        ],
    }
    with pytest.raises(ValueError, match="No leader found in group data"):
        HeosGroup.from_data(data, None)


@pytest.mark.parametrize(
    ("command", "group_id", "result"),
    [
        (const.EVENT_GROUP_VOLUME_CHANGED, "1", True),
        (const.EVENT_GROUP_VOLUME_CHANGED, "2", False),
        (const.EVENT_PLAYER_VOLUME_CHANGED, "1", False),
    ],
)
async def test_on_event_no_match_returns_false(
    group: HeosGroup, command: str, group_id: str, result: bool
) -> None:
    """Test the set_volume command."""
    event = HeosMessage(
        command,
        message={
            const.ATTR_GROUP_ID: group_id,
            const.ATTR_LEVEL: "10",
            const.ATTR_MUTE: const.VALUE_ON,
        },
    )
    assert result == await group.on_event(event)
    if result:
        assert group.volume == 10
        assert group.is_muted
    else:
        assert group.volume == 0
        assert not group.is_muted


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
