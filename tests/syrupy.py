"""Define the pyheos test sryupy plugin."""

import dataclasses
from pathlib import Path
from typing import Any

from syrupy.extensions.amber import AmberDataSerializer, AmberSnapshotExtension
from syrupy.location import PyTestLocation
from syrupy.types import PropertyFilter, PropertyMatcher, PropertyPath, SerializableData


class HeosSnapshotSerializer(AmberDataSerializer):
    """Heos snapshot serializer for Syrupy."""

    @classmethod
    def _serialize(
        cls,
        data: SerializableData,
        *,
        depth: int = 0,
        exclude: PropertyFilter | None = None,
        include: PropertyFilter | None = None,
        matcher: PropertyMatcher | None = None,
        path: PropertyPath = (),
        visited: set[Any] | None = None,
    ) -> str:
        """Pre-process data before serializing."""
        if dataclasses.is_dataclass(type(data)):
            data = dataclasses.asdict(data)

        return super()._serialize(
            data,
            depth=depth,
            exclude=exclude,
            include=include,
            matcher=matcher,
            path=path,
            visited=visited,
        )


class HeosSnapshotExtension(AmberSnapshotExtension):
    """Heos extension for Syrupy."""

    VERSION = "1"

    serializer_class: type[AmberDataSerializer] = HeosSnapshotSerializer

    @classmethod
    def dirname(cls, *, test_location: PyTestLocation) -> str:
        """Return the directory for the snapshot files."""
        test_dir = Path(test_location.filepath).parent
        return str(test_dir.joinpath("snapshots"))
