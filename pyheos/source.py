"""Define the heos source module."""
from typing import Optional


class HeosSource:
    """Define an individual heos source."""

    def __init__(self, commands, data: Optional[dict] = None):
        """Init the source class."""
        self._commands = commands
        self._name = None  # type: str
        self._image_url = None  # type: str
        self._type = None  # type: str
        self._source_id = None  # type: int
        self._available = None  # type: bool
        self._service_username = None  # type: str
        if data:
            self._from_data(data)

    def _from_data(self, data: dict):
        self._name = data['name']
        self._image_url = data['image_url']
        self._type = data['type']

        source_id = data.get('sid')
        if source_id:
            self._source_id = int(source_id)

        self._available = data.get('available')
        self._service_username = data.get('service_username')

    def __str__(self):
        """Get a user-readable representation of the source."""
        return "<{} ({})>".format(self._name, self._type)

    def __repr__(self):
        """Get a debug representation of the source."""
        return "<{} ({}) {}>".format(self._name, self._type, self._source_id)

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
    def source_id(self) -> int:
        """Get the id of the source."""
        return self._source_id

    @property
    def available(self) -> bool:
        """Return True if the source is available."""
        return self._available

    @property
    def service_username(self):
        """Get the service username."""
        return self._service_username
