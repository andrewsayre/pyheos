"""Define the HEOS command module."""

import logging
from enum import StrEnum
from typing import Any, Final, TypeVar

from pyheos.const import REPORT_ISSUE_TEXT

# Browse commands
COMMAND_BROWSE_ADD_TO_QUEUE: Final = "browse/add_to_queue"
COMMAND_BROWSE_BROWSE: Final = "browse/browse"
COMMAND_BROWSE_DELETE__PLAYLIST: Final = "browse/delete_playlist"
COMMAND_BROWSE_GET_SEARCH_CRITERIA: Final = "browse/get_search_criteria"
COMMAND_BROWSE_GET_SOURCE_INFO: Final = "browse/get_source_info"
COMMAND_BROWSE_GET_SOURCES: Final = "browse/get_music_sources"
COMMAND_BROWSE_MULTI_SEARCH: Final = "browse/multi_search"
COMMAND_BROWSE_PLAY_INPUT: Final = "browse/play_input"
COMMAND_BROWSE_PLAY_PRESET: Final = "browse/play_preset"
COMMAND_BROWSE_PLAY_STREAM: Final = "browse/play_stream"
COMMAND_BROWSE_RENAME_PLAYLIST: Final = "browse/rename_playlist"
COMMAND_BROWSE_RETRIEVE_METADATA: Final = "browse/retrieve_metadata"
COMMAND_BROWSE_SEARCH: Final = "browse/search"
COMMAND_BROWSE_SET_SERVICE_OPTION: Final = "browse/set_service_option"

# Player commands
COMMAND_CHECK_UPDATE: Final = "player/check_update"
COMMAND_CLEAR_QUEUE: Final = "player/clear_queue"
COMMAND_GET_MUTE: Final = "player/get_mute"
COMMAND_GET_NOW_PLAYING_MEDIA: Final = "player/get_now_playing_media"
COMMAND_GET_PLAY_MODE: Final = "player/get_play_mode"
COMMAND_GET_PLAY_STATE: Final = "player/get_play_state"
COMMAND_GET_PLAYER_INFO: Final = "player/get_player_info"
COMMAND_GET_PLAYERS: Final = "player/get_players"
COMMAND_GET_QUEUE: Final = "player/get_queue"
COMMAND_GET_QUICK_SELECTS: Final = "player/get_quickselects"
COMMAND_GET_VOLUME: Final = "player/get_volume"
COMMAND_MOVE_QUEUE_ITEM: Final = "player/move_queue_item"
COMMAND_PLAY_NEXT: Final = "player/play_next"
COMMAND_PLAY_PREVIOUS: Final = "player/play_previous"
COMMAND_PLAY_QUEUE: Final = "player/play_queue"
COMMAND_PLAY_QUICK_SELECT: Final = "player/play_quickselect"
COMMAND_REMOVE_FROM_QUEUE: Final = "player/remove_from_queue"
COMMAND_SAVE_QUEUE: Final = "player/save_queue"
COMMAND_SET_MUTE: Final = "player/set_mute"
COMMAND_SET_PLAY_MODE: Final = "player/set_play_mode"
COMMAND_SET_PLAY_STATE: Final = "player/set_play_state"
COMMAND_SET_QUICK_SELECT: Final = "player/set_quickselect"
COMMAND_SET_VOLUME: Final = "player/set_volume"
COMMAND_TOGGLE_MUTE: Final = "player/toggle_mute"
COMMAND_VOLUME_DOWN: Final = "player/volume_down"
COMMAND_VOLUME_UP: Final = "player/volume_up"

# Group commands
COMMAND_GET_GROUP_INFO: Final = "group/get_group_info"
COMMAND_GET_GROUP_MUTE: Final = "group/get_mute"
COMMAND_GET_GROUP_VOLUME: Final = "group/get_volume"
COMMAND_GET_GROUPS: Final = "group/get_groups"
COMMAND_GROUP_TOGGLE_MUTE: Final = "group/toggle_mute"
COMMAND_GROUP_VOLUME_DOWN: Final = "group/volume_down"
COMMAND_GROUP_VOLUME_UP: Final = "group/volume_up"
COMMAND_SET_GROUP: Final = "group/set_group"
COMMAND_SET_GROUP_MUTE: Final = "group/set_mute"
COMMAND_SET_GROUP_VOLUME: Final = "group/set_volume"

# System commands
COMMAND_ACCOUNT_CHECK: Final = "system/check_account"
COMMAND_HEART_BEAT: Final = "system/heart_beat"
COMMAND_REGISTER_FOR_CHANGE_EVENTS: Final = "system/register_for_change_events"
COMMAND_REBOOT: Final = "system/reboot"
COMMAND_SIGN_IN: Final = "system/sign_in"
COMMAND_SIGN_OUT: Final = "system/sign_out"


_LOGGER: Final = logging.getLogger(__name__)


TStrEnum = TypeVar("TStrEnum", bound=StrEnum)


def parse_enum(
    key: str, data: dict[str, Any], enum_type: type[TStrEnum], default: TStrEnum
) -> TStrEnum:
    """Parse an enum value from the provided data. This is a safe operation that will return the default value if the key is missing or the value is not recognized."""
    value = data.get(key)
    if value is None:
        return default
    try:
        return enum_type(value)
    except ValueError:
        _LOGGER.warning(
            "Unrecognized '%s' value: '%s', using default value: '%s'. Full data: %s. %s.",
            key,
            value,
            default,
            data,
            REPORT_ISSUE_TEXT,
        )
        return default
