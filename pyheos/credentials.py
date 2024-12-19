"""Define the credentials module."""

from dataclasses import dataclass


@dataclass(frozen=True)
class Credentials:
    """Define an object to hold a HEOS account credentials."""

    username: str
    password: str
