"""Tests for the response module."""

from pyheos.response import HeosResponse


def test_str():
    """Test the __str__ function."""
    data = {
        "heos": {
            "command": "player/get_play_state",
            "result": "success",
            "message": "pid={player_id}&state=stop"
        },
        "payload": {
        }
    }
    player = HeosResponse(data)
    assert str(player) == str(data['heos'])
    assert repr(player) == str(data)
