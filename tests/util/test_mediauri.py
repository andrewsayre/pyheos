"""Tests for the mediauri utility module."""

import pytest

from pyheos.media import MediaItem, MediaMusicSource
from pyheos.util import mediauri
from tests.common import MediaItems, MediaMusicSources


@pytest.mark.parametrize(
    ("uri", "expected_result"),
    [("heos://media/10/album", True), ("http://example.com", False)],
)
def test_is_media_uri(uri: str, expected_result: bool) -> None:
    """Test the is_media_uri function."""
    assert mediauri.is_media_uri(uri) == expected_result


@pytest.mark.parametrize(
    ("media", "expected_uri"),
    [
        (
            MediaItems.ALBUM,
            "heos://media/10/album?name=After+Hours&image_url=http%3A%2F%2Fresources.wimpmusic.com%2Fimages%2Fbbe7f53c%2F44f0%2F41ba%2F873f%2F743e3091adde%2F160x160.jpg&playable=True&browsable=True&container_id=LIBALBUM-134788273&artist=The+Weeknd",
        ),
        (
            MediaItems.INPUT,
            "heos://media/-263109739/station?name=HEOS+Drive+-+AUX+In+1&image_url=&playable=True&browsable=False&media_id=inputs%2Faux_in_1",
        ),
        (
            MediaItems.SONG,
            "heos://media/10/song?name=Imaginary+Parties&image_url=http%3A%2F%2Fresources.wimpmusic.com%2Fimages%2F7e7bacc1%2F3e75%2F4761%2Fa822%2F9342239edfa0%2F640x640.jpg&playable=True&browsable=False&container_id=123&media_id=456&artist=Superfruit&album=Future+Friends&album_id=78374740",
        ),
    ],
    ids=["album", "input", "song"],
)
def test_to_from_media_uri_media(media: MediaItem, expected_uri: str) -> None:
    """Test media items are rendered as a URI string correctly."""
    uri = mediauri.to_media_uri(media)
    assert uri == expected_uri

    new_media = mediauri.from_media_uri(uri)
    assert isinstance(new_media, MediaItem)
    assert new_media.source_id == media.source_id
    assert new_media.type == media.type
    assert new_media.name == media.name
    assert new_media.image_url == media.image_url
    assert new_media.playable == media.playable
    assert new_media.browsable == media.browsable
    assert new_media.container_id == media.container_id
    assert new_media.media_id == media.media_id
    assert new_media.artist == media.artist
    assert new_media.album == media.album
    assert new_media.album_id == media.album_id


@pytest.mark.parametrize(
    ("media", "expected_uri"),
    [
        (
            MediaMusicSources.FAVORITES,
            "heos://media/1028/heos_service?name=Favorites&image_url=https%3A%2F%2Fproduction.ws.skyegloup.com%3A443%2Fmedia%2Fimages%2Fservice%2Flogos%2Fmusicsource_logo_favorites.png&available=True",
        ),
        (
            MediaMusicSources.TIDAL,
            "heos://media/10/music_service?name=Tidal&image_url=https%3A%2F%2Fproduction.ws.skyegloup.com%3A443%2Fmedia%2Fimages%2Fservice%2Flogos%2Ftidal.png&available=True&service_username=user%40example.com",
        ),
        (
            MediaMusicSources.PANDORA,
            "heos://media/1/music_service?name=Pandora&image_url=https%3A%2F%2Fproduction.ws.skyegloup.com%3A443%2Fmedia%2Fimages%2Fservice%2Flogos%2Fpandora.png&available=False",
        ),
    ],
    ids=["favorites", "tidal", "pandora"],
)
def test_to_from_media_uri_music_source(
    media: MediaMusicSource, expected_uri: str
) -> None:
    """Test media items are rendered as a URI string correctly."""
    uri = mediauri.to_media_uri(media)
    assert uri == expected_uri

    new_media = mediauri.from_media_uri(uri)
    assert isinstance(new_media, MediaMusicSource)
    assert new_media.source_id == media.source_id
    assert new_media.type == media.type
    assert new_media.name == media.name
    assert new_media.image_url == media.image_url
    assert new_media.available == media.available
    assert new_media.service_username == media.service_username
