"""Define the heos source module."""

from typing import Any, Optional, Sequence

from pyheos.command import HeosCommands  # pylint: disable=unused-import


class InputSource:
    """Define an input source."""

    def __init__(self, player_id: int, name: str, input_name: str) -> None:
        """Init the source."""
        self._player_id = player_id  # type: int
        self._name = name  # type: str
        self._input_name = input_name  # type: str

    def __str__(self) -> str:
        """Get a user-readable representation of the source."""
        return f"<{self._name} ({self._input_name})>"

    def __repr__(self) -> str:
        """Get a debug representation of the source."""
        return f"<{self._name} ({self._input_name}) on {self._player_id}>"

    @property
    def name(self) -> str:
        """Get the friendly display name."""
        return self._name

    @property
    def input_name(self) -> str:
        """Get the input source name."""
        return self._input_name

    @property
    def player_id(self) -> int:
        """Get the player id."""
        return self._player_id


class HeosSource:
    """Define an individual heos source."""

    def __init__(self, commands: HeosCommands, data: dict[str, Any]) -> None:
        """Init the source class."""
        self._commands = commands
        self._name: str = data["name"]
        self._image_url: str = data["image_url"]
        self._type: str = data["type"]
        self._source_id: int | None = (
            int(str(data.get("sid"))) if data.get("sid") else None
        )
        self._available: bool = data.get("available") == "true"
        self._service_username: str | None = data.get("service_username")
        self._container: bool = data.get("container") == "yes"
        self._container_id: str | None = data.get("cid")
        self._media_id: str | None = data.get("mid")
        self._playable: bool = data.get("playable") == "yes"

    def __str__(self) -> str:
        """Get a user-readable representation of the source."""
        return f"<{self._name} ({self._type})>"

    def __repr__(self) -> str:
        """Get a debug representation of the source."""
        return f"<{self._name} ({self._type}) {self._source_id}>"

    async def browse(self) -> "Sequence[HeosSource]":
        """Browse the contents of the current source."""
        if not self._source_id:
            raise ValueError("Source is not browsable.")
        items = await self._commands.browse(self._source_id)
        return [HeosSource(self._commands, item) for item in items]

    @property
    def name(self) -> str:
        """Get the name of the source."""
        return self._name

    @property
    def image_url(self) -> str:
        """Get the image url of the source."""
        return self._image_url

    @property
    def type(self) -> str:
        """Get the type of the source."""
        return self._type

    @property
    def source_id(self) -> int | None:
        """Get the id of the source."""
        return self._source_id

    @property
    def available(self) -> bool:
        """Return True if the source is available."""
        return self._available

    @property
    def service_username(self) -> str | None:
        """Get the service username."""
        return self._service_username

    @property
    def media_id(self) -> str | None:
        """Get the media id."""
        return self._media_id

    @property
    def container(self) -> bool:
        """Return True if the source is a container."""
        return self._container

    @property
    def container_id(self) -> str | None:
        """Get the ID of the container."""
        return self._container_id

    @property
    def playable(self) -> bool:
        """Return True if the source is playable."""
        return self._playable
