"""Define the heos response module."""
from typing import Any, Dict, Optional
from urllib.parse import parse_qsl


class HeosResponse:
    """Define a HEOS response representation."""

    def __init__(self, data: Optional[dict] = None):
        """Init a new instance of the heos response."""
        self._raw_data = None   # type: dict
        self._command = None   # type: str
        self._result = None    # type: bool
        self._message = None   # type: dict
        self._payload = None   # type: dict
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
        self._command = heos['command']
        self._result = heos.get('result') == 'success'
        raw_message = heos.get('message')
        if raw_message:
            self._message = dict(parse_qsl(raw_message, True))
        self._payload = data.get('payload')

    @property
    def is_under_process(self) -> bool:
        """Return True if the response represents a command under process."""
        return self._message and 'command under process' in self._message

    @property
    def is_event(self) -> bool:
        """Return True if the response is an event."""
        return self.command.startswith("event/")

    @property
    def command(self) -> str:
        """Get the command of the response."""
        return self._command

    @property
    def result(self) -> bool:
        """Get the result."""
        return self._result

    @property
    def payload(self) -> Optional[Dict]:
        """Get the payload of the message."""
        return self._payload

    def get_message(self, key: str) -> Any:
        """Get message paramter by key."""
        if self._message:
            return self._message.get(key)

    def has_message(self, key: str) -> bool:
        """Determine if the key within the message."""
        return self._message and key in self._message

    def get_player_id(self) -> int:
        """Get the player_id from the message."""
        return int(self._message['pid'])

    def get_group_id(self) -> int:
        """Get the group_id from the message."""
        return int(self._message['gid'])

    def raise_for_result(self):
        """Raise an error if result is not successful."""
        if self.result:
            return
        text = self.get_message('text')
        system_error_number = self.get_message('syserrno')
        if system_error_number:
            text += " " + system_error_number
        error_id = self.get_message('eid')
        error_id = int(error_id) if error_id else error_id
        raise CommandError(self._command, text, error_id)


class CommandError(Exception):
    """Define an error command response."""

    def __init__(self, command: str, text: str, error_id: int):
        """Create a new instance of the error."""
        self._command = command
        self._error_text = text
        self._error_id = error_id
        super().__init__("{} ({})".format(text, error_id))

    @property
    def command(self) -> str:
        """Get the command that raised the error."""
        return self._command

    @property
    def error_text(self) -> str:
        """Get the error text from the response."""
        return self._error_text

    @property
    def error_id(self) -> int:
        """Return the error id."""
        return self._error_id
