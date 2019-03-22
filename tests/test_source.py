"""Tests for the sources module."""
from pyheos.source import HeosSource


def test_str_repr():
    """Test the __str__ function."""
    data = {
        "name": "AUX Input",
        "image_url": "https://production.ws.skyegloup.com:443"
                     "/media/images/service/logos/musicsource_logo_aux.png",
        "type": "heos_service",
        "sid": 1027,
        "available": "true"
    }
    player = HeosSource(None, data)
    assert str(player) == '<AUX Input (heos_service)>'
    assert repr(player) == '<AUX Input (heos_service) 1027>'
