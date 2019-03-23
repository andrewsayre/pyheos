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
SOURCE_AUX_INPUT = 'AUX Input'
SOURCE_FAVORITES = 'Favorites'

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
SIGNAL_HEOS_UPDATED = "heos_updated"

BASE_URI = "heos://"

# Browse commands
COMMAND_BROWSE_GET_SOURCES = BASE_URI + "browse/get_music_sources"
COMMAND_BROWSE_BROWSE = BASE_URI + "browse/browse?sid={source_id}"
COMMAND_BROWSE_PLAY_INPUT = BASE_URI + "browse/play_input?pid={player_id}&" \
                                       "spid={source_player_id}&" \
                                       "input={input_name}"
COMMAND_BROWSE_PLAY_PRESET = \
    BASE_URI + "browse/play_preset?pid={player_id}&preset={preset}"
COMMAND_BROWSE_PLAY_STREAM = "browse/play_stream"

# Player commands
COMMAND_GET_PLAYERS = BASE_URI + "player/get_players"
COMMAND_GET_PLAY_STATE = BASE_URI + "player/get_play_state?pid={player_id}"
COMMAND_SET_PLAY_STATE = \
    BASE_URI + "player/set_play_state?pid={player_id}&state={state}"
COMMAND_GET_NOW_PLAYING_MEDIA = \
    BASE_URI + "player/get_now_playing_media?pid={player_id}"
COMMAND_GET_VOLUME = \
    BASE_URI + "player/get_volume?pid={player_id}"
COMMAND_SET_VOLUME = \
    BASE_URI + "player/set_volume?pid={player_id}&level={level}"
COMMAND_GET_MUTE = BASE_URI + "player/get_mute?pid={player_id}"
COMMAND_SET_MUTE = BASE_URI + "player/set_mute?pid={player_id}&state={state}"
COMMAND_VOLUME_UP = BASE_URI + "player/volume_up?pid={player_id}&step={step}"
COMMAND_VOLUME_DOWN = \
    BASE_URI + "player/volume_down?pid={player_id}&step={step}"
COMMAND_TOGGLE_MUTE = BASE_URI + "player/toggle_mute?pid={player_id}"
COMMAND_GET_PLAY_MODE = BASE_URI + "player/get_play_mode?pid={player_id}"
COMMAND_SET_PLAY_MODE = BASE_URI + "player/set_play_mode?pid={player_id}" \
                                   "&repeat={repeat}&shuffle={shuffle}"
COMMAND_CLEAR_QUEUE = BASE_URI + "player/clear_queue?pid={player_id}"
COMMAND_PLAY_NEXT = BASE_URI + "player/play_next?pid={player_id}"
COMMAND_PLAY_PREVIOUS = BASE_URI + "player/play_previous?pid={player_id}"


# System commands
COMMAND_REGISTER_FOR_CHANGE_EVENTS = \
    BASE_URI + "system/register_for_change_events?enable={enable}"

# Events
EVENT_PLAYER_STATE_CHANGED = "event/player_state_changed"
EVENT_PLAYER_NOW_PLAYING_CHANGED = "event/player_now_playing_changed"
EVENT_PLAYER_NOW_PLAYING_PROGRESS = "event/player_now_playing_progress"
EVENT_PLAYER_VOLUME_CHANGED = "event/player_volume_changed"
EVENT_REPEAT_MODE_CHANGED = "event/repeat_mode_changed"
EVENT_SHUFFLE_MODE_CHANGED = "event/shuffle_mode_changed"
EVENT_SOURCES_CHANGED = "event/sources_changed"
