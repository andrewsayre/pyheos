"""Tests for the group module."""
import pytest

from pyheos import const


@pytest.mark.asyncio
async def test_set_volume_and_mute(mock_device, heos):
    """Test the volume commands."""
    await heos.get_groups()
    group = heos.groups.get(1)

    mock_device.register(const.COMMAND_SET_GROUP_VOLUME, {'level': '25'},
                         'group.set_volume')
    mock_device.register(const.COMMAND_GROUP_VOLUME_DOWN, {'step': '6'},
                         'group.volume_down')
    mock_device.register(const.COMMAND_GROUP_VOLUME_UP, {'step': '6'},
                         'group.volume_up')

    # Volume
    with pytest.raises(ValueError):
        await group.set_volume(-1)
    with pytest.raises(ValueError):
        await group.set_volume(101)
    await group.set_volume(25)

    # Up
    with pytest.raises(ValueError):
        await group.volume_up(0)
    with pytest.raises(ValueError):
        await group.volume_up(11)
    await group.volume_up(6)

    # Down
    with pytest.raises(ValueError):
        await group.volume_down(0)
    with pytest.raises(ValueError):
        await group.volume_down(11)
    await group.volume_down(6)
