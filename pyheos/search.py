"""Define the search module."""

import re
from collections.abc import Sequence
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Final, Optional, cast

from pyheos import command as c
from pyheos.media import MediaItem
from pyheos.message import HeosMessage

if TYPE_CHECKING:
    from pyheos.heos import Heos

TUPLE_MATCHER: Final = re.compile(r"\(([0-9,-]+)\)")


@dataclass
class SearchCriteria:
    """Define the search criteria for a music source."""

    name: str
    criteria_id: int
    wildcard: bool
    container_id: str | None = None
    playable: bool = False

    @staticmethod
    def _from_data(data: dict[str, str]) -> "SearchCriteria":
        """Create a new instance from the provided data."""
        return SearchCriteria(
            name=data[c.ATTR_NAME],
            criteria_id=int(data[c.ATTR_SEARCH_CRITERIA_ID]),
            wildcard=data[c.ATTR_WILDCARD] == c.VALUE_YES,
            container_id=data.get(c.ATTR_CONTAINER_ID),
            playable=data.get(c.ATTR_PLAYABLE) == c.VALUE_YES,
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

    @staticmethod
    def _from_message(message: HeosMessage, heos: "Heos") -> "SearchResult":
        """Create a new instance from a message."""
        source_id = message.get_message_value_int(c.ATTR_SOURCE_ID)

        return SearchResult(
            heos=heos,
            source_id=source_id,
            criteria_id=message.get_message_value_int(c.ATTR_SEARCH_CRITERIA_ID),
            search=message.get_message_value(c.ATTR_SEARCH),
            returned=message.get_message_value_int(c.ATTR_RETURNED),
            count=message.get_message_value_int(c.ATTR_COUNT),
            items=list(
                [
                    MediaItem.from_data(item, source_id, None, heos)
                    for item in cast(Sequence[dict[str, str]], message.payload)
                ]
            ),
        )


@dataclass
class MultiSearchResult:
    """Define the results of a multi-search."""

    source_ids: Sequence[int]
    criteria_ids: Sequence[int]
    search: str
    returned: int
    count: int
    items: Sequence[MediaItem] = field(repr=False, hash=False, compare=False)
    statistics: Sequence["SearchStatistic"] = field(
        repr=False, hash=False, compare=False
    )
    errors: Sequence["SearchStatistic"] = field(repr=False, hash=False, compare=False)
    heos: Optional["Heos"] = field(repr=False, hash=False, compare=False, default=None)

    @staticmethod
    def _from_message(message: HeosMessage, heos: "Heos") -> "MultiSearchResult":
        """Create a new instance from a message."""
        source_ids = message.get_message_value(c.ATTR_SOURCE_ID).split(",")
        criteria_ids = message.get_message_value(c.ATTR_SEARCH_CRITERIA_ID).split(",")
        statisics = SearchStatistic._from_string(
            message.get_message_value(c.ATTR_STATS)
        )
        items: list[MediaItem] = []
        # In order to determine the source_id of the result, we match up the index with how many items were returned for a given source
        payload = cast(list[dict[str, str]], message.payload)
        index = 0
        for stat in statisics:
            assert stat.returned is not None
            for _ in range(stat.returned):
                items.append(
                    MediaItem.from_data(payload[index], stat.source_id, heos=heos)
                )
                index += 1

        return MultiSearchResult(
            heos=heos,
            source_ids=[int(source_id) for source_id in source_ids],
            criteria_ids=[int(criteria_id) for criteria_id in criteria_ids],
            search=message.get_message_value(c.ATTR_SEARCH),
            returned=message.get_message_value_int(c.ATTR_RETURNED),
            count=message.get_message_value_int(c.ATTR_COUNT),
            items=items,
            statistics=statisics,
            errors=SearchStatistic._from_string(
                message.get_message_value(c.ATTR_ERROR_NUMBER)
            ),
        )


@dataclass
class SearchStatistic:
    """Define the search statistics."""

    source_id: int
    criteria_id: int
    returned: int | None = None
    count: int | None = None
    error_number: int | None = None

    @staticmethod
    def _from_string(data: str) -> list["SearchStatistic"]:
        """Create a new instance from the provided tuple."""
        # stats=(10,2,2,2),(10,1,0,0),(1,0,57,57),(10,3,15,15)
        # errno=(13,0,2),(8,0,-1061)
        stats: list[SearchStatistic] = []
        matches = TUPLE_MATCHER.findall(data)
        for match in matches:
            stats_tuple = match.split(",")

            if len(stats_tuple) == 3:
                stats.append(
                    SearchStatistic(
                        source_id=int(stats_tuple[0]),
                        criteria_id=int(stats_tuple[1]),
                        error_number=int(stats_tuple[2]),
                    )
                )
            else:
                stats.append(
                    SearchStatistic(
                        source_id=int(stats_tuple[0]),
                        criteria_id=int(stats_tuple[1]),
                        returned=int(stats_tuple[2]),
                        count=int(stats_tuple[3]),
                    )
                )
        return stats
