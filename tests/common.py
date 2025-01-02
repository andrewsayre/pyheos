"""Define the common for the tests."""

from pyheos import const
from pyheos.media import MediaItem, MediaMusicSource


# Media Items
class MediaItems:
    """Define a set of media items for testing."""

    ALBUM = MediaItem(
        const.MUSIC_SOURCE_TIDAL,
        "After Hours",
        const.MediaType.ALBUM,
        "http://resources.wimpmusic.com/images/bbe7f53c/44f0/41ba/873f/743e3091adde/160x160.jpg",
        None,
        True,
        True,
        "LIBALBUM-134788273",
        None,
        "The Weeknd",
        None,
        None,
    )

    PLAYLIST = MediaItem(
        const.MUSIC_SOURCE_PLAYLISTS,
        "My Playlist",
        const.MediaType.PLAYLIST,
        "",
        None,
        True,
        True,
        "123",
        None,
        None,
        None,
        None,
    )

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

    SONG = MediaItem(
        const.MUSIC_SOURCE_TIDAL,
        "Imaginary Parties",
        const.MediaType.SONG,
        "http://resources.wimpmusic.com/images/7e7bacc1/3e75/4761/a822/9342239edfa0/640x640.jpg",
        None,
        True,
        False,
        "123",
        "456",
        "Superfruit",
        "Future Friends",
        "78374740",
    )

    STATION = MediaItem(
        const.MUSIC_SOURCE_PANDORA,
        "Cooltime Kids (Children's) Radio",
        const.MediaType.STATION,
        "https://content-images.p-cdn.com/images/9d/b9/b9/85/ef1146388a09ecb87153e168/_500W_500H.jpg",
        None,
        True,
        False,
        "A-Z",
        "3853208159976579343",
        None,
        None,
        None,
    )


class MediaMusicSources:
    """Define a set of media music sources for testing."""

    FAVORITES = MediaMusicSource(
        const.MUSIC_SOURCE_FAVORITES,
        "Favorites",
        const.MediaType.HEOS_SERVICE,
        "",
        None,
        True,
        None,
    )
    PANDORA = MediaMusicSource(
        const.MUSIC_SOURCE_PANDORA,
        "Pandora",
        const.MediaType.MUSIC_SERVICE,
        "",
        None,
        False,
        None,
    )
