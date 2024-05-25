"""Define the error module for HEOS."""

import asyncio

DEFAULT_ERROR_MESSAGES = {
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
    error_message = str(error)
    if not error_message:
        error_message = DEFAULT_ERROR_MESSAGES.get(type(error))
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

    def __init__(self, command: str, text: str, error_id: int):
        """Create a new instance of the error."""
        self._command = command
        self._error_text = text
        self._error_id = error_id
        super().__init__(command, f"{text} ({error_id})")

    @property
    def error_text(self) -> str:
        """Get the error text from the response."""
        return self._error_text

    @property
    def error_id(self) -> int:
        """Return the error id."""
        return self._error_id
