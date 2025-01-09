"""Define the search module."""

from dataclasses import dataclass

from pyheos import const


@dataclass
class SearchCriteria:
    """Define the search criteria for a music source."""

    name: str
    search_criteria_id: int
    wildcard: bool
    container_id: str | None = None
    playable: bool = False

    @classmethod
    def _from_data(cls, data: dict[str, str]) -> "SearchCriteria":
        """Create a new instance from the provided data."""
        return SearchCriteria(
            name=data[const.ATTR_NAME],
            search_criteria_id=int(data[const.ATTR_SEARCH_CRITERIA_ID]),
            wildcard=data[const.ATTR_WILDCARD] == const.VALUE_YES,
            container_id=data.get(const.ATTR_CONTAINER_ID),
            playable=data.get(const.ATTR_PLAYABLE) == const.VALUE_YES,
        )
