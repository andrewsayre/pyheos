"""
Define the system command module.

This module creates HEOS system commands.

Commands not implemented:
    4.1.7 Prettify JSON response
        Helper command to prettify JSON response when user is running CLI controller through telnet.
        This command will not be implemented in the library.
"""

from pyheos import command, const
from pyheos.message import HeosCommand


class SystemCommands:
    """Define functions for creating system commands."""

    @staticmethod
    def register_for_change_events(enable: bool) -> HeosCommand:
        """Register for change events.

        References:
            4.1.1 Register for Change Events"""
        return HeosCommand(
            command.COMMAND_REGISTER_FOR_CHANGE_EVENTS,
            {const.ATTR_ENABLE: const.VALUE_ON if enable else const.VALUE_OFF},
        )

    @staticmethod
    def check_account() -> HeosCommand:
        """Create a check account command.

        References:
            4.1.2 HEOS Account Check"""
        return HeosCommand(command.COMMAND_ACCOUNT_CHECK)

    @staticmethod
    def sign_in(username: str, password: str) -> HeosCommand:
        """Create a sign in command.

        References:
            4.1.3 HEOS Account Sign In"""
        return HeosCommand(
            command.COMMAND_SIGN_IN,
            {const.ATTR_USER_NAME: username, const.ATTR_PASSWORD: password},
        )

    @staticmethod
    def sign_out() -> HeosCommand:
        """Create a sign out command.

        References:
            4.1.4 HEOS Account Sign Out"""
        return HeosCommand(command.COMMAND_SIGN_OUT)

    @staticmethod
    def heart_beat() -> HeosCommand:
        """Create a heart beat command.

        References:
            4.1.5 HEOS System Heart Beat"""
        return HeosCommand(command.COMMAND_HEART_BEAT)

    @staticmethod
    def reboot() -> HeosCommand:
        """Create a reboot command.

        References:
            4.1.6 HEOS Speaker Reboot"""
        return HeosCommand(command.COMMAND_REBOOT)
