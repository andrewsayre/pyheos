"""Tests for the player module."""

import re

import pytest

from pyheos import command as c
from pyheos.const import (
    INPUT_AUX_IN_1,
    MUSIC_SOURCE_DEEZER,
    MUSIC_SOURCE_PLAYLISTS,
    MUSIC_SOURCE_TIDAL,
    SEARCHED_TRACKS,
)
from pyheos.media import MediaItem
from pyheos.player import HeosPlayer
from pyheos.types import (
    AddCriteriaType,
    LineOutLevelType,
    NetworkType,
    PlayState,
    RepeatType,
)
from tests import CallCommand, calls_command, calls_commands, value
from tests.common import MediaItems


@pytest.mark.parametrize(
    ("network", "expected_network"),
    [
        (None, NetworkType.UNKNOWN),
        ("wired", NetworkType.WIRED),
        ("invalid", NetworkType.UNKNOWN),  # Invalid network type
    ],
)
def test_from_data(network: str | None, expected_network: NetworkType) -> None:
    """Test the from_data function."""
    data = {
        c.ATTR_NAME: "Back Patio",
        c.ATTR_PLAYER_ID: 1,
        c.ATTR_MODEL: "HEOS Drive",
        c.ATTR_VERSION: "1.493.180",
        c.ATTR_IP_ADDRESS: "192.168.0.1",
        c.ATTR_NETWORK: network,
        c.ATTR_LINE_OUT: 1,
        c.ATTR_SERIAL: "1234567890",
    }
    player = HeosPlayer._from_data(data, None)

    assert player.name == "Back Patio"
    assert player.player_id == 1
    assert player.model == "HEOS Drive"
    assert player.version == "1.493.180"
    assert player.ip_address == "192.168.0.1"
    assert player.network == expected_network
    assert player.line_out == LineOutLevelType.VARIABLE
    assert player.serial == "1234567890"


async def test_update_from_data(player: HeosPlayer) -> None:
    """Test the __str__ function."""
    data = {
        c.ATTR_NAME: "Patio",
        c.ATTR_PLAYER_ID: 2,
        c.ATTR_MODEL: "HEOS Drives",
        c.ATTR_VERSION: "2.0.0",
        c.ATTR_IP_ADDRESS: "192.168.0.2",
        c.ATTR_NETWORK: "wifi",
        c.ATTR_LINE_OUT: "0",
        c.ATTR_SERIAL: "0987654321",
    }
    player._update_from_data(data)

    assert player.name == "Patio"
    assert player.player_id == 2
    assert player.model == "HEOS Drives"
    assert player.version == "2.0.0"
    assert player.ip_address == "192.168.0.2"
    assert player.network == NetworkType.WIFI
    assert player.line_out == LineOutLevelType.UNKNOWN
    assert player.serial == "0987654321"


@pytest.mark.parametrize("state", (PlayState.PAUSE, PlayState.PLAY, PlayState.STOP))
@calls_command(
    "player.set_play_state",
    {c.ATTR_PLAYER_ID: 1, c.ATTR_STATE: value(arg_name="state")},
)
async def test_set_state(player: HeosPlayer, state: PlayState) -> None:
    """Test the play, pause, and stop commands."""
    await player.set_state(state)


@calls_command(
    "player.set_play_state",
    {c.ATTR_PLAYER_ID: 1, c.ATTR_STATE: PlayState.PLAY},
)
async def test_set_play(player: HeosPlayer) -> None:
    """Test the pause commands."""
    await player.play()


@calls_command(
    "player.set_play_state",
    {c.ATTR_PLAYER_ID: 1, c.ATTR_STATE: PlayState.PAUSE},
)
async def test_set_pause(player: HeosPlayer) -> None:
    """Test the play commands."""
    await player.pause()


@calls_command(
    "player.set_play_state",
    {c.ATTR_PLAYER_ID: 1, c.ATTR_STATE: PlayState.STOP},
)
async def test_set_stop(player: HeosPlayer) -> None:
    """Test the stop commands."""
    await player.stop()


@pytest.mark.parametrize("level", [-1, 101])
async def test_set_volume_invalid_raises(player: HeosPlayer, level: int) -> None:
    """Test the set_volume command to an invalid value raises."""
    with pytest.raises(ValueError):
        await player.set_volume(level)


@calls_command("player.set_volume", {c.ATTR_PLAYER_ID: 1, c.ATTR_LEVEL: 100})
async def test_set_volume(player: HeosPlayer) -> None:
    """Test the set_volume c."""
    await player.set_volume(100)


@pytest.mark.parametrize("mute", [True, False])
@calls_command(
    "player.set_mute",
    {
        c.ATTR_PLAYER_ID: 1,
        c.ATTR_STATE: value(arg_name="mute", formatter="on_off"),
    },
)
async def test_set_mute(player: HeosPlayer, mute: bool) -> None:
    """Test the set_mute c."""
    await player.set_mute(mute)


@calls_command("player.set_mute", {c.ATTR_PLAYER_ID: 1, c.ATTR_STATE: c.VALUE_ON})
async def test_mute(player: HeosPlayer) -> None:
    """Test the mute c."""
    await player.mute()


@calls_command(
    "player.set_mute",
    {c.ATTR_PLAYER_ID: 1, c.ATTR_STATE: c.VALUE_OFF},
)
async def test_unmute(player: HeosPlayer) -> None:
    """Test the unmute c."""
    await player.unmute()


@calls_command("player.toggle_mute", {c.ATTR_PLAYER_ID: 1})
async def test_toggle_mute(player: HeosPlayer) -> None:
    """Test the toggle_mute c."""
    await player.toggle_mute()


@pytest.mark.parametrize("step", [0, 11])
async def test_volume_up_invalid_step_raises(player: HeosPlayer, step: int) -> None:
    """Test the volume_up command raises with invalid step value raises."""
    with pytest.raises(ValueError):
        await player.volume_up(step)


@calls_command("player.volume_up", {c.ATTR_PLAYER_ID: 1, c.ATTR_STEP: 6})
async def test_volume_up(player: HeosPlayer) -> None:
    """Test the volume_up c."""
    await player.volume_up(6)


@pytest.mark.parametrize("step", [0, 11])
async def test_volume_down_invalid_step_raises(player: HeosPlayer, step: int) -> None:
    """Test the volume_down command with invalid step value raises."""
    with pytest.raises(ValueError):
        await player.volume_down(step)


@calls_command("player.volume_down", {c.ATTR_PLAYER_ID: 1, c.ATTR_STEP: 6})
async def test_volume_down(player: HeosPlayer) -> None:
    """Test the volume_down c."""
    await player.volume_down(6)


@calls_command(
    "player.set_play_mode",
    {
        c.ATTR_PLAYER_ID: 1,
        c.ATTR_REPEAT: RepeatType.ON_ALL,
        c.ATTR_SHUFFLE: c.VALUE_ON,
    },
)
async def test_set_play_mode(player: HeosPlayer) -> None:
    """Test the set play mode c."""
    await player.set_play_mode(RepeatType.ON_ALL, True)


@calls_command("player.play_next", {c.ATTR_PLAYER_ID: 1})
async def test_play_next(player: HeosPlayer) -> None:
    """Test the play next c."""
    await player.play_next()


@calls_command("player.play_previous", {c.ATTR_PLAYER_ID: 1})
async def test_play_previous(player: HeosPlayer) -> None:
    """Test the play previous c."""
    await player.play_previous()


@calls_command(
    "player.clear_queue",
    {c.ATTR_PLAYER_ID: 1},
    add_command_under_process=True,
)
async def test_clear_queue(player: HeosPlayer) -> None:
    """Test the clear_queue commands."""
    await player.clear_queue()


@calls_command("player.get_queue", {c.ATTR_PLAYER_ID: 1})
async def test_get_queue(player: HeosPlayer) -> None:
    """Test the get queue c."""
    result = await player.get_queue()

    assert len(result) == 11
    item = result[0]
    assert item.song == "Baby"
    assert item.album == "22 Break"
    assert item.artist == "Oh Wonder"
    assert (
        item.image_url
        == "http://resources.wimpmusic.com/images/bdfd93c2/0b3a/495e/a557/4493fcbb7ab3/640x640.jpg"
    )
    assert item.queue_id == 1
    assert item.media_id == "199555606"
    assert item.album_id == "199555605"


@calls_command("player.play_queue", {c.ATTR_PLAYER_ID: 1, c.ATTR_QUEUE_ID: 1})
async def test_play_queue(player: HeosPlayer) -> None:
    """Test the play_queue c."""
    await player.play_queue(1)


@calls_command(
    "player.remove_from_queue",
    {c.ATTR_PLAYER_ID: 1, c.ATTR_QUEUE_ID: "1,2,3"},
)
async def test_remove_from_queue(player: HeosPlayer) -> None:
    """Test the play_queue c."""
    await player.remove_from_queue([1, 2, 3])


@calls_command("player.save_queue", {c.ATTR_PLAYER_ID: 1, c.ATTR_NAME: "Test"})
async def test_save_queue(player: HeosPlayer) -> None:
    """Test the save_queue c."""
    await player.save_queue("Test")


async def test_save_queue_too_long_raises(player: HeosPlayer) -> None:
    """Test the save_queue c."""
    with pytest.raises(
        ValueError, match="'name' must be less than or equal to 128 characters"
    ):
        await player.save_queue("S" * 129)


@calls_command(
    "player.move_queue_item",
    {
        c.ATTR_PLAYER_ID: 1,
        c.ATTR_SOURCE_QUEUE_ID: "2,3,4",
        c.ATTR_DESTINATION_QUEUE_ID: 1,
    },
)
async def test_move_queue_item(player: HeosPlayer) -> None:
    """Test the move_queue_item c."""
    await player.move_queue_item([2, 3, 4], 1)


@calls_command("player.get_queue", {c.ATTR_PLAYER_ID: 1, c.ATTR_RANGE: "0,10"})
async def test_get_queue_with_range(player: HeosPlayer) -> None:
    """Test the check_update c."""
    result = await player.get_queue(0, 10)

    assert len(result) == 11
    item = result[0]
    assert item.song == "Baby"
    assert item.album == "22 Break"
    assert item.artist == "Oh Wonder"
    assert (
        item.image_url
        == "http://resources.wimpmusic.com/images/bdfd93c2/0b3a/495e/a557/4493fcbb7ab3/640x640.jpg"
    )
    assert item.queue_id == 1
    assert item.media_id == "199555606"
    assert item.album_id == "199555605"


@calls_command(
    "browse.play_input",
    {
        c.ATTR_PLAYER_ID: 1,
        c.ATTR_INPUT: INPUT_AUX_IN_1,
        c.ATTR_SOURCE_PLAYER_ID: 2,
    },
)
async def test_play_input_source(player: HeosPlayer) -> None:
    """Test the play input source."""
    await player.play_input_source(INPUT_AUX_IN_1, 2)


@calls_command("browse.play_preset", {c.ATTR_PLAYER_ID: 1, c.ATTR_PRESET: 1})
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
        c.ATTR_PLAYER_ID: 1,
        c.ATTR_URL: "https://my.website.com/podcast.mp3?patron-auth=qwerty",
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


@calls_command("player.play_quickselect", {c.ATTR_PLAYER_ID: 1, c.ATTR_ID: 2})
async def test_play_quick_select(player: HeosPlayer) -> None:
    """Test the play quick select."""
    await player.play_quick_select(2)


@pytest.mark.parametrize("index", [0, 7])
async def test_set_quick_select_invalid_raises(player: HeosPlayer, index: int) -> None:
    """Test set quick select invalid index raises."""
    with pytest.raises(ValueError):
        await player.set_quick_select(index)


@calls_command("player.set_quickselect", {c.ATTR_PLAYER_ID: 1, c.ATTR_ID: 2})
async def test_set_quick_select(player: HeosPlayer) -> None:
    """Test the play favorite."""
    await player.set_quick_select(2)


@calls_command("player.get_quickselects", {c.ATTR_PLAYER_ID: 1})
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
        await player.play_media(media_item_album, AddCriteriaType.PLAY_NOW)


@calls_command(
    "browse.add_to_queue_container",
    {
        c.ATTR_PLAYER_ID: 1,
        c.ATTR_SOURCE_ID: MUSIC_SOURCE_PLAYLISTS,
        c.ATTR_CONTAINER_ID: "123",
        c.ATTR_ADD_CRITERIA_ID: AddCriteriaType.PLAY_NOW,
    },
    add_command_under_process=True,
)
async def test_play_media_container(
    player: HeosPlayer, media_item_playlist: MediaItem
) -> None:
    """Test adding a container to the queue."""
    await player.play_media(media_item_playlist, AddCriteriaType.PLAY_NOW)


@calls_command(
    "browse.add_to_queue_track",
    {
        c.ATTR_PLAYER_ID: 1,
        c.ATTR_SOURCE_ID: MediaItems.SONG.source_id,
        c.ATTR_CONTAINER_ID: MediaItems.SONG.container_id,
        c.ATTR_MEDIA_ID: MediaItems.SONG.media_id,
        c.ATTR_ADD_CRITERIA_ID: AddCriteriaType.PLAY_NOW,
    },
    add_command_under_process=True,
)
async def test_play_media_track(player: HeosPlayer, media_item_song: MediaItem) -> None:
    """Test adding a track to the queue."""
    await player.play_media(media_item_song, AddCriteriaType.PLAY_NOW)


@calls_command(
    "browse.add_to_queue_track",
    {
        c.ATTR_PLAYER_ID: 1,
        c.ATTR_SOURCE_ID: MUSIC_SOURCE_DEEZER,
        c.ATTR_CONTAINER_ID: "123",
        c.ATTR_MEDIA_ID: "456",
        c.ATTR_ADD_CRITERIA_ID: AddCriteriaType.PLAY_NOW,
    },
    add_command_under_process=True,
)
async def test_add_to_queue(player: HeosPlayer) -> None:
    """Test adding a track to the queue."""
    await player.add_to_queue(
        MUSIC_SOURCE_DEEZER, "123", "456", AddCriteriaType.PLAY_NOW
    )


@calls_command(
    "browse.add_to_queue_search",
    {
        c.ATTR_PLAYER_ID: 1,
        c.ATTR_SOURCE_ID: MUSIC_SOURCE_TIDAL,
        c.ATTR_CONTAINER_ID: SEARCHED_TRACKS + "Tangerine Rays",
        c.ATTR_ADD_CRITERIA_ID: AddCriteriaType.PLAY_NOW,
    },
    add_command_under_process=True,
)
async def test_add_search_to_queue(player: HeosPlayer) -> None:
    """Test adding a track to the queue."""
    await player.add_search_to_queue(MUSIC_SOURCE_TIDAL, "Tangerine Rays")


@calls_command("player.get_now_playing_media_blank", {c.ATTR_PLAYER_ID: 1})
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
    assert player.now_playing_media.options == []


@calls_commands(
    CallCommand("player.get_player_info", {c.ATTR_PLAYER_ID: 1}),
    CallCommand("player.get_play_state", {c.ATTR_PLAYER_ID: -263109739}),
    CallCommand("player.get_now_playing_media", {c.ATTR_PLAYER_ID: -263109739}),
    CallCommand("player.get_volume", {c.ATTR_PLAYER_ID: -263109739}),
    CallCommand("player.get_mute", {c.ATTR_PLAYER_ID: -263109739}),
    CallCommand("player.get_play_mode", {c.ATTR_PLAYER_ID: -263109739}),
)
async def test_refresh(player: HeosPlayer) -> None:
    """Test refresh, including base, updates the correct information."""
    await player.refresh()

    assert player.name == "Zone 1"
    assert player.player_id == -263109739
    assert player.model == "HEOS Drive"
    assert player.version == "3.34.620"
    assert player.ip_address == "127.0.0.1"
    assert player.serial == "123456789"


@calls_commands(
    CallCommand("player.get_play_state", {c.ATTR_PLAYER_ID: 1}),
    CallCommand("player.get_now_playing_media", {c.ATTR_PLAYER_ID: 1}),
    CallCommand("player.get_volume", {c.ATTR_PLAYER_ID: 1}),
    CallCommand("player.get_mute", {c.ATTR_PLAYER_ID: 1}),
    CallCommand("player.get_play_mode", {c.ATTR_PLAYER_ID: 1}),
)
async def test_refresh_no_base_update(player: HeosPlayer) -> None:
    """Test refresh updates the correct information."""
    await player.refresh(refresh_base_info=False)

    assert player.name == "Back Patio"
    assert player.player_id == 1


@calls_command("player.check_update", {c.ATTR_PLAYER_ID: 1})
async def test_check_update(player: HeosPlayer) -> None:
    """Test the check_update c."""
    result = await player.check_update()
    assert result
