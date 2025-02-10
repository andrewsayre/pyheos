"""Define the common module."""

from typing import cast

from pyheos.const import TARGET_VERSION


def is_supported_version(
    version: str | None, min_version: str = TARGET_VERSION
) -> bool:
    """Check if a version is supported.

    Args:
        version (str): The version to check.
        min_version (str): The minimum version.

    Returns:
        bool: True if the version is supported, False otherwise.
    """
    if version is None:
        return False
    try:
        sem_ver = get_sem_ver(version)
    except ValueError:
        return False
    min_sem_ver = get_sem_ver(min_version)
    for i, ver in enumerate(sem_ver):
        if ver < min_sem_ver[i]:
            return False
        if ver > min_sem_ver[i]:
            return True
    return True


def get_sem_ver(version: str) -> tuple[int, int, int]:
    """Get the semantic version from a string.

    Args:
        version (str): The version string.

    Returns:
        tuple: The semantic version as a tuple.
    """
    return cast(tuple[int, int, int], tuple(map(int, version.split(".", 3))))
