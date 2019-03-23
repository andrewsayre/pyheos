"""Define the heos source module."""
from typing import Optional, Sequence  # pylint: disable=unused-import


class InputSource:
    """Define an input source."""

    def __init__(self, player_id: int, name: str, input_name: str):
        """Init the source."""
        self._player_id = player_id  # type: int
        self._name = name  # type: str
        self._input_name = input_name  # type: str

    def __str__(self):
        """Get a user-readable representation of the source."""
        return "<{} ({})>".format(self._name, self._input_name)

    def __repr__(self):
        """Get a debug representation of the source."""
        return "<{} ({}) on {}>".format(self._name, self._input_name,
                                        self._player_id)

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

    def __init__(self, commands, data: Optional[dict] = None):
        """Init the source class."""
        self._commands = commands
        self._name = None  # type: str
        self._image_url = None  # type: str
        self._type = None  # type: str
        self._source_id = None  # type: int
        self._available = None  # type: bool
        self._service_username = None  # type: str
        self._container = None  # type: bool
        self._media_id = None  # type: str
        self._playable = None  # type: bool
        if data:
            self._from_data(data)

    def _from_data(self, data: dict):
        self._name = data['name']
        self._image_url = data['image_url']
        self._type = data['type']

        source_id = data.get('sid')
        if source_id:
            self._source_id = int(source_id)

        self._available = data.get('available') == 'true'
        self._service_username = data.get('service_username')
        self._container = data.get('container') == 'yes'
        self._media_id = data.get('mid')
        self._playable = data.get('playable') == 'yes'

    def __str__(self):
        """Get a user-readable representation of the source."""
        return "<{} ({})>".format(self._name, self._type)

    def __repr__(self):
        """Get a debug representation of the source."""
        return "<{} ({}) {}>".format(self._name, self._type, self._source_id)

    async def browse(self) -> 'Sequence[HeosSource]':
        """Browse the contents of the current source."""
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
    def source_id(self) -> int:
        """Get the id of the source."""
        return self._source_id

    @property
    def available(self) -> bool:
        """Return True if the source is available."""
        return self._available

    @property
    def service_username(self) -> str:
        """Get the service username."""
        return self._service_username

    @property
    def media_id(self) -> str:
        """Get the media id."""
        return self._media_id

    @property
    def container(self) -> bool:
        """Return True if the source is a container."""
        return self._container

    @property
    def playable(self) -> bool:
        """Return True if the source is playable."""
        return self._playable
