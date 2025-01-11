"""
Define the system command module.

This module creates HEOS system commands.

Commands not implemented:
    4.1.7 Prettify JSON response
        Helper command to prettify JSON response when user is running CLI controller through telnet.
        This command will not be implemented in the library.
"""

from collections.abc import Sequence
from typing import Any, cast

from pyheos import command as c
from pyheos.command.connection import ConnectionMixin
from pyheos.credentials import Credentials
from pyheos.message import HeosCommand
from pyheos.system import HeosHost, HeosSystem


class SystemCommands(ConnectionMixin):
    """A mixin to provide access to the system commands."""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        """Init a new instance of the BrowseMixin."""
        super(SystemCommands, self).__init__(*args, **kwargs)

        self._current_credentials = self._options.credentials
        self._signed_in_username: str | None = None

    @property
    def is_signed_in(self) -> bool:
        """Return True if the HEOS accuont is signed in."""
        return bool(self._signed_in_username)

    @property
    def signed_in_username(self) -> str | None:
        """Return the signed-in username."""
        return self._signed_in_username

    @property
    def current_credentials(self) -> Credentials | None:
        """Return the current credential, if any set."""
        return self._current_credentials

    @current_credentials.setter
    def current_credentials(self, credentials: Credentials | None) -> None:
        """Update the current credential."""
        self._current_credentials = credentials

    async def register_for_change_events(self, enable: bool) -> None:
        """Register for change events.

        References:
            4.1.1 Register for Change Events"""
        await self._connection.command(
            HeosCommand(
                c.COMMAND_REGISTER_FOR_CHANGE_EVENTS,
                {c.ATTR_ENABLE: c.VALUE_ON if enable else c.VALUE_OFF},
            )
        )

    async def check_account(self) -> str | None:
        """Return the logged in username.

        References:
            4.1.2 HEOS Account Check"""
        result = await self._connection.command(HeosCommand(c.COMMAND_ACCOUNT_CHECK))
        if c.ATTR_SIGNED_IN in result.message:
            self._signed_in_username = result.get_message_value(c.ATTR_USER_NAME)
        else:
            self._signed_in_username = None
        return self._signed_in_username

    async def sign_in(
        self, username: str, password: str, *, update_credential: bool = True
    ) -> str:
        """Sign in to the HEOS account using the provided credential and return the user name.

        Args:
            username: The username of the HEOS account.
            password: The password of the HEOS account.
            update_credential: Set to True to update the stored credential if login is successful, False to keep the current credential. The default is True. If the credential is updated, it will be used to signed in automatically upon reconnection.

        Returns:
            The username of the signed in account.

        References:
            4.1.3 HEOS Account Sign In"""
        result = await self._connection.command(
            HeosCommand(
                c.COMMAND_SIGN_IN,
                {c.ATTR_USER_NAME: username, c.ATTR_PASSWORD: password},
            )
        )
        self._signed_in_username = result.get_message_value(c.ATTR_USER_NAME)
        if update_credential:
            self.current_credentials = Credentials(username, password)
        return self._signed_in_username

    async def sign_out(self, *, update_credential: bool = True) -> None:
        """Sign out of the HEOS account.

        Args:
            update_credential: Set to True to clear the stored credential, False to keep it. The default is True. If the credential is cleared, the account will not be signed in automatically upon reconnection.

        References:
            4.1.4 HEOS Account Sign Out"""
        await self._connection.command(HeosCommand(c.COMMAND_SIGN_OUT))
        self._signed_in_username = None
        if update_credential:
            self.current_credentials = None

    async def heart_beat(self) -> None:
        """Send a heart beat message to the HEOS device.

        References:
            4.1.5 HEOS System Heart Beat"""
        await self._connection.command(HeosCommand(c.COMMAND_HEART_BEAT))

    async def reboot(self) -> None:
        """Reboot the HEOS device.

        References:
            4.1.6 HEOS Speaker Reboot"""
        await self._connection.command(HeosCommand(c.COMMAND_REBOOT))

    async def get_system_info(self) -> HeosSystem:
        """Get information about the HEOS system.

        References:
            4.2.1 Get Players"""
        response = await self._connection.command(HeosCommand(c.COMMAND_GET_PLAYERS))
        payload = cast(Sequence[dict], response.payload)
        hosts = list([HeosHost._from_data(item) for item in payload])
        host = next(host for host in hosts if host.ip_address == self._options.host)
        return HeosSystem(self._signed_in_username, host, hosts)
