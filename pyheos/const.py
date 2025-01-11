"""Define consts for the pyheos package.

This module only contains constants needed to interact with the library (that are exported). Constants only
used internally are located in the modules where they are used.
"""

from typing import Final

DEFAULT_TIMEOUT: Final = 10.0
DEFAULT_RECONNECT_DELAY: Final = 10.0
DEFAULT_RECONNECT_ATTEMPTS: Final = 0  # Unlimited
DEFAULT_HEART_BEAT: Final = 10.0
DEFAULT_STEP: Final = 5

# Command error codes (keep discrete values as we do not control the list)
ERROR_UNREGONIZED_COMMAND: Final = 1
ERROR_INVALID_ID: Final = 2
ERROR_WRONG_ARGUMENTS: Final = 3
ERROR_DATA_NOT_AVAILABLE: Final = 4
ERROR_RESOURCE_NOT_AVAILABLE: Final = 5
ERROR_INVALID_CREDNETIALS: Final = 6
ERROR_COMMAND_NOT_EXECUTED: Final = 7
ERROR_USER_NOT_LOGGED_IN: Final = 8
ERROR_PARAMETER_OUT_OF_RANGE: Final = 9
ERROR_USER_NOT_FOUND: Final = 10
ERROR_INTERNAL: Final = 11
ERROR_SYSTEM_ERROR: Final = 12
ERROR_PROCESSING_PREVIOUS_COMMAND: Final = 13
ERROR_MEDIA_CANNOT_BE_PLAYED: Final = 14
ERROR_OPTION_NOTP_SUPPORTED: Final = 15
ERROR_TOO_MANY_COMMANDS_IN_QUEUE: Final = 16
ERROR_SKIP_LIMIT_REACHED: Final = 17

# Document system error codes (keep discrete values as we do not control the list)
SYSTEM_ERROR_REMOTE_SERVICE_ERROR: Final = -9
SYSTEM_ERROR_SERVICE_NOT_REGISTERED: Final = -1061
SYSTEM_ERROR_USER_NOT_LOGGED_IN: Final = -1063
SYSTEM_ERROR_USER_NOT_FOUND: Final = -1056
SYSTEM_ERROR_CONTENT_AUTHENTICATION_ERROR: Final = -1201
SYSTEM_ERROR_CONTENT_AUTHORIZATION_ERROR: Final = -1232
SYSTEM_ERROR_ACCOUNT_PARAMETERS_INVALID: Final = -1239

# Search Crtieria Container IDs (keep discrete values as we do not control the list)
SEARCHED_TRACKS: Final = "SEARCHED_TRACKS-"

# Music Sources (keep discrete values as we do not control the list)
MUSIC_SOURCE_CONNECT: Final = 0  # TIDAL Connect // possibly Spotify Connect as well (?)
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

# Inputs (keep discrete values as we do not control the list)
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
INPUT_SOURCE_1: Final = "inputs/source1"
INPUT_SOURCE_2: Final = "inputs/source2"
INPUT_SOURCE_3: Final = "inputs/source3"
INPUT_SOURCE_4: Final = "inputs/source4"
INPUT_SOURCE_5: Final = "inputs/source5"
INPUT_SOURCE_6: Final = "inputs/source6"
INPUT_SOURCE_7: Final = "inputs/source7"
INPUT_SOURCE_8: Final = "inputs/source8"
INPUT_SOURCE_9: Final = "inputs/source9"
INPUT_SOURCE_10: Final = "inputs/source10"
INPUT_SOURCE_11: Final = "inputs/source11"
INPUT_SOURCE_12: Final = "inputs/source12"
INPUT_SOURCE_13: Final = "inputs/source13"
INPUT_SOURCE_14: Final = "inputs/source14"
INPUT_SOURCE_15: Final = "inputs/source15"
INPUT_SOURCE_16: Final = "inputs/source16"
INPUT_SOURCE_17: Final = "inputs/source17"
INPUT_SOURCE_18: Final = "inputs/source18"
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
    INPUT_SOURCE_1,
    INPUT_SOURCE_2,
    INPUT_SOURCE_3,
    INPUT_SOURCE_4,
    INPUT_SOURCE_5,
    INPUT_SOURCE_6,
    INPUT_SOURCE_7,
    INPUT_SOURCE_8,
    INPUT_SOURCE_9,
    INPUT_SOURCE_10,
    INPUT_SOURCE_11,
    INPUT_SOURCE_12,
    INPUT_SOURCE_13,
    INPUT_SOURCE_14,
    INPUT_SOURCE_15,
    INPUT_SOURCE_16,
    INPUT_SOURCE_17,
    INPUT_SOURCE_18,
    INPUT_SOURCE_18,
    INPUT_TUNER,
    INPUT_TV_AUDIO,
    INPUT_TV,
    INPUT_USB_AC,
)

# Service options (keep discrete values as we do not control the list)
SERVICE_OPTION_ADD_TRACK_TO_LIBRARY: Final = 1
SERVICE_OPTION_ADD_ALBUM_TO_LIBRARY: Final = 2
SERVICE_OPTION_ADD_STATION_TO_LIBRARY: Final = 3
SERVICE_OPTION_ADD_PLAYLIST_TO_LIBRARY: Final = 4
SERVICE_OPTION_REMOVE_TRACK_FROM_LIBRARY: Final = 5
SERVICE_OPTION_REMOVE_ALBUM_FROM_LIBRARY: Final = 6
SERVICE_OPTION_REMOVE_STATION_FROM_LIBRARY: Final = 7
SERVICE_OPTION_REMOVE_PLAYLIST_FROM_LIBRARY: Final = 8
SERVICE_OPTION_THUMBS_UP: Final = 11
SERVICE_OPTION_THUMBS_DOWN: Final = 12
SERVICE_OPTION_CREATE_NEW_STATION_BY_SEARCH_CRITERIA: Final = 13
SERVICE_OPTION_ADD_TO_FAVORITES: Final = 19
SERVICE_OPTION_REMOVE_FROM_FAVORITES: Final = 20

# HEOS Events (keep discrete values as we do not control the list)
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
