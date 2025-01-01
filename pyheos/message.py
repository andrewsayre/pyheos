"""Define the message module for signals received from HEOS."""

import json
import logging
from dataclasses import dataclass, field
from functools import cached_property
from typing import Any, cast
from urllib.parse import parse_qsl

from pyheos import const

_LOGGER = logging.getLogger(__name__)


@dataclass(frozen=True)
class HeosCommand:
    """Define a HEOS command that is sent to the HEOS device."""

    command: str
    parameters: dict[str, Any] = field(default_factory=dict)

    @property
    def uri(self) -> str:
        """Get the command as a URI string that can be sent to the controller."""
        return self._get_uri(False)

    @property
    def uri_masked(self) -> str:
        """Get the command as a URI string that has sensitive fields masked."""
        return self._get_uri(True)

    def _get_uri(self, mask: bool = False) -> str:
        """Get the command as a URI string."""
        query_string = (
            f"?{HeosCommand._encode_query(self.parameters, mask=mask)}"
            if self.parameters
            else ""
        )
        return f"{const.BASE_URI}{self.command}{query_string}"

    @classmethod
    def _quote(cls, value: Any) -> str:
        """Quote a string per the CLI specification."""
        return "".join([const.QUOTE_MAP.get(char, char) for char in str(value)])

    @classmethod
    def _encode_query(cls, items: dict[str, Any], *, mask: bool = False) -> str:
        """Encode a dict to query string per CLI specifications."""
        pairs = []
        for key in sorted(items.keys()):
            value = const.MASK if mask and key in const.MASKED_PARAMS else items[key]
            item = f"{key}={HeosCommand._quote(value)}"
            # Ensure 'url' goes last per CLI spec
            if key == const.ATTR_URL:
                pairs.append(item)
            else:
                pairs.insert(0, item)
        return "&".join(pairs)


@dataclass(frozen=True)
class HeosMessage:
    """Lower a message received from a HEOS device. This is a lower level class used internally."""

    raw_message: str

    @cached_property
    def container(self) -> dict[str, Any]:
        """Get the entire message as a dictionary."""
        return cast(dict[str, Any], json.loads(self.raw_message))

    @cached_property
    def heos(self) -> dict[str, Any]:
        """Get the HEOS section as a dictionary."""
        return cast(dict[str, Any], self.container[const.ATTR_HEOS])

    @cached_property
    def payload(self) -> dict[str, Any] | list[Any] | None:
        """Get the payload section as a dictionary."""
        return self.container.get("payload")

    @cached_property
    def command(self) -> str:
        """Get the command the message is referring to."""
        return str(self.heos["command"])

    @cached_property
    def message(self) -> dict[str, str]:
        """Get the message parameters as a dictionary. If not present in the message, an empty dictionary is returned."""
        if raw_message := self.heos.get(const.ATTR_MESSAGE):
            return dict(parse_qsl(raw_message, keep_blank_values=True))
        return {}

    @cached_property
    def is_under_process(self) -> bool:
        """Return True if the message represents a command under process, otherwise False."""
        return "command under process" in self.message

    @cached_property
    def is_event(self) -> bool:
        """Return True if the message is an event, otherwise False."""
        return self.command.startswith("event/")

    @cached_property
    def result(self) -> bool:
        """Return True if the message represents a successful command. If not present in the response, True is returned."""
        return bool(
            self.heos.get(const.ATTR_RESULT, const.VALUE_SUCCESS) == const.VALUE_SUCCESS
        )

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
