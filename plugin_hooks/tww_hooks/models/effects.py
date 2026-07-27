from __future__ import annotations

from dataclasses import dataclass, field
from collections.abc import Mapping
from typing import Any
from enum import StrEnum



@dataclass(slots=True, frozen=True)
class EffectDocument:
    version: int
    source: EffectSource
    effects: tuple[Effect, ...]

@dataclass(slots=True, frozen=True)
class EffectSource:
    model: str
    class_id: str
    object_id: str

@dataclass(slots=True, frozen=True)
class Effect:
    kind: EffectKind

@dataclass(slots=True, frozen=True)
class UpdateAttributeEffect(Effect):
    tww_class_id: str
    tww_identity: Mapping[str, Any]
    tww_attribute_id: str
    value: Any

@dataclass(slots=True, frozen=True)
class EnforceExistsEffect(Effect):
    tww_class_id: str
    tww_identity: Mapping[str, Any]

@dataclass(slots=True, frozen=True)
class EnforceNotExistsEffect(Effect):
    tww_class_id: str
    tww_identity: Mapping[str, Any]

class EffectKind(StrEnum):
    UPDATE_ATTRIBUTE = "update_attribute"
    ENFORCE_EXISTS = "enforce_exists"
    ENFORCE_NOT_EXISTS = "enforce_not_exists"
