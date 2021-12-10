"""Tests for the sources module."""
import pytest

from pyheos import const
from pyheos.source import HeosSource, InputSource


def test_source_str_repr():
    """Test the __str__ function."""
    data = {
        "name": "AUX Input",
        "image_url": "https://production.ws.skyegloup.com:443"
        "/media/images/service/logos/musicsource_logo_aux.png",
        "type": "heos_service",
        "sid": 1027,
        "available": "true",
    }
    source = HeosSource(None, data)
    assert str(source) == "<AUX Input (heos_service)>"
    assert repr(source) == "<AUX Input (heos_service) 1027>"


def test_input_str_repr():
    """Test the __str__ function."""
    source = InputSource(1, "Test", "Input")
    assert str(source) == "<Test (Input)>"
    assert repr(source) == "<Test (Input) on 1>"


@pytest.mark.asyncio
async def test_browse_source(mock_device, heos):
    """Test the browse function."""
    sources = await heos.get_music_sources()
    local_music_sid = 1024
    source = sources.get(local_music_sid)
    args = {"sid": str(local_music_sid)}
    mock_device.register(const.COMMAND_BROWSE_BROWSE, args, "browse.browse_source")
    containers = await source.browse()
    assert len(containers) == 1
    container = containers[0]
    assert container.container
    assert container.container_id == "10"
    assert container.source_id == local_music_sid  # tests id inheritance

    # Test cannot be used on containers
    with pytest.raises(RuntimeError) as excinfo:
        await container.browse()

    assert "Use browse_container instead" in str(excinfo.value)


@pytest.mark.asyncio
async def test_browse_container(mock_device, heos):
    """Test the browse_container function."""
    sources = await heos.get_music_sources()
    local_music_sid = 1024
    source = sources.get(local_music_sid)
    args = {"sid": str(local_music_sid)}
    mock_device.register(const.COMMAND_BROWSE_BROWSE, args, "browse.browse_source")
    containers = await source.browse()
    container = containers[0]
    start = 0
    end = 50
    args = {
        "sid": str(local_music_sid),
        "cid": container.container_id,
        "range": "%d,%d" % (start, end),
    }
    mock_device.register(
        const.COMMAND_BROWSE_BROWSE, args, "browse.browse_container", replace=True
    )
    subcontainers = await container.browse_container(start, end)
    assert len(subcontainers) == 1
    subcontainer = subcontainers[0]
    args = {
        "sid": str(local_music_sid),
        "cid": subcontainer.container_id,
        "range": "%d,%d" % (start, end),
    }
    mock_device.register(
        const.COMMAND_BROWSE_BROWSE, args, "browse.browse_subcontainer"
    )
    songs = await subcontainer.browse_container(start, end)
    assert len(songs) == 1
    song = songs[0]
    assert not song.container
    assert song.media_id == "10/11/20"
    assert song.container_id == subcontainer.container_id  # tests id inheritance
    assert song.source_id == local_music_sid  # tests id inheritance

    # Test cannot be used on non containers
    with pytest.raises(RuntimeError) as excinfo:
        await source.browse_container(start, end)

    assert "Use browse instead" in str(excinfo.value)


@pytest.mark.asyncio
async def test_get_child_source(mock_device, heos):
    """Test getting a child source."""
    sources = await heos.get_music_sources()
    local_music_sid = 1024
    source = sources.get(local_music_sid)
    args = {"sid": str(local_music_sid)}
    mock_device.register(const.COMMAND_BROWSE_BROWSE, args, "browse.browse_source")
    containers = await source.browse()
    container = containers[0]

    search_container = await source.get_child_source(container.name)
    assert search_container.container_id == container.container_id

    start = 0
    end = start + const.INDEX_CHUNK_SIZE
    args = {
        "sid": str(local_music_sid),
        "cid": container.container_id,
        "range": "%d,%d" % (start, end),
    }
    mock_device.register(
        const.COMMAND_BROWSE_BROWSE, args, "browse.browse_container", replace=True
    )
    subcontainers = await container.browse_container(start, end)
    subcontainer = subcontainers[0]
    start = 1
    end = start + const.INDEX_CHUNK_SIZE
    args = {
        "sid": str(local_music_sid),
        "cid": container.container_id,
        "range": "%d,%d" % (start, end),
    }
    mock_device.register(
        const.COMMAND_BROWSE_BROWSE, args, "browse.browse_container_exhausted"
    )

    search_subcontainer = await container.get_child_source(subcontainer.name)
    assert search_subcontainer.container_id == subcontainer.container_id

    # Test not found
    assert await source.get_child_source("Does not exist") is None
    assert await container.get_child_source("Does not exist") is None


@pytest.mark.asyncio
async def test_index_all(mock_device, heos):
    """Test the index_all functionality."""
    sources = await heos.get_music_sources()
    local_music_sid = 1024
    source = sources.get(local_music_sid)
    args = {"sid": str(local_music_sid)}
    mock_device.register(const.COMMAND_BROWSE_BROWSE, args, "browse.browse_source")
    containers = await source.browse()
    container = containers[0]
    start = 0
    end = start + const.INDEX_CHUNK_SIZE
    args = {
        "sid": str(local_music_sid),
        "cid": container.container_id,
        "range": "%d,%d" % (start, end),
    }
    mock_device.register(
        const.COMMAND_BROWSE_BROWSE, args, "browse.browse_container", replace=True
    )
    subcontainers = await container.browse_container(start, end)
    subcontainer = subcontainers[0]
    args = {
        "sid": str(local_music_sid),
        "cid": subcontainer.container_id,
        "range": "%d,%d" % (start, end),
    }
    mock_device.register(
        const.COMMAND_BROWSE_BROWSE, args, "browse.browse_subcontainer"
    )
    songs = await subcontainer.browse_container(start, end)
    song = songs[0]

    start = 1
    end = start + const.INDEX_CHUNK_SIZE
    args = {
        "sid": str(local_music_sid),
        "cid": container.container_id,
        "range": "%d,%d" % (start, end),
    }
    mock_device.register(
        const.COMMAND_BROWSE_BROWSE, args, "browse.browse_container_exhausted"
    )
    args = {
        "sid": str(local_music_sid),
        "cid": subcontainer.container_id,
        "range": "%d,%d" % (start, end),
    }
    mock_device.register(
        const.COMMAND_BROWSE_BROWSE, args, "browse.browse_subcontainer_exhausted"
    )

    song_count = await container.index_all()
    assert song_count == 1
    search_subcontainer = await container.get_child_source(subcontainer.name)
    assert search_subcontainer.container_id == subcontainer.container_id
    search_song = await search_subcontainer.get_child_source(song.name)
    assert search_song.media_id == song.media_id
