"""
Define the system command module.

This module creates HEOS system commands.

Commands not implemented:
    4.1.7 Prettify JSON response
        Helper command to prettify JSON response when user is running CLI controller through telnet.
        This command will not be implemented in the library.
"""

from pyheos import command as c
from pyheos.message import HeosCommand


class SystemCommands:
    """Define functions for creating system commands."""

    @staticmethod
    def register_for_change_events(enable: bool) -> HeosCommand:
        """Register for change events.

        References:
            4.1.1 Register for Change Events"""
        return HeosCommand(
            c.COMMAND_REGISTER_FOR_CHANGE_EVENTS,
            {c.ATTR_ENABLE: c.VALUE_ON if enable else c.VALUE_OFF},
        )

    @staticmethod
    def check_account() -> HeosCommand:
        """Create a check account c.

        References:
            4.1.2 HEOS Account Check"""
        return HeosCommand(c.COMMAND_ACCOUNT_CHECK)

    @staticmethod
    def sign_in(username: str, password: str) -> HeosCommand:
        """Create a sign in c.

        References:
            4.1.3 HEOS Account Sign In"""
        return HeosCommand(
            c.COMMAND_SIGN_IN,
            {c.ATTR_USER_NAME: username, c.ATTR_PASSWORD: password},
        )

    @staticmethod
    def sign_out() -> HeosCommand:
        """Create a sign out c.

        References:
            4.1.4 HEOS Account Sign Out"""
        return HeosCommand(c.COMMAND_SIGN_OUT)

    @staticmethod
    def heart_beat() -> HeosCommand:
        """Create a heart beat c.

        References:
            4.1.5 HEOS System Heart Beat"""
        return HeosCommand(c.COMMAND_HEART_BEAT)

    @staticmethod
    def reboot() -> HeosCommand:
        """Create a reboot c.

        References:
            4.1.6 HEOS Speaker Reboot"""
        return HeosCommand(c.COMMAND_REBOOT)
