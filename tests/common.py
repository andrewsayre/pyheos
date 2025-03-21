"""Define the common for the tests."""

from pyheos import const
from pyheos.media import MediaItem, MediaMusicSource
from pyheos.types import MediaType


# Media Items
class MediaItems:
    """Define a set of media items for testing."""

    ALBUM = MediaItem(
        const.MUSIC_SOURCE_TIDAL,
        "After Hours",
        MediaType.ALBUM,
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
        MediaType.PLAYLIST,
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
        MediaType.STATION,
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
        MediaType.SONG,
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
        MediaType.STATION,
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

    DEVICE = MediaItem(
        -263109739,
        "HEOS Drive",
        MediaType.HEOS_SERVICE,
        "https://production.ws.skyegloup.com:443/media/images/service/logos/musicsource_logo_aux.png",
        None,
        False,
        True,
    )


class MediaMusicSources:
    """Define a set of media music sources for testing."""

    FAVORITES = MediaMusicSource(
        const.MUSIC_SOURCE_FAVORITES,
        "Favorites",
        MediaType.HEOS_SERVICE,
        "https://production.ws.skyegloup.com:443/media/images/service/logos/musicsource_logo_favorites.png",
        None,
        True,
        None,
    )
    PANDORA = MediaMusicSource(
        const.MUSIC_SOURCE_PANDORA,
        "Pandora",
        MediaType.MUSIC_SERVICE,
        "https://production.ws.skyegloup.com:443/media/images/service/logos/pandora.png",
        None,
        False,
        None,
    )
    TIDAL = MediaMusicSource(
        const.MUSIC_SOURCE_TIDAL,
        "Tidal",
        MediaType.MUSIC_SERVICE,
        "https://production.ws.skyegloup.com:443/media/images/service/logos/tidal.png",
        None,
        True,
        "user@example.com",
    )
