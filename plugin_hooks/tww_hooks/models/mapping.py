# models/dict_mapping.py

from dataclasses import dataclass, field
from collections.abc import Mapping


@dataclass(slots=True, frozen=True)
class ValueMapping:
    """
    Maps a source-model value list entry to the canonical internal model.
    """
    tww_val_id: int = field(
        metadata={
            "doc": (
                "Canonical value identifier. Corresponds to "
                "a value-list code or database value id."
            )
        }
    )

    value: str =field(
        metadata={
            "doc": (
                "Source-model value that maps to the canonical TWW value_en "
                "or value_en of the canonical TWW code (if ModelMapping is_ssot) "
            )
        }
    )

    vl_extension: bool = field(
        default=False,
        metadata={
            "doc": (
                "Whether this value originates from a value-list extension "
                "rather than the base VSA/SIA405 model."
            )
        },
    )


@dataclass(slots=True, frozen=True)
class ForeignKeyMapping:
    """
    Describes the canonical object referenced by a mapped attribute.

    This is used when the mapped canonical attribute stores a reference
    rather than a literal value.
    """

    referenced_class_id: str = field(
        metadata={
            "doc": (
                "Canonical class identifier this source class maps to. "
                "Corresponds to a table/class in the internal TWW "
                "semantic model."
            )
        },
    )
    referenced_attribute_id: str  = field(
        default='obj_id',
        metadata={
            "doc": (
                "Canonical attribute identifier this source class maps to. "
                "Corresponds to an attribute in the internal TWW "
                "semantic model."
            )
        },
    )


@dataclass(slots=True, frozen=True)
class AttributeMapping:
    """
    Maps a source-model attribute to the canonical internal model.
    """
    tww_class_id: str | None = field(
        default=None,
        metadata={
            "doc": (
                "Canonical class identifier this source class maps to. "
                "Corresponds to a table/class in the internal TWW "
                "semantic model."
            )
        },
    )
    tww_attr_id: str | None  = field(
        default=None,
        metadata={
            "doc": (
                "Canonical attribute identifier this source class maps to. "
                "Corresponds to an attribute in the internal TWW "
                "semantic model."
            )
        },
    )
    foreign_key: ForeignKeyMapping | None = field(
        default=None,
        metadata={
            "doc": (
                "Optional reference metadata if the canonical attribute is a "
                "foreign key. Points to the referenced canonical class and key "
                "attribute, not to another AttributeMapping."
            )
        },
    )

    values: Mapping[str, ValueMapping] = field(
        default_factory=dict,
        metadata={
            "doc": "Optional value mappings keyed by source-model value."
        },
    )

@dataclass(slots=True, frozen=True)
class ClassMapping:
    """
    Maps a source-model class to the canonical internal model.
    """
    tww_class_id: str | None = field(
        default=None,
        metadata={
            "doc": (
                "Canonical class identifier this source class maps to. "
                "Corresponds to a table/class in the internal TWW "
                "semantic model."
            )
        },
    )
    tww_identity_attr: str = field(
        default="obj_id",
        metadata={
            "doc": (
                "Canonical TWW attribute used to identify and match objects "
                "of this class across models or schemas. Usually corresponds "
                "to `obj_id`, but should be understood as semantic object "
                "identity rather than necessarily the physical database "
                "primary key."
            )
        },
    )
    attributes: Mapping[str, AttributeMapping] = field(
        default_factory=dict,
        metadata={
            "doc": "Attribute mappings keyed by source-model attribute identifier.."
        },
    )


@dataclass(slots=True, frozen=True)
class ModelMapping:
    """
    Describes how one source model maps to the canonical internal model.
    """
    classes: Mapping[str, ClassMapping]= field(
        default_factory=dict,
        metadata={
            "doc": "Class mappings keyed by source-model value."
        },
    )
    is_ssot: bool = field(
        default=False,
        metadata={
           "doc": (
                "Whether this model mapping describes the canonical source "
                "of truth model."
            )

        },
    )

@dataclass(frozen=True)
class RelationContext:
    """
    Runtime context used for a mapped relation.

    This object links a concrete SQLAlchemy ORM relation with the semantic
    class mapping used by the diff and validation pipeline.
    """

    relation: type = field(
        metadata={
            "doc": (
                "ORM relation generated from sqlalchemy."
            )
        },
    )
    class_mapping: ClassMapping = field(
        metadata={
            "doc": (
                "Class mappings keyed by source-model class identifier."
            )
        },
    )


