from __future__ import annotations

from dataclasses import dataclass, field
from collections.abc import Mapping
from datetime import datetime
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

    last_modification: datetime | None = field(
        default=None,
        metadata={
            "doc": (
                "Current last_modification value."
            )
        },
    )