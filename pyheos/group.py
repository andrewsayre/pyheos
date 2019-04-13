"""Define the heos group module."""
from typing import Dict, Sequence

from .player import HeosPlayer


def create_group(data: dict, players: Dict[int, HeosPlayer]) -> 'HeosGroup':
    """Create a group from the data."""
    leader = None
    members = []
    for group_player in data['players']:
        player = players[int(group_player['pid'])]
        if group_player['role'] == 'leader':
            leader = player
        else:
            members.append(player)
    return HeosGroup(data['name'], int(data['gid']), leader, members)


class HeosGroup:
    """A group of players."""

    def __init__(self, name: str, group_id: int, leader: HeosPlayer,
                 members: Sequence[HeosPlayer]):
        """Init the group class."""
        self._name = name  # type: str
        self._group_id = group_id  # type: int
        self._leader = leader  #  type: HeosPlayer
        self._members = members  # type: Sequence[HeosPlayer]

    @property
    def name(self) -> str:
        """Get the name of the group."""
        return self._name

    @property
    def group_id(self) -> int:
        """Get the id of the group."""
        return self._group_id

    @property
    def leader(self) -> HeosPlayer:
        """Get the leader player of the group."""
        return self._leader

    @property
    def members(self) -> Sequence[HeosPlayer]:
        """Get the members of the group."""
        return self._members
