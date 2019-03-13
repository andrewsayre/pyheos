"""Define consts for the pyheos package."""

__title__ = "pyheos"
__version__ = "0.0.1"

CLI_PORT = 1255
DEFAULT_TIMEOUT = 2

BASE_URI = "heos://"

PLAY_STATE_PLAY = 'play'
PLAY_STATE_PAUSE = 'pause'
PLAY_STATE_STOP = 'stop'
VALID_PLAY_STATES = (
    PLAY_STATE_PLAY,
    PLAY_STATE_PAUSE,
    PLAY_STATE_STOP
)

SIGNAL_PLAYER_UPDATED = "player_updated"

# Player commands
COMMAND_GET_PLAYERS = BASE_URI + "player/get_players"
COMMAND_GET_PLAY_STATE = BASE_URI + "player/get_play_state?pid={player_id}"
COMMAND_SET_PLAY_STATE = \
    BASE_URI + "player/set_play_state?pid={player_id}&state={state}"
COMMAND_GET_NOW_PLAYING_MEDIA = \
    BASE_URI + "player/get_now_playing_media?pid={player_id}"

# System commands
COMMAND_REGISTER_FOR_CHANGE_EVENTS = \
    BASE_URI + "system/register_for_change_events?enable={enable}"

# Events
EVENT_PLAYER_STATE_CHANGED = "event/player_state_changed"
EVENT_PLAYER_NOW_PLAYING_CHANGED = "event/player_now_playing_changed"
