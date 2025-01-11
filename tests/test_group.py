"""Tests for the group module."""

import pytest

from pyheos import command as c
from pyheos.const import EVENT_GROUP_VOLUME_CHANGED, EVENT_PLAYER_VOLUME_CHANGED
from pyheos.group import HeosGroup
from pyheos.heos import Heos
from pyheos.message import HeosMessage
from tests import CallCommand, calls_command, calls_commands, value


def test_group_from_data_no_leader_raises() -> None:
    """Test creating a group from data with no leader."""
    data = {
        c.ATTR_NAME: "Test Group",
        c.ATTR_GROUP_ID: "1",
        c.ATTR_PLAYERS: [
            {
                c.ATTR_PLAYER_ID: "1",
                c.ATTR_ROLE: c.VALUE_MEMBER,
            },
            {
                c.ATTR_PLAYER_ID: "2",
                c.ATTR_ROLE: c.VALUE_MEMBER,
            },
        ],
    }
    with pytest.raises(ValueError, match="No leader found in group data"):
        HeosGroup._from_data(data, None)


@pytest.mark.parametrize(
    ("command", "group_id", "result"),
    [
        (EVENT_GROUP_VOLUME_CHANGED, "1", True),
        (EVENT_GROUP_VOLUME_CHANGED, "2", False),
        (EVENT_PLAYER_VOLUME_CHANGED, "1", False),
    ],
)
async def test_on_event_no_match_returns_false(
    group: HeosGroup, command: str, group_id: str, result: bool
) -> None:
    """Test the set_volume command."""
    event = HeosMessage(
        command,
        message={
            c.ATTR_GROUP_ID: group_id,
            c.ATTR_LEVEL: "10",
            c.ATTR_MUTE: c.VALUE_ON,
        },
    )
    assert result == await group._on_event(event)
    if result:
        assert group.volume == 10
        assert group.is_muted
    else:
        assert group.volume == 0
        assert not group.is_muted


@calls_command(
    "group.set_volume",
    {c.ATTR_LEVEL: "25", c.ATTR_GROUP_ID: "1"},
)
async def test_set_volume(group: HeosGroup) -> None:
    """Test the set_volume command."""
    await group.set_volume(25)


@pytest.mark.parametrize("volume", [-1, 101])
async def test_set_volume_invalid_raises(group: HeosGroup, volume: int) -> None:
    """Test the set_volume command."""
    with pytest.raises(ValueError):
        await group.set_volume(volume)


@calls_command(
    "group.volume_down",
    {c.ATTR_STEP: "6", c.ATTR_GROUP_ID: "1"},
)
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


@calls_command("group.volume_up", {c.ATTR_STEP: "6", c.ATTR_GROUP_ID: "1"})
async def test_volume_up(group: HeosGroup) -> None:
    """Test the volume_up command."""
    await group.volume_up(6)


@pytest.mark.parametrize("step", [0, 11])
async def test_volume_up_invalid_raises(group: HeosGroup, step: int) -> None:
    """Test the volume_up command."""
    with pytest.raises(ValueError):
        await group.volume_up(step)


@calls_command(
    "group.set_mute",
    {
        c.ATTR_GROUP_ID: "1",
        c.ATTR_STATE: c.VALUE_ON,
    },
)
async def test_mute(group: HeosGroup) -> None:
    """Test mute commands."""
    await group.mute()


@pytest.mark.parametrize("mute", [True, False])
@calls_command(
    "group.set_mute",
    {
        c.ATTR_GROUP_ID: "1",
        c.ATTR_STATE: value(arg_name="mute", formatter="on_off"),
    },
)
async def test_set_mute(group: HeosGroup, mute: bool) -> None:
    """Test mute commands."""
    await group.set_mute(mute)


@calls_command(
    "group.set_mute",
    {
        c.ATTR_GROUP_ID: "1",
        c.ATTR_STATE: c.VALUE_OFF,
    },
)
async def test_unmute(group: HeosGroup) -> None:
    """Test mute commands."""
    await group.unmute()


@calls_command("group.toggle_mute", {c.ATTR_GROUP_ID: "1"})
async def test_toggle_mute(group: HeosGroup) -> None:
    """Test toggle mute command."""
    await group.toggle_mute()


@calls_commands(
    CallCommand("group.get_group_info", {c.ATTR_GROUP_ID: 1}),
    CallCommand("group.get_volume", {c.ATTR_GROUP_ID: -263109739}),
    CallCommand("group.get_mute", {c.ATTR_GROUP_ID: -263109739}),
)
async def test_refresh(group: HeosGroup) -> None:
    """Test refresh, including base, updates the correct information."""
    await group.refresh()

    assert group.name == "Zone 1 + Zone 2"
    assert group.group_id == -263109739
    assert group.lead_player_id == -263109739
    assert group.member_player_ids == [845195621]
    assert group.volume == 42
    assert not group.is_muted


@calls_commands(
    CallCommand("group.get_volume", {c.ATTR_GROUP_ID: 1}),
    CallCommand("group.get_mute", {c.ATTR_GROUP_ID: 1}),
)
async def test_refresh_no_base_update(group: HeosGroup) -> None:
    """Test refresh updates the correct information."""
    await group.refresh(refresh_base_info=False)

    assert group.name == "Back Patio + Front Porch"
    assert group.group_id == 1
    assert group.lead_player_id == 1
    assert group.member_player_ids == [2]
    assert group.volume == 42
    assert not group.is_muted
