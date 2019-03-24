"""Define the heos response module."""
from typing import Any, Optional
from urllib.parse import parse_qsl


class HeosResponse:
    """Define a HEOS response representation."""

    def __init__(self, data: Optional[dict] = None):
        """Init a new instance of the heos response."""
        self._raw_data = None   # type: dict
        self.command = None   # type: str
        self.result = None    # type: bool
        self.message = None   # type: dict
        self.payload = None   # type: dict
        if data:
            self.from_json(data)

    def __str__(self):
        """Get a user-readable representation of the response."""
        return "{}".format(self._raw_data['heos'])

    def __repr__(self):
        """Get a debug representation of the player."""
        return "{}".format(self._raw_data)

    def from_json(self, data: dict):
        """Populate the response from json."""
        self._raw_data = data
        heos = data['heos']
        self.command = heos['command']
        self.result = heos.get('result') == 'success'
        raw_message = heos.get('message')
        if raw_message:
            self.message = dict(parse_qsl(raw_message, True))
        self.payload = data.get('payload')

    @property
    def is_under_process(self) -> bool:
        """Return True if the response represents a command under process."""
        return self.message and 'command under process' in self.message

    @property
    def is_event(self) -> bool:
        """Return True if the response is an event."""
        return self.command.startswith("event/")

    def get_message(self, key: str) -> Any:
        """Get message paramter by key."""
        if self.message:
            return self.message.get(key)

    def get_player_id(self) -> int:
        """Get the player_id from the message."""
        return int(self.message['pid'])

    def get_group_id(self) -> int:
        """Get the group_id from the message."""
        return int(self.message['gid'])
