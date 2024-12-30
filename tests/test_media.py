"""Define tests for browsing media."""

import pytest

from pyheos.error import CommandFailedError
from pyheos.heos import Heos
from pyheos.media import MediaItem


@pytest.mark.skip
@pytest.mark.asyncio
async def test_browse() -> None:
    """Test groups changed fires dispatcher."""
    print("")
    try:
        heos = await Heos.create_and_connect(
            "172.16.0.255", events=False, auto_reconnect=False, heart_beat=False
        )
        sources = await heos.get_music_sources()

        for source in sources.values():
            if not source.available:
                continue

            print(f"{source.name} (sid={source.source_id}) ->")
            result = await source.browse()
            for item in result.items:
                await print_source(item)

        assert sources
    finally:
        await heos.disconnect()


@pytest.mark.skip
async def print_source(source: MediaItem, level: int = 0) -> None:
    """Print the source and its contents."""
    if level > 3:
        print(f"{'    ' * (level)}{source}")
        return

    if source.container_id:
        print(
            f"{'    ' * level}{source.name} (sid={source.source_id}&cid={source.container_id}) ->"
        )
    else:
        print(f"{'    ' * level}{source.name} (sid={source.source_id}) ->")

    try:
        result = await source.browse(0, 5)
    except CommandFailedError:
        return

    for item in result.items:
        if item.browsable:
            await print_source(item, level + 1)
        else:
            print(f"{'    ' * (level + 1)}{item}")
    print("")
