"""Define the heos response module."""

from typing import Any, Optional
from urllib.parse import parse_qsl

from .error import CommandFailedError


class HeosResponse:
    """Define a HEOS response representation."""

    def __init__(self, data: dict) -> None:
        """Init a new instance of the heos response."""
        self._raw_data: dict = data
        heos = data["heos"]
        self._command: str = str(heos["command"])
        self._result: bool = str(heos.get("result")) == "success"
        self._message: dict[str, str] = {}
        if raw_message := heos.get("message"):
            self._message = dict(parse_qsl(raw_message, True))
        self._payload: list | dict | None = data.get("payload")

    def __str__(self):
        """Get a user-readable representation of the response."""
        return str(self._raw_data["heos"])

    def __repr__(self):
        """Get a debug representation of the player."""
        return str(self._raw_data)

    @property
    def is_under_process(self) -> bool:
        """Return True if the response represents a command under process."""
        return "command under process" in self._message

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
    def payload(self) -> list | dict | None:
        """Get the payload of the message."""
        return self._payload

    def get_message(self, key: str) -> Any:
        """Get message parameter by key."""
        if self._message:
            return self._message.get(key)

    def has_message(self, key: str) -> bool:
        """Determine if the key within the message."""
        return key in self._message

    def get_player_id(self) -> int:
        """Get the player_id from the message."""
        if player_id := self._message.get("pid"):
            return int(player_id)
        raise ValueError("Response does not contain a player id.")

    def get_group_id(self) -> int:
        """Get the group_id from the message."""
        if group_id := self._message.get("gid"):
            return int(group_id)
        raise ValueError("Response does not contain a group id.")

    def raise_for_result(self) -> None:
        """Raise an error if result is not successful."""
        if self.result:
            return
        text = self.get_message("text")
        system_error_number = self.get_message("syserrno")
        if system_error_number:
            text += " " + system_error_number
        error_id = self.get_message("eid")
        error_id = int(error_id) if error_id else error_id
        raise CommandFailedError(self._command, text, error_id)
