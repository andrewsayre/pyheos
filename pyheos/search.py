"""Define the search module."""

from collections.abc import Sequence
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Optional, cast

from pyheos import const
from pyheos.media import MediaItem
from pyheos.message import HeosMessage

if TYPE_CHECKING:
    from pyheos.heos import Heos


@dataclass
class SearchCriteria:
    """Define the search criteria for a music source."""

    name: str
    criteria_id: int
    wildcard: bool
    container_id: str | None = None
    playable: bool = False

    @classmethod
    def _from_data(cls, data: dict[str, str]) -> "SearchCriteria":
        """Create a new instance from the provided data."""
        return SearchCriteria(
            name=data[const.ATTR_NAME],
            criteria_id=int(data[const.ATTR_SEARCH_CRITERIA_ID]),
            wildcard=data[const.ATTR_WILDCARD] == const.VALUE_YES,
            container_id=data.get(const.ATTR_CONTAINER_ID),
            playable=data.get(const.ATTR_PLAYABLE) == const.VALUE_YES,
        )


@dataclass
class SearchResult:
    """Define the search result."""

    source_id: int
    criteria_id: int
    search: str
    returned: int
    count: int
    items: Sequence[MediaItem] = field(repr=False, hash=False, compare=False)
    heos: Optional["Heos"] = field(repr=False, hash=False, compare=False, default=None)

    @classmethod
    def _from_message(cls, message: HeosMessage, heos: "Heos") -> "SearchResult":
        """Create a new instance from a message."""
        source_id = message.get_message_value_int(const.ATTR_SOURCE_ID)

        return SearchResult(
            heos=heos,
            source_id=source_id,
            criteria_id=message.get_message_value_int(const.ATTR_SEARCH_CRITERIA_ID),
            search=message.get_message_value(const.ATTR_SEARCH),
            returned=message.get_message_value_int(const.ATTR_RETURNED),
            count=message.get_message_value_int(const.ATTR_COUNT),
            items=list(
                [
                    MediaItem.from_data(item, source_id, None, heos)
                    for item in cast(Sequence[dict[str, str]], message.payload)
                ]
            ),
        )
