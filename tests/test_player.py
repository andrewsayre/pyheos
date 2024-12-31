"""Tests for the player module."""

import re

import pytest

from pyheos import const
from pyheos.heos import Heos, HeosOptions
from pyheos.media import MediaItem
from pyheos.player import HeosPlayer
from tests import MockHeosDevice


@pytest.mark.asyncio
async def test_str() -> None:
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
    player = HeosPlayer(Heos(HeosOptions("None")), data)
    assert str(player) == "{Back Patio (HEOS Drive)}"
    assert repr(player) == "{Back Patio (HEOS Drive) with id 1 at 192.168.0.1}"


@pytest.mark.asyncio
async def test_set_state(mock_device: MockHeosDevice, heos: Heos) -> None:
    """Test the play, pause, and stop commands."""

    await heos.get_players()
    player = heos.players[1]
    # Invalid
    with pytest.raises(ValueError):
        await player.set_state("invalid")
    # Play
    mock_device.register(
        const.COMMAND_SET_PLAY_STATE,
        {const.ATTR_PLAYER_ID: "1", const.ATTR_STATE: "play"},
        "player.set_play_state",
    )
    await player.play()
    # Pause
    mock_device.register(
        const.COMMAND_SET_PLAY_STATE,
        {const.ATTR_PLAYER_ID: "1", const.ATTR_STATE: "pause"},
        "player.set_play_state",
        replace=True,
    )
    await player.pause()
    # Stop
    mock_device.register(
        const.COMMAND_SET_PLAY_STATE,
        {const.ATTR_PLAYER_ID: "1", const.ATTR_STATE: "stop"},
        "player.set_play_state",
        replace=True,
    )
    await player.stop()


@pytest.mark.asyncio
async def test_set_volume(mock_device: MockHeosDevice, heos: Heos) -> None:
    """Test the set_volume command."""
    await heos.get_players()
    player = heos.players[1]

    with pytest.raises(ValueError):
        await player.set_volume(-1)
    with pytest.raises(ValueError):
        await player.set_volume(101)

    mock_device.register(
        const.COMMAND_SET_VOLUME,
        {const.ATTR_PLAYER_ID: "1", const.ATTR_LEVEL: "100"},
        "player.set_volume",
    )
    await player.set_volume(100)


@pytest.mark.asyncio
async def test_set_mute(mock_device: MockHeosDevice, heos: Heos) -> None:
    """Test the set_mute command."""
    await heos.get_players()
    player = heos.players[1]
    # Mute
    mock_device.register(
        const.COMMAND_SET_MUTE,
        {const.ATTR_PLAYER_ID: "1", const.ATTR_STATE: const.VALUE_ON},
        "player.set_mute",
    )
    await player.mute()
    # Unmute
    mock_device.register(
        const.COMMAND_SET_MUTE,
        {const.ATTR_PLAYER_ID: "1", const.ATTR_STATE: const.VALUE_OFF},
        "player.set_mute",
        replace=True,
    )
    await player.unmute()


@pytest.mark.asyncio
async def test_toggle_mute(mock_device: MockHeosDevice, heos: Heos) -> None:
    """Test the toggle_mute command."""
    await heos.get_players()
    player = heos.players[1]
    mock_device.register(
        const.COMMAND_TOGGLE_MUTE, {const.ATTR_PLAYER_ID: "1"}, "player.toggle_mute"
    )
    await player.toggle_mute()


@pytest.mark.asyncio
async def test_volume_up(mock_device: MockHeosDevice, heos: Heos) -> None:
    """Test the volume_up command."""
    await heos.get_players()
    player = heos.players[1]
    with pytest.raises(ValueError):
        await player.volume_up(0)
    with pytest.raises(ValueError):
        await player.volume_up(11)
    mock_device.register(
        const.COMMAND_VOLUME_UP,
        {const.ATTR_PLAYER_ID: "1", const.ATTR_STEP: "6"},
        "player.volume_up",
    )
    await player.volume_up(6)


@pytest.mark.asyncio
async def test_volume_down(mock_device: MockHeosDevice, heos: Heos) -> None:
    """Test the volume_down command."""
    await heos.get_players()
    player = heos.players[1]
    with pytest.raises(ValueError):
        await player.volume_down(0)
    with pytest.raises(ValueError):
        await player.volume_down(11)
    mock_device.register(
        const.COMMAND_VOLUME_DOWN,
        {const.ATTR_PLAYER_ID: "1", const.ATTR_STEP: "6"},
        "player.volume_down",
    )
    await player.volume_down(6)


@pytest.mark.asyncio
async def test_set_play_mode(mock_device: MockHeosDevice, heos: Heos) -> None:
    """Test the volume commands."""
    await heos.get_players()
    player = heos.players[1]
    args = {
        const.ATTR_PLAYER_ID: "1",
        const.ATTR_REPEAT: const.RepeatType.ON_ALL,
        const.ATTR_SHUFFLE: const.VALUE_ON,
    }
    mock_device.register(const.COMMAND_SET_PLAY_MODE, args, "player.set_play_mode")

    await player.set_play_mode(const.RepeatType.ON_ALL, True)


@pytest.mark.asyncio
async def test_play_next_previous(mock_device: MockHeosDevice, heos: Heos) -> None:
    """Test the volume commands."""
    await heos.get_players()
    player = heos.players[1]
    args = {const.ATTR_PLAYER_ID: "1"}
    # Next
    mock_device.register(const.COMMAND_PLAY_NEXT, args, "player.play_next")
    await player.play_next()
    # Previous
    mock_device.register(const.COMMAND_PLAY_PREVIOUS, args, "player.play_previous")
    await player.play_previous()


@pytest.mark.asyncio
async def test_clear_queue(mock_device: MockHeosDevice, heos: Heos) -> None:
    """Test the volume commands."""
    await heos.get_players()
    player = heos.players[1]
    args = {const.ATTR_PLAYER_ID: "1"}
    mock_device.register(const.COMMAND_CLEAR_QUEUE, args, "player.clear_queue")
    await player.clear_queue()

    # Also test with a 'command under process' response
    mock_device.register(
        const.COMMAND_CLEAR_QUEUE,
        args,
        ["player.clear_queue", "player.clear_queue_processing"],
        replace=True,
    )
    await player.clear_queue()


@pytest.mark.asyncio
async def test_play_input_source(
    mock_device: MockHeosDevice, heos: Heos, media_item_input: MediaItem
) -> None:
    """Test the play input source."""
    await heos.get_players()
    player = heos.players[1]

    mock_device.register(
        const.COMMAND_BROWSE_PLAY_INPUT,
        {
            const.ATTR_PLAYER_ID: "1",
            const.ATTR_INPUT: const.INPUT_AUX_IN_1,
            const.ATTR_SOURCE_PLAYER_ID: media_item_input.source_id,
        },
        "browse.play_input",
    )
    assert media_item_input.media_id is not None

    await player.play_input_source(
        media_item_input.media_id, media_item_input.source_id
    )


@pytest.mark.asyncio
async def test_play_preset_station(mock_device: MockHeosDevice, heos: Heos) -> None:
    """Test the play favorite."""
    await heos.get_players()
    player = heos.players[1]

    # Test invalid starting index
    with pytest.raises(ValueError):
        await player.play_preset_station(0)

    args = {const.ATTR_PLAYER_ID: "1", const.ATTR_PRESET: "1"}
    mock_device.register(const.COMMAND_BROWSE_PLAY_PRESET, args, "browse.play_preset")

    await player.play_preset_station(1)


@pytest.mark.asyncio
async def test_play_url(mock_device: MockHeosDevice, heos: Heos) -> None:
    """Test the play favorite."""
    await heos.get_players()
    player = heos.players[1]
    url = "https://my.website.com/podcast.mp3"
    args = {const.ATTR_PLAYER_ID: "1", const.ATTR_URL: url}
    mock_device.register(const.COMMAND_BROWSE_PLAY_STREAM, args, "browse.play_stream")

    await player.play_url(url)


@pytest.mark.asyncio
async def test_play_quick_select(mock_device: MockHeosDevice, heos: Heos) -> None:
    """Test the play favorite."""
    await heos.get_players()
    player = heos.players[1]

    with pytest.raises(ValueError):
        await player.play_quick_select(0)
    with pytest.raises(ValueError):
        await player.play_quick_select(7)

    args = {const.ATTR_PLAYER_ID: "1", const.ATTR_ID: "2"}
    mock_device.register(
        const.COMMAND_PLAY_QUICK_SELECT, args, "player.play_quickselect"
    )
    await player.play_quick_select(2)


@pytest.mark.asyncio
async def test_set_quick_select(mock_device: MockHeosDevice, heos: Heos) -> None:
    """Test the play favorite."""
    await heos.get_players()
    player = heos.players[1]

    with pytest.raises(ValueError):
        await player.set_quick_select(0)
    with pytest.raises(ValueError):
        await player.set_quick_select(7)

    args = {const.ATTR_PLAYER_ID: "1", const.ATTR_ID: "2"}
    mock_device.register(const.COMMAND_SET_QUICK_SELECT, args, "player.set_quickselect")
    await player.set_quick_select(2)


@pytest.mark.asyncio
async def test_get_quick_selects(mock_device: MockHeosDevice, heos: Heos) -> None:
    """Test the play favorite."""
    await heos.get_players()
    player = heos.players[1]
    args = {const.ATTR_PLAYER_ID: "1"}
    mock_device.register(
        const.COMMAND_GET_QUICK_SELECTS, args, "player.get_quickselects"
    )
    selects = await player.get_quick_selects()
    assert selects == {
        1: "Quick Select 1",
        2: "Quick Select 2",
        3: "Quick Select 3",
        4: "Quick Select 4",
        5: "Quick Select 5",
        6: "Quick Select 6",
    }


@pytest.mark.asyncio
async def test_play_media_unplayable_source(
    mock_device: MockHeosDevice, heos: Heos, media_item_album: MediaItem
) -> None:
    """Test add to queue with unplayable source raises."""
    media_item_album.playable = False
    await heos.get_players()
    player = heos.players[1]

    with pytest.raises(
        ValueError, match=re.escape(f"Media '{media_item_album}' is not playable")
    ):
        await player.play_media(media_item_album, const.AddCriteriaType.PLAY_NOW)


@pytest.mark.asyncio
async def test_play_media_container(mock_device: MockHeosDevice, heos: Heos) -> None:
    """Test adding a container to the queue."""
    await heos.get_players()
    player = heos.players[1]
    source = MediaItem.from_data(
        {
            const.ATTR_NAME: "My Playlist",
            const.ATTR_TYPE: const.MediaType.PLAYLIST,
            const.ATTR_IMAGE_URL: "",
            const.ATTR_PLAYABLE: const.VALUE_YES,
            const.ATTR_CONTAINER: const.VALUE_YES,
            const.ATTR_CONTAINER_ID: "123",
        },
        source_id=const.MUSIC_SOURCE_PLAYLISTS,
    )
    args = {
        const.ATTR_PLAYER_ID: "1",
        const.ATTR_SOURCE_ID: str(const.MUSIC_SOURCE_PLAYLISTS),
        const.ATTR_CONTAINER_ID: "123",
        const.ATTR_ADD_CRITERIA_ID: str(const.AddCriteriaType.PLAY_NOW),
    }
    mock_device.register(
        const.COMMAND_BROWSE_ADD_TO_QUEUE, args, "browse.add_to_queue_container"
    )
    await player.play_media(source, const.AddCriteriaType.PLAY_NOW)


@pytest.mark.asyncio
async def test_play_media_track(
    mock_device: MockHeosDevice, heos: Heos, media_item_song_data: dict[str, str]
) -> None:
    """Test adding a track to the queue."""
    await heos.get_players()
    player = heos.players[1]
    source = MediaItem.from_data(
        media_item_song_data,
        source_id=const.MUSIC_SOURCE_PLAYLISTS,
        container_id="123",
    )
    args = {
        const.ATTR_PLAYER_ID: "1",
        const.ATTR_SOURCE_ID: str(const.MUSIC_SOURCE_PLAYLISTS),
        const.ATTR_CONTAINER_ID: "123",
        const.ATTR_ADD_CRITERIA_ID: str(const.AddCriteriaType.PLAY_NOW),
        const.ATTR_MEDIA_ID: "78374741",
    }
    mock_device.register(
        const.COMMAND_BROWSE_ADD_TO_QUEUE, args, "browse.add_to_queue_track"
    )
    await player.play_media(source, const.AddCriteriaType.PLAY_NOW)


@pytest.mark.asyncio
async def test_add_to_queue(
    mock_device: MockHeosDevice, heos: Heos, media_item_song: MediaItem
) -> None:
    """Test adding a track to the queue."""
    await heos.get_players()
    player = heos.players[1]
    args = {
        const.ATTR_PLAYER_ID: "1",
        const.ATTR_SOURCE_ID: media_item_song.source_id,
        const.ATTR_CONTAINER_ID: media_item_song.container_id,
        const.ATTR_ADD_CRITERIA_ID: str(const.AddCriteriaType.PLAY_NOW),
        const.ATTR_MEDIA_ID: media_item_song.media_id,
    }
    mock_device.register(
        const.COMMAND_BROWSE_ADD_TO_QUEUE, args, "browse.add_to_queue_track"
    )
    assert media_item_song.container_id is not None
    await player.add_to_queue(
        media_item_song.source_id,
        media_item_song.container_id,
        media_item_song.media_id,
        const.AddCriteriaType.PLAY_NOW,
    )


@pytest.mark.asyncio
async def test_now_playing_media_unavailable(
    mock_device: MockHeosDevice, heos: Heos
) -> None:
    """Test edge where now_playing_media returns an empty payload."""
    await heos.get_players()
    player = heos.players[1]
    mock_device.register(
        const.COMMAND_GET_NOW_PLAYING_MEDIA,
        None,
        "player.get_now_playing_media_blank",
        replace=True,
    )
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
