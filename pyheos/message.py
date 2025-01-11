"""Define the message module for signals received from HEOS."""

import json
from dataclasses import dataclass, field
from functools import cached_property
from typing import Any, Final
from urllib.parse import parse_qsl

from pyheos import command as c

BASE_URI: Final = "heos://"
QUOTE_MAP: Final = {"&": "%26", "=": "%3D", "%": "%25"}
MASKED_PARAMS: Final = {c.ATTR_PASSWORD}
MASK: Final = "********"


@dataclass(frozen=True)
class HeosCommand:
    """Define a HEOS command that is sent to the HEOS device."""

    command: str
    parameters: dict[str, Any] = field(default_factory=dict)

    def __repr__(self) -> str:
        """Get a string representaton of the message."""
        return self.uri_masked

    @cached_property
    def uri(self) -> str:
        """Get the command as a URI string that can be sent to the controller."""
        return self._get_uri(False)

    @cached_property
    def uri_masked(self) -> str:
        """Get the command as a URI string that has sensitive fields masked."""
        return self._get_uri(True)

    def _get_uri(self, mask: bool = False) -> str:
        """Get the command as a URI string."""
        query_string = (
            f"?{HeosCommand.__encode_query(self.parameters, mask=mask)}"
            if self.parameters
            else ""
        )
        return f"{BASE_URI}{self.command}{query_string}"

    @staticmethod
    def __quote(value: Any) -> str:
        """Quote a string per the CLI specification."""
        return "".join([QUOTE_MAP.get(char, char) for char in str(value)])

    @staticmethod
    def __encode_query(items: dict[str, Any], *, mask: bool = False) -> str:
        """Encode a dict to query string per CLI specifications."""
        pairs = []
        for key in sorted(items.keys()):
            value = MASK if mask and key in MASKED_PARAMS else items[key]
            item = f"{key}={HeosCommand.__quote(value)}"
            # Ensure 'url' goes last per CLI spec and is not quoted
            if key == c.ATTR_URL:
                pairs.append(f"{key}={value}")
            else:
                pairs.insert(0, item)
        return "&".join(pairs)


@dataclass(repr=False)
class HeosMessage:
    """Lower a message received from a HEOS device. This is a lower level class used internally."""

    command: str
    result: bool = True
    message: dict[str, str] = field(default_factory=dict)
    payload: dict[str, Any] | list[Any] | None = None
    options: list[dict[str, list[dict[str, Any]]]] | None = None

    _raw_message: str | None = field(
        init=False, hash=False, repr=False, compare=False, default=None
    )

    def __repr__(self) -> str:
        """Get a string representaton of the message."""
        return self._raw_message or f"{self.command} {self.message}"

    @staticmethod
    def _from_raw_message(raw_message: str) -> "HeosMessage":
        """Create a HeosMessage from a raw message."""
        container = json.loads(raw_message)
        heos = container[c.ATTR_HEOS]
        instance = HeosMessage(
            command=str(heos[c.ATTR_COMMAND]),
            result=bool(heos.get(c.ATTR_RESULT, c.VALUE_SUCCESS) == c.VALUE_SUCCESS),
            message=dict(
                parse_qsl(heos.get(c.ATTR_MESSAGE, ""), keep_blank_values=True)
            ),
            payload=container.get(c.ATTR_PAYLOAD),
            options=container.get(c.ATTR_OPTIONS),
        )
        instance._raw_message = raw_message
        return instance

    @cached_property
    def is_under_process(self) -> bool:
        """Return True if the message represents a command under process, otherwise False."""
        return "command under process" in self.message

    @cached_property
    def is_event(self) -> bool:
        """Return True if the message is an event, otherwise False."""
        return self.command.startswith("event/")

    def get_message_value(self, key: str) -> str:
        """Get a message parameter as a string."""
        assert self.message is not None
        if key not in self.message:
            raise KeyError(f"Key '{key}' not found in message parameters.")
        return self.message[key]

    def get_message_value_float(self, key: str) -> float:
        """Get a message parameter as a float."""
        return float(self.get_message_value(key))

    def get_message_value_int(self, key: str) -> int:
        """Get a message parameter as an integer.

        Convert to float first because it may contain a decimal point.
        """
        return int(self.get_message_value_float(key))
