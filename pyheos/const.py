"""Define consts for the pyheos package."""

from enum import StrEnum
from typing import Final

CLI_PORT: Final = 1255
DEFAULT_TIMEOUT: Final = 10.0
DEFAULT_RECONNECT_DELAY: Final = 10.0
DEFAULT_RECONNECT_ATTEMPTS: Final = 0  # Unlimited
DEFAULT_HEART_BEAT: Final = 10.0
DEFAULT_STEP: Final = 5

ATTR_ALBUM_ID: Final = "album_id"
ATTR_ALBUM: Final = "album"
ATTR_ARTIST: Final = "artist"
ATTR_AVAILABLE: Final = "available"
ATTR_CONTAINER: Final = "container"
ATTR_CONTAINER_ID: Final = "cid"
ATTR_COUNT: Final = "count"
ATTR_CURRENT_POSITION: Final = "cur_pos"
ATTR_DURATION: Final = "duration"
ATTR_ENABLE: Final = "enable"
ATTR_ERROR: Final = "error"
ATTR_ERROR_ID: Final = "eid"
ATTR_GROUP_ID: Final = "gid"
ATTR_ID: Final = "id"
ATTR_IMAGE_URL: Final = "image_url"
ATTR_IP_ADDRESS: Final = "ip"
ATTR_LEVEL: Final = "level"
ATTR_LINE_OUT: Final = "lineout"
ATTR_MEDIA_ID: Final = "mid"
ATTR_MODEL: Final = "model"
ATTR_MUTE: Final = "mute"
ATTR_NAME: Final = "name"
ATTR_NETWORK: Final = "network"
ATTR_PASSWORD: Final = "pw"
ATTR_PLAYABLE: Final = "playable"
ATTR_PLAYER_ID: Final = "pid"
ATTR_QUEUE_ID: Final = "qid"
ATTR_RANGE: Final = "range"
ATTR_REPEAT: Final = "repeat"
ATTR_RETURNED: Final = "returned"
ATTR_SERIAL: Final = "serial"
ATTR_SERVICE_USER_NAME: Final = "service_username"
ATTR_SHUFFLE: Final = "shuffle"
ATTR_SONG: Final = "song"
ATTR_SOURCE_ID: Final = "sid"
ATTR_SIGNED_OUT: Final = "signed_out"
ATTR_SIGNED_IN: Final = "signed_in"
ATTR_STATE: Final = "state"
ATTR_STATION: Final = "station"
ATTR_STEP: Final = "step"
ATTR_SYSTEM_ERROR_NUMBER: Final = "syserrno"
ATTR_TEXT: Final = "text"
ATTR_TYPE: Final = "type"
ATTR_URL: Final = "url"
ATTR_USER_NAME: Final = "un"
ATTR_VERSION: Final = "version"

QUOTE_MAP: Final = {"&": "%26", "=": "%3D", "%": "%25"}
MASKED_PARAMS: Final = {ATTR_PASSWORD}
MASK: Final = "********"
SEPARATOR: Final = "\r\n"
SEPARATOR_BYTES: Final = SEPARATOR.encode()

VALUE_ON: Final = "on"
VALUE_OFF: Final = "off"
VALUE_TRUE: Final = "true"
VALUE_FALSE: Final = "false"
VALUE_YES: Final = "yes"
VALUE_NO: Final = "no"

ERROR_INVALID_CREDNETIALS: Final = 6
ERROR_USER_NOT_LOGGED_IN: Final = 8
ERROR_USER_NOT_FOUND: Final = 10
ERROR_SYSTEM_ERROR: Final = 12

SYSTEM_ERROR_USER_NOT_LOGGED_IN: Final = -1063
SYSTEM_ERROR_USER_NOT_FOUND: Final = -1056

STATE_CONNECTED: Final = "connected"
STATE_DISCONNECTED: Final = "disconnected"
STATE_RECONNECTING: Final = "reconnecting"

NETWORK_TYPE_WIRED: Final = "wired"
NETWORK_TYPE_WIFI: Final = "wifi"
NETWORK_TYPE_UNKNOWN: Final = "unknown"

DATA_NEW: Final = "new"
DATA_MAPPED_IDS: Final = "mapped_ids"

PLAY_STATE_PLAY: Final = "play"
PLAY_STATE_PAUSE: Final = "pause"
PLAY_STATE_STOP: Final = "stop"
VALID_PLAY_STATES: Final = (PLAY_STATE_PLAY, PLAY_STATE_PAUSE, PLAY_STATE_STOP)


class RepeatType(StrEnum):
    """Define the repeat types."""

    ON_ALL = "on_all"
    ON_ONE = "on_one"
    OFF = "off"


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


# Music Sources
MUSIC_SOURCE_PANDORA: Final = 1
MUSIC_SOURCE_RHAPSODY: Final = 2
MUSIC_SOURCE_TUNEIN: Final = 3
MUSIC_SOURCE_SPOTIFY: Final = 4
MUSIC_SOURCE_DEEZER: Final = 5
MUSIC_SOURCE_NAPSTER: Final = 6
MUSIC_SOURCE_IHEARTRADIO: Final = 7
MUSIC_SOURCE_SIRIUSXM: Final = 8
MUSIC_SOURCE_SOUNDCLOUD: Final = 9
MUSIC_SOURCE_TIDAL: Final = 10
MUSIC_SOURCE_RDIO: Final = 12
MUSIC_SOURCE_AMAZON: Final = 13
MUSIC_SOURCE_MOODMIX: Final = 15
MUSIC_SOURCE_JUKE: Final = 16
MUSIC_SOURCE_QQMUSIC: Final = 18
MUSIC_SOURCE_LOCAL_MUSIC: Final = 1024
MUSIC_SOURCE_PLAYLISTS: Final = 1025
MUSIC_SOURCE_HISTORY: Final = 1026
MUSIC_SOURCE_AUX_INPUT: Final = 1027
MUSIC_SOURCE_FAVORITES: Final = 1028

# Supported controls
CONTROL_PLAY: Final = "play"
CONTROL_PAUSE: Final = "pause"
CONTROL_STOP: Final = "stop"
CONTROL_PLAY_NEXT: Final = "play_next"
CONTROL_PLAY_PREVIOUS: Final = "play_previous"

CONTROLS_ALL: Final = [
    CONTROL_PLAY,
    CONTROL_PAUSE,
    CONTROL_STOP,
    CONTROL_PLAY_NEXT,
    CONTROL_PLAY_PREVIOUS,
]
CONTROLS_FORWARD_ONLY: Final = [
    CONTROL_PLAY,
    CONTROL_PAUSE,
    CONTROL_STOP,
    CONTROL_PLAY_NEXT,
]
CONTROL_PLAY_STOP: Final = [CONTROL_PLAY, CONTROL_STOP]

SOURCE_CONTROLS: Final = {
    MUSIC_SOURCE_PANDORA: {MediaType.STATION: CONTROLS_FORWARD_ONLY},
    MUSIC_SOURCE_RHAPSODY: {
        MediaType.SONG: CONTROLS_ALL,
        MediaType.STATION: CONTROLS_FORWARD_ONLY,
    },
    MUSIC_SOURCE_TUNEIN: {
        MediaType.SONG: CONTROLS_ALL,
        MediaType.STATION: CONTROL_PLAY_STOP,
    },
    MUSIC_SOURCE_SPOTIFY: {
        MediaType.SONG: CONTROLS_ALL,
        MediaType.STATION: CONTROLS_FORWARD_ONLY,
    },
    MUSIC_SOURCE_DEEZER: {
        MediaType.SONG: CONTROLS_ALL,
        MediaType.STATION: CONTROLS_FORWARD_ONLY,
    },
    MUSIC_SOURCE_NAPSTER: {
        MediaType.SONG: CONTROLS_ALL,
        MediaType.STATION: CONTROLS_FORWARD_ONLY,
    },
    MUSIC_SOURCE_IHEARTRADIO: {
        MediaType.SONG: CONTROLS_ALL,
        MediaType.STATION: CONTROL_PLAY_STOP,
    },
    MUSIC_SOURCE_SIRIUSXM: {MediaType.STATION: CONTROL_PLAY_STOP},
    MUSIC_SOURCE_SOUNDCLOUD: {MediaType.SONG: CONTROLS_ALL},
    MUSIC_SOURCE_TIDAL: {MediaType.SONG: CONTROLS_ALL},
    MUSIC_SOURCE_AMAZON: {
        MediaType.SONG: CONTROLS_ALL,
        MediaType.STATION: CONTROLS_ALL,
    },
    MUSIC_SOURCE_AUX_INPUT: {MediaType.STATION: CONTROL_PLAY_STOP},
}


# Inputs
INPUT_ANALOG_IN_1: Final = "inputs/analog_in_1"
INPUT_ANALOG_IN_2: Final = "inputs/analog_in_2"
INPUT_AUX_8K: Final = "inputs/aux_8k"
INPUT_AUX_IN_1: Final = "inputs/aux_in_1"
INPUT_AUX_IN_2: Final = "inputs/aux_in_2"
INPUT_AUX_IN_3: Final = "inputs/aux_in_3"
INPUT_AUX_IN_4: Final = "inputs/aux_in_4"
INPUT_AUX_IN_SINGLE: Final = "inputs/aux_single"
INPUT_AUX1: Final = "inputs/aux1"
INPUT_AUX2: Final = "inputs/aux2"
INPUT_AUX3: Final = "inputs/aux3"
INPUT_AUX4: Final = "inputs/aux4"
INPUT_AUX5: Final = "inputs/aux5"
INPUT_AUX6: Final = "inputs/aux6"
INPUT_AUX7: Final = "inputs/aux7"
INPUT_BLURAY: Final = "inputs/bluray"
INPUT_CABLE_SAT: Final = "inputs/cable_sat"
INPUT_CD: Final = "inputs/cd"
INPUT_COAX_IN_1: Final = "inputs/coax_in_1"
INPUT_COAX_IN_2: Final = "inputs/coax_in_2"
INPUT_DVD: Final = "inputs/dvd"
INPUT_GAME: Final = "inputs/game"
INPUT_GAME_2: Final = "inputs/game2"
INPUT_HD_RADIO: Final = "inputs/hdradio"
INPUT_HDMI_ARC_1: Final = "inputs/hdmi_arc_1"
INPUT_HDMI_IN_1: Final = "inputs/hdmi_in_1"
INPUT_HDMI_IN_2: Final = "inputs/hdmi_in_2"
INPUT_HDMI_IN_3: Final = "inputs/hdmi_in_3"
INPUT_HDMI_IN_4: Final = "inputs/hdmi_in_4"
INPUT_LINE_IN_1: Final = "inputs/line_in_1"
INPUT_LINE_IN_2: Final = "inputs/line_in_2"
INPUT_LINE_IN_3: Final = "inputs/line_in_3"
INPUT_LINE_IN_4: Final = "inputs/line_in_4"
INPUT_MEDIA_PLAYER: Final = "inputs/mediaplayer"
INPUT_OPTICAL_IN_1: Final = "inputs/optical_in_1"
INPUT_OPTICAL_IN_2: Final = "inputs/optical_in_2"
INPUT_OPTICAL_IN_3: Final = "inputs/optical_in_3"
INPUT_PHONO: Final = "inputs/phono"
INPUT_RECORDER_IN_1: Final = "inputs/recorder_in_1"
INPUT_TUNER: Final = "inputs/tuner"
INPUT_TV: Final = "inputs/tv"
INPUT_TV_AUDIO: Final = "inputs/tvaudio"
INPUT_USB_AC: Final = "inputs/usbdac"

VALID_INPUTS: Final = (
    INPUT_ANALOG_IN_1,
    INPUT_ANALOG_IN_2,
    INPUT_AUX_8K,
    INPUT_AUX_IN_1,
    INPUT_AUX_IN_2,
    INPUT_AUX_IN_3,
    INPUT_AUX_IN_4,
    INPUT_AUX_IN_SINGLE,
    INPUT_AUX1,
    INPUT_AUX2,
    INPUT_AUX3,
    INPUT_AUX4,
    INPUT_AUX5,
    INPUT_AUX6,
    INPUT_AUX7,
    INPUT_BLURAY,
    INPUT_CABLE_SAT,
    INPUT_CD,
    INPUT_COAX_IN_1,
    INPUT_COAX_IN_2,
    INPUT_DVD,
    INPUT_GAME_2,
    INPUT_GAME,
    INPUT_HD_RADIO,
    INPUT_HDMI_ARC_1,
    INPUT_HDMI_IN_1,
    INPUT_HDMI_IN_2,
    INPUT_HDMI_IN_3,
    INPUT_HDMI_IN_4,
    INPUT_LINE_IN_1,
    INPUT_LINE_IN_2,
    INPUT_LINE_IN_3,
    INPUT_LINE_IN_4,
    INPUT_MEDIA_PLAYER,
    INPUT_OPTICAL_IN_1,
    INPUT_OPTICAL_IN_2,
    INPUT_OPTICAL_IN_3,
    INPUT_PHONO,
    INPUT_RECORDER_IN_1,
    INPUT_TUNER,
    INPUT_TV_AUDIO,
    INPUT_TV,
    INPUT_USB_AC,
)

# Add to Queue Options
ADD_QUEUE_PLAY_NOW: Final = 1
ADD_QUEUE_PLAY_NEXT: Final = 2
ADD_QUEUE_ADD_TO_END: Final = 3
ADD_QUEUE_REPLACE_AND_PLAY: Final = 4

VALID_ADD_QUEUE_OPTIONS: Final = (
    ADD_QUEUE_PLAY_NOW,
    ADD_QUEUE_PLAY_NEXT,
    ADD_QUEUE_ADD_TO_END,
    ADD_QUEUE_REPLACE_AND_PLAY,
)

# Signals
SIGNAL_PLAYER_EVENT: Final = "player_event"
SIGNAL_GROUP_EVENT: Final = "group_event"
SIGNAL_CONTROLLER_EVENT: Final = "controller_event"
SIGNAL_HEOS_EVENT: Final = "heos_event"
EVENT_CONNECTED: Final = "connected"
EVENT_DISCONNECTED: Final = "disconnected"
EVENT_USER_CREDENTIALS_INVALID: Final = "user credentials invalid"

BASE_URI: Final = "heos://"

# Browse commands
COMMAND_BROWSE_GET_SOURCES: Final = "browse/get_music_sources"
COMMAND_BROWSE_BROWSE: Final = "browse/browse"
COMMAND_BROWSE_PLAY_INPUT: Final = "browse/play_input"
COMMAND_BROWSE_PLAY_PRESET: Final = "browse/play_preset"
COMMAND_BROWSE_PLAY_STREAM: Final = "browse/play_stream"
COMMAND_BROWSE_ADD_TO_QUEUE: Final = "browse/add_to_queue"

# Player commands
COMMAND_GET_PLAYERS: Final = "player/get_players"
COMMAND_GET_PLAY_STATE: Final = "player/get_play_state"
COMMAND_SET_PLAY_STATE: Final = "player/set_play_state"
COMMAND_GET_NOW_PLAYING_MEDIA: Final = "player/get_now_playing_media"
COMMAND_GET_VOLUME: Final = "player/get_volume"
COMMAND_SET_VOLUME: Final = "player/set_volume"
COMMAND_GET_MUTE: Final = "player/get_mute"
COMMAND_SET_MUTE: Final = "player/set_mute"
COMMAND_VOLUME_UP: Final = "player/volume_up"
COMMAND_VOLUME_DOWN: Final = "player/volume_down"
COMMAND_TOGGLE_MUTE: Final = "player/toggle_mute"
COMMAND_GET_PLAY_MODE: Final = "player/get_play_mode"
COMMAND_SET_PLAY_MODE: Final = "player/set_play_mode"
COMMAND_CLEAR_QUEUE: Final = "player/clear_queue"
COMMAND_PLAY_NEXT: Final = "player/play_next"
COMMAND_PLAY_PREVIOUS: Final = "player/play_previous"
COMMAND_PLAY_QUICK_SELECT: Final = "player/play_quickselect"
COMMAND_SET_QUICK_SELECT: Final = "player/set_quickselect"
COMMAND_GET_QUICK_SELECTS: Final = "player/get_quickselects"

# Group commands
COMMAND_GET_GROUPS: Final = "group/get_groups"
COMMAND_SET_GROUP: Final = "group/set_group"
COMMAND_GET_GROUP_VOLUME: Final = "group/get_volume"
COMMAND_SET_GROUP_VOLUME: Final = "group/set_volume"
COMMAND_GET_GROUP_MUTE: Final = "group/get_mute"
COMMAND_SET_GROUP_MUTE: Final = "group/set_mute"
COMMAND_GROUP_TOGGLE_MUTE: Final = "group/toggle_mute"
COMMAND_GROUP_VOLUME_UP: Final = "group/volume_up"
COMMAND_GROUP_VOLUME_DOWN: Final = "group/volume_down"

# System commands
COMMAND_REGISTER_FOR_CHANGE_EVENTS: Final = "system/register_for_change_events"
COMMAND_HEART_BEAT: Final = "system/heart_beat"
COMMAND_ACCOUNT_CHECK: Final = "system/check_account"
COMMAND_SIGN_IN: Final = "system/sign_in"
COMMAND_SIGN_OUT: Final = "system/sign_out"

# Events
EVENT_PLAYER_STATE_CHANGED: Final = "event/player_state_changed"
EVENT_PLAYER_NOW_PLAYING_CHANGED: Final = "event/player_now_playing_changed"
EVENT_PLAYER_NOW_PLAYING_PROGRESS: Final = "event/player_now_playing_progress"
EVENT_PLAYER_VOLUME_CHANGED: Final = "event/player_volume_changed"
EVENT_PLAYER_PLAYBACK_ERROR: Final = "event/player_playback_error"
EVENT_PLAYER_QUEUE_CHANGED: Final = "event/player_queue_changed"
EVENT_GROUP_VOLUME_CHANGED: Final = "event/group_volume_changed"
EVENT_REPEAT_MODE_CHANGED: Final = "event/repeat_mode_changed"
EVENT_SHUFFLE_MODE_CHANGED: Final = "event/shuffle_mode_changed"
EVENT_SOURCES_CHANGED: Final = "event/sources_changed"
EVENT_PLAYERS_CHANGED: Final = "event/players_changed"
EVENT_GROUPS_CHANGED: Final = "event/groups_changed"
EVENT_USER_CHANGED: Final = "event/user_changed"

PLAYER_EVENTS: Final = (
    EVENT_PLAYER_STATE_CHANGED,
    EVENT_PLAYER_NOW_PLAYING_CHANGED,
    EVENT_PLAYER_NOW_PLAYING_PROGRESS,
    EVENT_PLAYER_VOLUME_CHANGED,
    EVENT_REPEAT_MODE_CHANGED,
    EVENT_SHUFFLE_MODE_CHANGED,
    EVENT_PLAYER_PLAYBACK_ERROR,
    EVENT_PLAYER_QUEUE_CHANGED,
)

GROUP_EVENTS: Final = EVENT_GROUP_VOLUME_CHANGED

HEOS_EVENTS: Final = (
    EVENT_SOURCES_CHANGED,
    EVENT_PLAYERS_CHANGED,
    EVENT_GROUPS_CHANGED,
    EVENT_USER_CHANGED,
)
