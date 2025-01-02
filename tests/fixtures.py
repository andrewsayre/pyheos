"""Define the fixtures for the tests."""

from pyheos import const
from pyheos.media import MediaItem


# Media Items
class MediaItems:
    """Define a set of media items for testing."""

    INPUT = MediaItem(
        -263109739,
        "HEOS Drive - AUX In 1",
        const.MediaType.STATION,
        "",
        None,
        True,
        False,
        None,
        "inputs/aux_in_1",
        None,
        None,
        None,
    )
