"""Define tests for browsing media."""

from typing import cast

import pytest

from pyheos.error import CommandFailedError
from pyheos.heos import Heos
from pyheos.media import MediaContainer, MediaSource


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
            if source.available:
                await print_source(source)

        assert sources
    finally:
        await heos.disconnect()


@pytest.mark.skip
async def print_source(source: MediaSource | MediaContainer, level: int = 0) -> None:
    """Print the source and its contents."""
    if level > 3:
        print(f"{'    ' * (level)}{source}")
        return

    try:
        if issubclass(type(source), MediaContainer):
            container = cast(MediaContainer, source)
            print(
                f"{'    ' * level}{source.name} (sid={container.source_id}&cid={container.container_id}) ->"
            )
            result = await container.browse(0, 5)
        else:
            print(f"{'    ' * level}{source.name} (sid={source.source_id}) ->")
            result = await source.browse()
    except CommandFailedError:
        return

    for item in result.items:
        if issubclass(type(item), tuple([MediaSource, MediaContainer])):
            await print_source(item, level + 1)  # type: ignore[arg-type]
        else:
            print(f"{'    ' * (level + 1)}{item}")
    print("")
