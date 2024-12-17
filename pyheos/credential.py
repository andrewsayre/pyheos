"""Define the credential module."""

from dataclasses import dataclass


@dataclass(frozen=True)
class Credential:
    """Define an object to hold a HEOS account credential."""

    username: str
    password: str
