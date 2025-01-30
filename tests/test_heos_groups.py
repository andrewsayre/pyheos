"""Defines a module for heos group related tests."""

import asyncio

from pyheos import command as c
from pyheos.common import ChangeSummary
from pyheos.const import EVENT_GROUPS_CHANGED
from pyheos.heos import Heos
from pyheos.types import SignalType
from tests import MockHeosDevice, calls_group_commands, calls_player_commands


@calls_player_commands()
@calls_group_commands()
async def test_groups_changed_event(mock_device: MockHeosDevice, heos: Heos) -> None:
    """Test groups changed fires dispatcher."""
    groups = await heos.get_groups()
    players = await heos.get_players()
    assert len(groups) == 1
    assert all(player.group_id is not None for player in players.values())
    signal = asyncio.Event()

    async def handler(event: str, data: ChangeSummary) -> None:
        assert event == EVENT_GROUPS_CHANGED
        assert data.removed_ids == [1]
        signal.set()

    heos.dispatcher.connect(SignalType.CONTROLLER_EVENT, handler)

    # Write event through mock device
    commands = [
        mock_device.register(
            c.COMMAND_GET_GROUPS, None, "group.get_groups_changed", replace=True
        ),
        mock_device.register(
            c.COMMAND_GET_PLAYERS, None, "player.get_players_no_groups", replace=True
        ),
    ]
    await mock_device.write_event("event.groups_changed")

    # Wait until the signal is set
    await signal.wait()
    map(lambda c: c.assert_called(), commands)

    updated_groups = await heos.get_groups()
    assert len(updated_groups.keys()) == 1
    assert groups[1] is updated_groups[1]
    assert updated_groups[1].available is False
    assert all(player.group_id is None for player in players.values())


@calls_group_commands()
async def test_groups_changed_event_players_not_loaded(
    mock_device: MockHeosDevice, heos: Heos
) -> None:
    """Test groups changed fires dispatcher and does not load players."""
    groups = await heos.get_groups()
    assert len(groups) == 1
    signal = asyncio.Event()

    async def handler(event: str, data: ChangeSummary) -> None:
        assert event == EVENT_GROUPS_CHANGED
        assert data.removed_ids == []
        assert data.added_ids == []
        signal.set()

    heos.dispatcher.connect(SignalType.CONTROLLER_EVENT, handler)

    await mock_device.write_event("event.groups_changed")

    # Wait until the signal is set
    await signal.wait()
    # get_groups_command.assert_called()
    updated_groups = await heos.get_groups()
    assert len(updated_groups.keys()) == 1
    assert updated_groups[1].available is True
