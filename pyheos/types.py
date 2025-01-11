"""Define the types module for HEOS."""

from enum import IntEnum, StrEnum


class AddCriteriaType(IntEnum):
    """Define the add to queue options."""

    PLAY_NOW = 1
    PLAY_NEXT = 2
    ADD_TO_END = 3
    REPLACE_AND_PLAY = 4


class ConnectionState(StrEnum):
    """Define the possible connection states."""

    CONNECTED = "connected"
    DISCONNECTED = "disconnected"
    RECONNECTING = "reconnecting"


class LineOutLevelType(IntEnum):
    """Define the line out level types."""

    UNKNOWN = 0
    VARIABLE = 1
    FIXED = 2


class VolumeControlType(IntEnum):
    "Define control types."

    UNKNOWN = 0
    NONE = 1
    IR = 2
    TRIGGER = 3
    NETWORK = 4


class NetworkType(StrEnum):
    """Define the network type."""

    WIRED = "wired"
    WIFI = "wifi"
    UNKNOWN = "unknown"


class ControlType(StrEnum):
    """Define the control types."""

    PLAY = "play"
    PAUSE = "pause"
    STOP = "stop"
    PLAY_NEXT = "play_next"
    PLAY_PREVIOUS = "play_previous"


class MediaType(StrEnum):
    """Define the media types."""

    ALBUM = "album"
    ARTIST = "artist"
    CONTAINER = "container"
    DLNA_SERVER = "dlna_server"
    GENRE = "genre"
    HEOS_SERVER = "heos_server"
    HEOS_SERVICE = "heos_service"
    MUSIC_SERVICE = "music_service"
    PLAYLIST = "playlist"
    SONG = "song"
    STATION = "station"


class PlayState(StrEnum):
    """Define the play states."""

    PLAY = "play"
    PAUSE = "pause"
    STOP = "stop"


class SignalType(StrEnum):
    """Define the signal names."""

    PLAYER_EVENT = "player_event"
    GROUP_EVENT = "group_event"
    CONTROLLER_EVENT = "controller_event"
    HEOS_EVENT = "heos_event"


class SignalHeosEvent(StrEnum):
    CONNECTED = "connected"
    DISCONNECTED = "disconnected"
    USER_CREDENTIALS_INVALID = "usercredentials_invalid"


class RepeatType(StrEnum):
    """Define the repeat types."""

    ON_ALL = "on_all"
    ON_ONE = "on_one"
    OFF = "off"
