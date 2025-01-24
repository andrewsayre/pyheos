"""Define abstract base classes for HEOS."""

from abc import ABC
from typing import Any


class RemoveHeosFieldABC(ABC):
    """Define an abstract base class that removes the 'heos' from dataclass's fields list to prevent serialization."""

    def __post_init__(self, *args: Any, **kwargs: Any) -> None:
        """Post initialize the player."""
        # Prevent the heos instance from being serialized
        fields = self.__dataclass_fields__.copy()  # type: ignore[has-type] # pylint: disable=access-member-before-definition
        del fields["heos"]
        self.__dataclass_fields__ = fields
