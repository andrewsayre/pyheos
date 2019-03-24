"""Define consts for the pyheos package."""

__title__ = "pyheos"
__version__ = "0.0.1"

CLI_PORT = 1255
DEFAULT_TIMEOUT = 5
DEFAULT_STEP = 5

PLAY_STATE_PLAY = 'play'
PLAY_STATE_PAUSE = 'pause'
PLAY_STATE_STOP = 'stop'
VALID_PLAY_STATES = (
    PLAY_STATE_PLAY,
    PLAY_STATE_PAUSE,
    PLAY_STATE_STOP
)

REPEAT_ON_ALL = "on_all"
REPEAT_ON_ONE = "on_one"
REPEAT_OFF = "off"
VALID_REPEAT_MODES = (
    REPEAT_ON_ALL,
    REPEAT_ON_ONE,
    REPEAT_OFF
)

# Music Source Types
TYPE_MUSIC_SERVICE = 'music_service'
TYPE_STATION = 'station'
TYPE_HEOS_SERVICE = 'heos_service'

# Music Sources
MUSIC_SOURCE_PANDORA = 1
MUSIC_SOURCE_RHAPSODY = 2
MUSIC_SOURCE_TUNEIN = 3
MUSIC_SOURCE_SPOTIFY = 4
MUSIC_SOURCE_DEEZER = 5
MUSIC_SOURCE_NAPSTER = 6
MUSIC_SOURCE_IHEARTRADIO = 7
MUSIC_SOURCE_SIRIUSXM = 8
MUSIC_SOURCE_SOUNDCLOUD = 9
MUSIC_SOURCE_TIDAL = 10
MUSIC_SOURCE_RDIO = 12
MUSIC_SOURCE_AMAZON = 13
MUSIC_SOURCE_MOODMIX = 15
MUSIC_SOURCE_JUKE = 16
MUSIC_SOURCE_QQMUSIC = 18
MUSIC_SOURCE_LOCAL_MUSIC = 1024
MUSIC_SOURCE_PLAYLISTS = 1025
MUSIC_SOURCE_HISTORY = 1026
MUSIC_SOURCE_AUX_INPUT = 1027
MUSIC_SOURCE_FAVORITES = 1028

# Inputs
INPUT_AUX_IN_1 = "inputs/aux_in_1"
INPUT_AUX_IN_2 = "inputs/aux_in_2"
INPUT_AUX_IN_3 = "inputs/aux_in_3"
INPUT_AUX_IN_4 = "inputs/aux_in_4"
INPUT_AUX_IN_SINGLE = "inputs/aux_single"
INPUT_AUX1 = "inputs/aux1"
INPUT_AUX2 = "inputs/aux2"
INPUT_AUX3 = "inputs/aux3"
INPUT_AUX4 = "inputs/aux4"
INPUT_AUX5 = "inputs/aux5"
INPUT_AUX6 = "inputs/aux6"
INPUT_AUX7 = "inputs/aux7"
INPUT_LINE_IN_1 = "inputs/line_in_1"
INPUT_LINE_IN_2 = "inputs/line_in_2"
INPUT_LINE_IN_3 = "inputs/line_in_3"
INPUT_LINE_IN_4 = "inputs/line_in_4"
INPUT_COAX_IN_1 = "inputs/coax_in_1"
INPUT_COAX_IN_2 = "inputs/coax_in_2"
INPUT_OPTICAL_IN_1 = "inputs/optical_in_1"
INPUT_OPTICAL_IN_2 = "inputs/optical_in_2"
INPUT_HDMI_IN_1 = "inputs/hdmi_in_1"
INPUT_HDMI_IN_2 = "inputs/hdmi_in_2"
INPUT_HDMI_IN_3 = "inputs/hdmi_in_3"
INPUT_HDMI_IN_4 = "inputs/hdmi_in_4"
INPUT_HDMI_ARC_1 = "inputs/hdmi_arc_1"
INPUT_CABLE_SAT = "inputs/cable_sat"
INPUT_DVD = "inputs/dvd"
INPUT_BLURAY = "inputs/bluray"
INPUT_GAME = "inputs/game"
INPUT_MEDIA_PLAYER = "inputs/mediaplayer"
INPUT_CD = "inputs/cd"
INPUT_TUNER = "inputs/tuner"
INPUT_HD_RADIO = "inputs/hdradio"
INPUT_TV_AUDIO = "inputs/tvaudio"
INPUT_PHONO = "inputs/phono"
INPUT_USB_AC = "inputs/usbdac"
INPUT_ANALOG = "inputs/analog"

VALID_INPUTS = (
    INPUT_AUX_IN_1, INPUT_AUX_IN_2, INPUT_AUX_IN_3, INPUT_AUX_IN_4,
    INPUT_AUX_IN_SINGLE, INPUT_AUX1, INPUT_AUX2, INPUT_AUX3, INPUT_AUX4,
    INPUT_AUX5, INPUT_AUX6, INPUT_AUX7, INPUT_LINE_IN_1, INPUT_LINE_IN_2,
    INPUT_LINE_IN_3, INPUT_LINE_IN_4, INPUT_COAX_IN_1, INPUT_COAX_IN_2,
    INPUT_OPTICAL_IN_1, INPUT_OPTICAL_IN_2, INPUT_HDMI_IN_1, INPUT_HDMI_IN_2,
    INPUT_HDMI_IN_3, INPUT_HDMI_IN_4, INPUT_HDMI_ARC_1, INPUT_CABLE_SAT,
    INPUT_DVD, INPUT_BLURAY, INPUT_GAME, INPUT_MEDIA_PLAYER, INPUT_CD,
    INPUT_TUNER, INPUT_HD_RADIO, INPUT_TV_AUDIO, INPUT_PHONO, INPUT_USB_AC,
    INPUT_ANALOG)

# Signals
SIGNAL_PLAYER_UPDATED = "player_updated"
SIGNAL_GROUP_UPDATED = "group_updated"
SIGNAL_HEOS_UPDATED = "heos_updated"

BASE_URI = "heos://"

# Browse commands
COMMAND_BROWSE_GET_SOURCES = "browse/get_music_sources"
COMMAND_BROWSE_BROWSE = "browse/browse"
COMMAND_BROWSE_PLAY_INPUT = "browse/play_input"
COMMAND_BROWSE_PLAY_PRESET = "browse/play_preset"
COMMAND_BROWSE_PLAY_STREAM = "browse/play_stream"

# Player commands
COMMAND_GET_PLAYERS = "player/get_players"
COMMAND_GET_PLAY_STATE = "player/get_play_state"
COMMAND_SET_PLAY_STATE = "player/set_play_state"
COMMAND_GET_NOW_PLAYING_MEDIA = "player/get_now_playing_media"
COMMAND_GET_VOLUME = "player/get_volume"
COMMAND_SET_VOLUME = "player/set_volume"
COMMAND_GET_MUTE = "player/get_mute"
COMMAND_SET_MUTE = "player/set_mute"
COMMAND_VOLUME_UP = "player/volume_up"
COMMAND_VOLUME_DOWN = "player/volume_down"
COMMAND_TOGGLE_MUTE = "player/toggle_mute"
COMMAND_GET_PLAY_MODE = "player/get_play_mode"
COMMAND_SET_PLAY_MODE = "player/set_play_mode"
COMMAND_CLEAR_QUEUE = "player/clear_queue"
COMMAND_PLAY_NEXT = "player/play_next"
COMMAND_PLAY_PREVIOUS = "player/play_previous"


# System commands
COMMAND_REGISTER_FOR_CHANGE_EVENTS = "system/register_for_change_events"

# Events
EVENT_PLAYER_STATE_CHANGED = "event/player_state_changed"
EVENT_PLAYER_NOW_PLAYING_CHANGED = "event/player_now_playing_changed"
EVENT_PLAYER_NOW_PLAYING_PROGRESS = "event/player_now_playing_progress"
EVENT_PLAYER_VOLUME_CHANGED = "event/player_volume_changed"
EVENT_PLAYER_PLAYBACK_ERROR = "event/player_playback_error"
EVENT_PLAYER_QUEUE_CHANGED = "event/player_queue_changed"
EVENT_GROUP_VOLUME_CHANGED = "event/group_volume_changed"
EVENT_REPEAT_MODE_CHANGED = "event/repeat_mode_changed"
EVENT_SHUFFLE_MODE_CHANGED = "event/shuffle_mode_changed"
EVENT_SOURCES_CHANGED = "event/sources_changed"
EVENT_PLAYERS_CHANGED = "event/players_changed"
EVENT_GROUPS_CHANGED = "event/groups_changed"
EVENT_USER_CHANGED = "event/user_changed"

PLAYER_EVENTS = (
    EVENT_PLAYER_STATE_CHANGED, EVENT_PLAYER_NOW_PLAYING_CHANGED,
    EVENT_PLAYER_NOW_PLAYING_PROGRESS, EVENT_PLAYER_VOLUME_CHANGED,
    EVENT_REPEAT_MODE_CHANGED, EVENT_SHUFFLE_MODE_CHANGED,
    EVENT_PLAYER_PLAYBACK_ERROR, EVENT_PLAYER_QUEUE_CHANGED
)

GROUP_EVENTS = (
    EVENT_GROUP_VOLUME_CHANGED
)

HEOS_EVENTS = (
    EVENT_SOURCES_CHANGED, EVENT_PLAYERS_CHANGED, EVENT_GROUPS_CHANGED,
    EVENT_USER_CHANGED
)
