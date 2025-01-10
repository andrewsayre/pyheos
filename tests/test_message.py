"""Define tests for the message module."""

import re

import pytest

from pyheos import command as c
from pyheos.message import HeosMessage


def test_get_message_value_missing_key_raises() -> None:
    """Test creating a browse result from data."""

    message = HeosMessage(c.COMMAND_BROWSE_BROWSE)

    with pytest.raises(
        KeyError, match=re.escape("Key 'missing_key' not found in message parameters.")
    ):
        message.get_message_value("missing_key")
