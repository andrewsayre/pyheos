"""Define the error module for HEOS."""

from pyheos.command import ATTR_ERROR_ID, ATTR_SYSTEM_ERROR_NUMBER, ATTR_TEXT
from pyheos.const import (
    ERROR_INVALID_CREDNETIALS,
    ERROR_SYSTEM_ERROR,
    ERROR_USER_NOT_FOUND,
    ERROR_USER_NOT_LOGGED_IN,
    SYSTEM_ERROR_USER_NOT_FOUND,
    SYSTEM_ERROR_USER_NOT_LOGGED_IN,
)
from pyheos.message import HeosMessage


class HeosError(Exception):
    """Define an error from the HEOS library."""

    pass


class CommandError(HeosError):
    """Define an error for when a HEOS command send fails."""

    def __init__(self, command: str, message: str):
        """Create a new instance of the error."""
        self._command = command
        super().__init__(message)

    @property
    def command(self) -> str:
        """Get the command that raised the error."""
        return self._command


class CommandFailedError(CommandError):
    """Define an error for when a HEOS command is sent, but a failure response is returned."""

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

    @staticmethod
    def __is_authentication_error(
        error_id: int, system_error_number: int | None
    ) -> bool:
        """Return True if the error is related to authentication, otherwise False."""
        if error_id == ERROR_SYSTEM_ERROR:
            return system_error_number in (
                SYSTEM_ERROR_USER_NOT_LOGGED_IN,
                SYSTEM_ERROR_USER_NOT_FOUND,
            )
        return error_id in (
            ERROR_INVALID_CREDNETIALS,
            ERROR_USER_NOT_LOGGED_IN,
            ERROR_USER_NOT_FOUND,
        )

    @classmethod
    def _from_message(cls, message: HeosMessage) -> "CommandFailedError":
        """Create a new instance of the error from a message."""
        error_text = message.get_message_value(ATTR_TEXT)
        system_error_number = None
        error_id = message.get_message_value_int(ATTR_ERROR_ID)
        if error_id == ERROR_SYSTEM_ERROR:
            system_error_number = message.get_message_value_int(
                ATTR_SYSTEM_ERROR_NUMBER
            )
            error_text += f" {system_error_number}"

        if CommandFailedError.__is_authentication_error(error_id, system_error_number):
            return CommandAuthenticationError(
                message.command, error_text, error_id, system_error_number
            )

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


class CommandAuthenticationError(CommandFailedError):
    """Define an error for when a command succeeds, but an authentication error is returned."""

    pass
