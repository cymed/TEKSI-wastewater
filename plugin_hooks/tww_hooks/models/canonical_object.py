from __future__ import annotations

from dataclasses import dataclass, field
from collections.abc import Mapping
from typing import Any


@dataclass(slots=True, frozen=True)
class CanonicalObjectIdentity:
    """
    Canonical identity of a TWW object.
    """

    class_id: str = field(
        metadata={
            "doc": (
                "Canonical class identifier."
            )
        },
    )

    attributes: Mapping[str, Any] = field(
        metadata={
            "doc": (
                "Attributes uniquely identifying the object."
            )
        },
    )

@dataclass(slots=True, frozen=True)
class CanonicalObject:
    """
    Canonical TWW object.
    """

    identity: CanonicalObjectIdentity = field(
        metadata={
            "doc": (
                "Canonical object identity."
            )
        },
    )

    values: Mapping[str, Any] = field(
        default_factory=dict,
        metadata={
            "doc": (
                "Canonical attribute values."
            )
        },
    )