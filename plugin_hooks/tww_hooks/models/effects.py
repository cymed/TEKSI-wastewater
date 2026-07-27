from __future__ import annotations

from dataclasses import dataclass, field
from collections.abc import Mapping
from typing import Any
from enum import StrEnum



class EffectKind(StrEnum):
    UPDATE_ATTRIBUTE = "update_attribute"
    ENFORCE_EXISTS = "enforce_exists"
    ENFORCE_NOT_EXISTS = "enforce_not_exists"
    
@dataclass(slots=True, frozen=True)
class EffectDocument:

    version: int = field(
        metadata={
            "doc": (
                "Version of the effect-document contract."
            )
        },
    )

    source: EffectSource = field(
        metadata={
            "doc": (
                "Source object from which the effects were generated."
            )
        },
    )

    effects: tuple[Effect, ...] = field(
        metadata={
            "doc": (
                "Semantic effects generated from the source object."
            )
        },
    )

@dataclass(slots=True, frozen=True)
class EffectSource:

    model: str = field(
        metadata={
            "doc": (
                "Source model identifier."
            )
        },
    )

    class_id: str = field(
        metadata={
            "doc": (
                "Source class identifier."
            )
        },
    )

    object_id: str = field(
        metadata={
            "doc": (
                "Source object identifier."
            )
        },
    )


@dataclass(slots=True, frozen=True)
class Effect:
    """
    Base effect model.
    """

@dataclass(slots=True, frozen=True)
class UpdateAttributeEffect(Effect):

    kind: EffectKind = field(
        default=EffectKind.UPDATE_ATTRIBUTE,
        init=False,
        metadata={
            "doc": (
                "Effect kind discriminator."
            )
        },
    )

    tww_class_id: str = field(
        metadata={
            "doc": (
                "Canonical TWW class identifier being modified."
            )
        },
    )

    tww_identity: Mapping[str, Any] = field(
        metadata={
            "doc": (
                "Canonical identity attributes used to locate the target "
                "object."
            )
        },
    )

    tww_attribute_id: str = field(
        metadata={
            "doc": (
                "Canonical attribute identifier being updated."
            )
        },
    )

    value: Any = field(
        metadata={
            "doc": (
                "New value that should be assigned to the target attribute."
            )
        },
    )

@dataclass(slots=True, frozen=True)
class EnforceExistsEffect(Effect):

    kind: EffectKind = field(
        default=EffectKind.ENFORCE_EXISTS,
        init=False,
        metadata={
            "doc": (
                "Effect kind discriminator."
            )
        },
    )

    tww_class_id: str = field(
        metadata={
            "doc": (
                "Canonical TWW class identifier that must exist."
            )
        },
    )

    tww_identity: Mapping[str, Any] = field(
        metadata={
            "doc": (
                "Canonical identity attributes identifying the required "
                "object."
            )
        },
    )

@dataclass(slots=True, frozen=True)
class EnforceNotExistsEffect(Effect):

    kind: EffectKind = field(
        default=EffectKind.ENFORCE_NOT_EXISTS,
        init=False,
        metadata={
            "doc": (
                "Effect kind discriminator."
            )
        },
    )

    tww_class_id: str = field(
        metadata={
            "doc": (
                "Canonical TWW class identifier that must not exist."
            )
        },
    )

    tww_identity: Mapping[str, Any] = field(
        metadata={
            "doc": (
                "Canonical identity attributes identifying the prohibited "
                "object."
            )
        },
    )

