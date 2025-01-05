"""Define the HEOS command module."""

from typing import Final

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
COMMAND_REBOOT: Final = "system/reboot"
COMMAND_SIGN_IN: Final = "system/sign_in"
COMMAND_SIGN_OUT: Final = "system/sign_out"
