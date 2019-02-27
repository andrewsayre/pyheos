"""Tests for the const file."""
from pyheos import const


def test_init():
    """Single test so tox passes."""
    assert const.__version__ == '0.0.0'
    assert const.__title__ == 'pyheos'

