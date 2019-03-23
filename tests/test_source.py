"""Tests for the sources module."""
from pyheos.source import HeosSource, InputSource


def test_source_str_repr():
    """Test the __str__ function."""
    data = {
        "name": "AUX Input",
        "image_url": "https://production.ws.skyegloup.com:443"
                     "/media/images/service/logos/musicsource_logo_aux.png",
        "type": "heos_service",
        "sid": 1027,
        "available": "true"
    }
    source = HeosSource(None, data)
    assert str(source) == '<AUX Input (heos_service)>'
    assert repr(source) == '<AUX Input (heos_service) 1027>'


def test_input_str_repr():
    """Test the __str__ function."""
    source = InputSource(1, "Test", "Input")
    assert str(source) == "<Test (Input)>"
    assert repr(source) == "<Test (Input) on 1>"
