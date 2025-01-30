"""Define the common module."""

from dataclasses import dataclass, field


@dataclass
class ChangeSummary:
    """Define a summary of player or group changes.

    Args:
        added_ids: The list of identifiers that have been added.
        removed_ids: The list of identifiers that have been removed.
        changed_ids: A dictionary that maps the previous ids to the updated ids
    """

    added_ids: list[int] = field(default_factory=list)
    removed_ids: list[int] = field(default_factory=list)
    changed_ids: dict[int, int] = field(default_factory=dict)
