"""Define the types module for HEOS."""

from enum import IntEnum, StrEnum


class AddCriteriaType(IntEnum):
    """Define the add to queue options."""

    PLAY_NOW = 1
    PLAY_NEXT = 2
    ADD_TO_END = 3
    REPLACE_AND_PLAY = 4


class NetworkType(StrEnum):
    """Define the network type."""

    WIRED = "wired"
    WIFI = "wifi"
    UNKNOWN = "unknown"


class PlayState(StrEnum):
    """Define the play states."""

    PLAY = "play"
    PAUSE = "pause"
    STOP = "stop"


class RepeatType(StrEnum):
    """Define the repeat types."""

    ON_ALL = "on_all"
    ON_ONE = "on_one"
    OFF = "off"
