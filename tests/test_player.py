"""Tests for the player module."""

import re

import pytest

from pyheos import const
from pyheos.media import MediaItem
from pyheos.player import HeosPlayer
from tests import calls_command, value
from tests.common import MediaItems


def test_from_data() -> None:
    """Test the __str__ function."""
    data = {
        const.ATTR_NAME: "Back Patio",
        const.ATTR_PLAYER_ID: 1,
        const.ATTR_MODEL: "HEOS Drive",
        const.ATTR_VERSION: "1.493.180",
        const.ATTR_IP_ADDRESS: "192.168.0.1",
        const.ATTR_NETWORK: const.NETWORK_TYPE_WIRED,
        const.ATTR_LINE_OUT: 1,
        const.ATTR_SERIAL: "1234567890",
    }
    player = HeosPlayer.from_data(data, None)

    assert player.name == "Back Patio"
    assert player.player_id == 1
    assert player.model == "HEOS Drive"
    assert player.version == "1.493.180"
    assert player.ip_address == "192.168.0.1"
    assert player.network == const.NETWORK_TYPE_WIRED
    assert player.line_out == 1
    assert player.serial == "1234567890"


async def test_update_from_data(player: HeosPlayer) -> None:
    """Test the __str__ function."""
    data = {
        const.ATTR_NAME: "Patio",
        const.ATTR_PLAYER_ID: 2,
        const.ATTR_MODEL: "HEOS Drives",
        const.ATTR_VERSION: "2.0.0",
        const.ATTR_IP_ADDRESS: "192.168.0.2",
        const.ATTR_NETWORK: const.NETWORK_TYPE_WIFI,
        const.ATTR_LINE_OUT: "0",
        const.ATTR_SERIAL: "0987654321",
    }
    player.update_from_data(data)

    assert player.name == "Patio"
    assert player.player_id == 2
    assert player.model == "HEOS Drives"
    assert player.version == "2.0.0"
    assert player.ip_address == "192.168.0.2"
    assert player.network == const.NETWORK_TYPE_WIFI
    assert player.line_out == 0
    assert player.serial == "0987654321"


@pytest.mark.parametrize(
    "state", (const.PlayState.PAUSE, const.PlayState.PLAY, const.PlayState.STOP)
)
@calls_command(
    "player.set_play_state",
    {const.ATTR_PLAYER_ID: 1, const.ATTR_STATE: value(arg_name="state")},
)
async def test_set_state(player: HeosPlayer, state: const.PlayState) -> None:
    """Test the play, pause, and stop commands."""
    await player.set_state(state)


@calls_command(
    "player.set_play_state",
    {const.ATTR_PLAYER_ID: 1, const.ATTR_STATE: const.PlayState.PLAY},
)
async def test_set_play(player: HeosPlayer) -> None:
    """Test the pause commands."""
    await player.play()


@calls_command(
    "player.set_play_state",
    {const.ATTR_PLAYER_ID: 1, const.ATTR_STATE: const.PlayState.PAUSE},
)
async def test_set_pause(player: HeosPlayer) -> None:
    """Test the play commands."""
    await player.pause()


@calls_command(
    "player.set_play_state",
    {const.ATTR_PLAYER_ID: 1, const.ATTR_STATE: const.PlayState.STOP},
)
async def test_set_stop(player: HeosPlayer) -> None:
    """Test the stop commands."""
    await player.stop()


@pytest.mark.parametrize("level", [-1, 101])
async def test_set_volume_invalid_raises(player: HeosPlayer, level: int) -> None:
    """Test the set_volume command to an invalid value raises."""
    with pytest.raises(ValueError):
        await player.set_volume(level)


@calls_command("player.set_volume", {const.ATTR_PLAYER_ID: 1, const.ATTR_LEVEL: 100})
async def test_set_volume(player: HeosPlayer) -> None:
    """Test the set_volume command."""
    await player.set_volume(100)


@pytest.mark.parametrize("mute", [True, False])
@calls_command(
    "player.set_mute",
    {
        const.ATTR_PLAYER_ID: 1,
        const.ATTR_STATE: value(arg_name="mute", formatter="on_off"),
    },
)
async def test_set_mute(player: HeosPlayer, mute: bool) -> None:
    """Test the set_mute command."""
    await player.set_mute(mute)


@calls_command(
    "player.set_mute", {const.ATTR_PLAYER_ID: 1, const.ATTR_STATE: const.VALUE_ON}
)
async def test_mute(player: HeosPlayer) -> None:
    """Test the mute command."""
    await player.mute()


@calls_command(
    "player.set_mute", {const.ATTR_PLAYER_ID: 1, const.ATTR_STATE: const.VALUE_OFF}
)
async def test_unmute(player: HeosPlayer) -> None:
    """Test the unmute command."""
    await player.unmute()


@calls_command("player.toggle_mute", {const.ATTR_PLAYER_ID: 1})
async def test_toggle_mute(player: HeosPlayer) -> None:
    """Test the toggle_mute command."""
    await player.toggle_mute()


@pytest.mark.parametrize("step", [0, 11])
async def test_volume_up_invalid_step_raises(player: HeosPlayer, step: int) -> None:
    """Test the volume_up command raises with invalid step value raises."""
    with pytest.raises(ValueError):
        await player.volume_up(step)


@calls_command("player.volume_up", {const.ATTR_PLAYER_ID: 1, const.ATTR_STEP: 6})
async def test_volume_up(player: HeosPlayer) -> None:
    """Test the volume_up command."""
    await player.volume_up(6)


@pytest.mark.parametrize("step", [0, 11])
async def test_volume_down_invalid_step_raises(player: HeosPlayer, step: int) -> None:
    """Test the volume_down command with invalid step value raises."""
    with pytest.raises(ValueError):
        await player.volume_down(step)


@calls_command("player.volume_down", {const.ATTR_PLAYER_ID: 1, const.ATTR_STEP: 6})
async def test_volume_down(player: HeosPlayer) -> None:
    """Test the volume_down command."""
    await player.volume_down(6)


@calls_command(
    "player.set_play_mode",
    {
        const.ATTR_PLAYER_ID: 1,
        const.ATTR_REPEAT: const.RepeatType.ON_ALL,
        const.ATTR_SHUFFLE: const.VALUE_ON,
    },
)
async def test_set_play_mode(player: HeosPlayer) -> None:
    """Test the set play mode command."""
    await player.set_play_mode(const.RepeatType.ON_ALL, True)


@calls_command("player.play_next", {const.ATTR_PLAYER_ID: 1})
async def test_play_next(player: HeosPlayer) -> None:
    """Test the play next command."""
    await player.play_next()


@calls_command("player.play_previous", {const.ATTR_PLAYER_ID: 1})
async def test_play_previous(player: HeosPlayer) -> None:
    """Test the play previous command."""
    await player.play_previous()


@calls_command(
    "player.clear_queue",
    {const.ATTR_PLAYER_ID: 1},
    add_command_under_process=True,
)
async def test_clear_queue(player: HeosPlayer) -> None:
    """Test the clear_queue commands."""
    await player.clear_queue()


@calls_command(
    "browse.play_input",
    {
        const.ATTR_PLAYER_ID: 1,
        const.ATTR_INPUT: const.INPUT_AUX_IN_1,
        const.ATTR_SOURCE_PLAYER_ID: 2,
    },
)
async def test_play_input_source(player: HeosPlayer) -> None:
    """Test the play input source."""
    await player.play_input_source(const.INPUT_AUX_IN_1, 2)


@calls_command("browse.play_preset", {const.ATTR_PLAYER_ID: 1, const.ATTR_PRESET: 1})
async def test_play_preset_station(player: HeosPlayer) -> None:
    """Test the play favorite."""
    await player.play_preset_station(1)


async def test_play_preset_station_invalid_index(player: HeosPlayer) -> None:
    """Test the play favorite."""
    with pytest.raises(ValueError):
        await player.play_preset_station(0)


@calls_command(
    "browse.play_stream",
    {
        const.ATTR_PLAYER_ID: 1,
        const.ATTR_URL: "https://my.website.com/podcast.mp3?patron-auth=qwerty",
    },
)
async def test_play_url(player: HeosPlayer) -> None:
    """Test the play url."""
    await player.play_url("https://my.website.com/podcast.mp3?patron-auth=qwerty")


@pytest.mark.parametrize("quick_select", [0, 7])
async def test_play_quick_select_invalid_raises(
    player: HeosPlayer, quick_select: int
) -> None:
    """Test play invalid quick select raises."""
    with pytest.raises(ValueError):
        await player.play_quick_select(quick_select)


@calls_command("player.play_quickselect", {const.ATTR_PLAYER_ID: 1, const.ATTR_ID: 2})
async def test_play_quick_select(player: HeosPlayer) -> None:
    """Test the play quick select."""
    await player.play_quick_select(2)


@pytest.mark.parametrize("index", [0, 7])
async def test_set_quick_select_invalid_raises(player: HeosPlayer, index: int) -> None:
    """Test set quick select invalid index raises."""
    with pytest.raises(ValueError):
        await player.set_quick_select(index)


@calls_command("player.set_quickselect", {const.ATTR_PLAYER_ID: 1, const.ATTR_ID: 2})
async def test_set_quick_select(player: HeosPlayer) -> None:
    """Test the play favorite."""
    await player.set_quick_select(2)


@calls_command("player.get_quickselects", {const.ATTR_PLAYER_ID: 1})
async def test_get_quick_selects(player: HeosPlayer) -> None:
    """Test the play favorite."""
    selects = await player.get_quick_selects()
    assert selects == {
        1: "Quick Select 1",
        2: "Quick Select 2",
        3: "Quick Select 3",
        4: "Quick Select 4",
        5: "Quick Select 5",
        6: "Quick Select 6",
    }


async def test_play_media_unplayable_source(
    player: HeosPlayer, media_item_album: MediaItem
) -> None:
    """Test play media with unplayable source raises."""
    media_item_album.playable = False
    with pytest.raises(
        ValueError, match=re.escape(f"Media '{media_item_album}' is not playable")
    ):
        await player.play_media(media_item_album, const.AddCriteriaType.PLAY_NOW)


@calls_command(
    "browse.add_to_queue_container",
    {
        const.ATTR_PLAYER_ID: 1,
        const.ATTR_SOURCE_ID: const.MUSIC_SOURCE_PLAYLISTS,
        const.ATTR_CONTAINER_ID: "123",
        const.ATTR_ADD_CRITERIA_ID: const.AddCriteriaType.PLAY_NOW,
    },
    add_command_under_process=True,
)
async def test_play_media_container(
    player: HeosPlayer, media_item_playlist: MediaItem
) -> None:
    """Test adding a container to the queue."""
    await player.play_media(media_item_playlist, const.AddCriteriaType.PLAY_NOW)


@calls_command(
    "browse.add_to_queue_track",
    {
        const.ATTR_PLAYER_ID: 1,
        const.ATTR_SOURCE_ID: MediaItems.SONG.source_id,
        const.ATTR_CONTAINER_ID: MediaItems.SONG.container_id,
        const.ATTR_MEDIA_ID: MediaItems.SONG.media_id,
        const.ATTR_ADD_CRITERIA_ID: const.AddCriteriaType.PLAY_NOW,
    },
    add_command_under_process=True,
)
async def test_play_media_track(player: HeosPlayer, media_item_song: MediaItem) -> None:
    """Test adding a track to the queue."""
    await player.play_media(media_item_song, const.AddCriteriaType.PLAY_NOW)


@calls_command(
    "browse.add_to_queue_track",
    {
        const.ATTR_PLAYER_ID: 1,
        const.ATTR_SOURCE_ID: const.MUSIC_SOURCE_DEEZER,
        const.ATTR_CONTAINER_ID: "123",
        const.ATTR_MEDIA_ID: "456",
        const.ATTR_ADD_CRITERIA_ID: const.AddCriteriaType.PLAY_NOW,
    },
    add_command_under_process=True,
)
async def test_add_to_queue(player: HeosPlayer) -> None:
    """Test adding a track to the queue."""
    await player.add_to_queue(
        const.MUSIC_SOURCE_DEEZER, "123", "456", const.AddCriteriaType.PLAY_NOW
    )


@calls_command("player.get_now_playing_media_blank", {const.ATTR_PLAYER_ID: 1})
async def test_now_playing_media_unavailable(player: HeosPlayer) -> None:
    """Test edge case where now_playing_media returns an empty payload."""
    await player.refresh_now_playing_media()
    assert player.now_playing_media.supported_controls == []
    assert player.now_playing_media.type is None
    assert player.now_playing_media.song is None
    assert player.now_playing_media.station is None
    assert player.now_playing_media.album is None
    assert player.now_playing_media.artist is None
    assert player.now_playing_media.image_url is None
    assert player.now_playing_media.album_id is None
    assert player.now_playing_media.media_id is None
