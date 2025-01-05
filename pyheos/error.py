"""Define the error module for HEOS."""

import asyncio
from functools import cached_property
from typing import Final

from pyheos import const
from pyheos.message import HeosMessage

DEFAULT_ERROR_MESSAGES: Final[dict[type[Exception], str]] = {
    asyncio.TimeoutError: "Command timed out",
    ConnectionError: "Connection error",
    BrokenPipeError: "Broken pipe",
    ConnectionAbortedError: "Connection aborted",
    ConnectionRefusedError: "Connection refused",
    ConnectionResetError: "Connection reset",
    OSError: "OS I/O error",
}


def format_error_message(error: Exception) -> str:
    """Format the error message based on a base error."""
    error_message: str = str(error)
    if not error_message:
        error_message = DEFAULT_ERROR_MESSAGES.get(type(error), type(error).__name__)
    return error_message


class HeosError(Exception):
    """Define an error from the heos library."""

    pass


class CommandError(HeosError):
    """Define an error command response."""

    def __init__(self, command: str, message: str):
        """Create a new instance of the error."""
        self._command = command
        super().__init__(message)

    @property
    def command(self) -> str:
        """Get the command that raised the error."""
        return self._command


class CommandFailedError(CommandError):
    """Define an error when a HEOS command fails."""

    def __init__(
        self,
        command: str,
        text: str,
        error_id: int,
        system_error_number: int | None = None,
    ):
        """Create a new instance of the error."""
        self._command = command
        self._error_text = text
        self._error_id = error_id
        self._system_error_number = system_error_number
        super().__init__(command, f"{text} ({error_id})")

    @classmethod
    def from_message(cls, message: HeosMessage) -> "CommandFailedError":
        """Create a new instance of the error from a message."""
        error_text = message.get_message_value(const.ATTR_TEXT)
        system_error_number = None
        error_id = message.get_message_value_int(const.ATTR_ERROR_ID)
        if error_id == const.ERROR_SYSTEM_ERROR:
            system_error_number = message.get_message_value_int(
                const.ATTR_SYSTEM_ERROR_NUMBER
            )
            error_text += f" {system_error_number}"

        return CommandFailedError(
            message.command, error_text, error_id, system_error_number
        )

    @property
    def error_text(self) -> str:
        """Get the error text from the response."""
        return self._error_text

    @property
    def error_id(self) -> int:
        """Return the error id."""
        return self._error_id

    @property
    def system_error_number(self) -> int | None:
        """Return the system error number if available."""
        return self._system_error_number

    @cached_property
    def is_credential_error(self) -> bool:
        """Return True if the error is related to authentication, otherwise False."""
        if self.error_id == const.ERROR_SYSTEM_ERROR:
            return self.system_error_number in (
                const.SYSTEM_ERROR_USER_NOT_LOGGED_IN,
                const.SYSTEM_ERROR_USER_NOT_FOUND,
            )
        return self._error_id in (
            const.ERROR_INVALID_CREDNETIALS,
            const.ERROR_USER_NOT_LOGGED_IN,
            const.ERROR_USER_NOT_FOUND,
        )
