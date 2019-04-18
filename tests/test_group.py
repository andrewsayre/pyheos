"""Tests for the group module."""
import pytest

from pyheos import const


@pytest.mark.asyncio
async def test_set_volume_and_mute(mock_device, heos):
    """Test the volume commands."""
    await heos.get_groups()
    group = heos.groups.get(1)

    mock_device.register(const.COMMAND_SET_GROUP_VOLUME, None,
                         'group.set_volume')

    # Volume
    with pytest.raises(ValueError):
        await group.set_volume(-1)
    with pytest.raises(ValueError):
        await group.set_volume(101)
    await group.set_volume(25)
