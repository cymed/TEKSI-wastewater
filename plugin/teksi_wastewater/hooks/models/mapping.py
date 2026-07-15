# models/dict_mapping.py

from dataclasses import dataclass, field
from collections.abc import Mapping


@dataclass(slots=True, frozen=True)
class ValueMapping:
    tww_od_val_id: int
    value: str
    vl_extension: bool = False


@dataclass(slots=True, frozen=True)
class AttributeMapping:
    tww_od_class_id: str | None = None
    tww_od_attr_id: str | None = None
    foreign_key: str | None = None
    values: Mapping[str, ValueMapping] = field(
        default_factory=dict,
    )

@dataclass(slots=True, frozen=True)
class ClassMapping:
    tww_od_class_id: str | None = None
    attributes: Mapping[str, AttributeMapping]


@dataclass(slots=True, frozen=True)
class ModelMapping:
    classes: Mapping[str, ClassMapping]


@dataclass(frozen=True)
class RelationContext:
    relation: type
    class_mapping: ClassMapping
    pk_attribute: str


