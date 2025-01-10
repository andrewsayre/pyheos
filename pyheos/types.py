"""Define the types module for HEOS."""

from enum import IntEnum


class AddCriteriaType(IntEnum):
    """Define the add to queue options."""

    PLAY_NOW = 1
    PLAY_NEXT = 2
    ADD_TO_END = 3
    REPLACE_AND_PLAY = 4
