# models/dict_mapping.py

from dataclasses import dataclass, field
from collections.abc import Mapping

from .canonical_object import CanonicalIdentityMapping

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
class FunctionMapping:
    """
    Describes a database-backed mapping function.

    Function mappings are used when a source attribute cannot be mapped to a
    canonical TWW class and attribute by simple structural metadata alone.

    Typical examples are AGXX attributes whose meaning depends on several
    source attributes or on existing database state. Instead of duplicating
    this logic in YAML or Python, the mapping references a database function
    that implements the authoritative transformation.

    The function is expected to return a well-defined result that can be
    consumed by the change loader, validation logic or rights evaluator.
    """

    schema: str = field(
        metadata={
            "doc": (
                "Database schema containing the mapping function. "
                "Example: `tww_app`."
            )
        },
    )

    name: str = field(
        metadata={
            "doc": (
                "Database function name implementing the mapping logic. "
                "Example: `fct_agxx_gepknoten_funktionag_mapping`."
            )
        },
    )

    parameters: Mapping[str, str] = field(
        default_factory=dict,
        metadata={
            "doc": (
                "Function parameter mapping. Keys are database function "
                "parameter names. Values are source-model attribute names "
                "whose values should be passed to the corresponding "
                "parameter. Example: `{'funktionag': 'funktionag', "
                "'ignore_ws': 'ignore_ws'}`."
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
    identity: CanonicalIdentityMapping = field(
        default_factory=lambda: CanonicalIdentityMapping(
            source_attribute="t_ili_tid",
            canonical_attribute="obj_id",
        ),
    )
        
    attributes: Mapping[str, AttributeMapping] = field(
        default_factory=dict,
        metadata={
            "doc": (
                "Attribute mappings keyed by source runtime attribute identifier. "
                "For ili2pg imports this is the actual SQLAlchemy/ili2pg column "
                "name, which may differ from the original INTERLIS attribute name "
                "when ili2pg had to avoid reserved words."
            )
        },
    )
    )
    function: FunctionMapping | None = field(
        default=None,
        metadata={
            "doc": (
                "Optional database-backed mapping function. Used when the "
                "source attribute cannot be mapped by a simple class/attribute "
                "target. If present, the function is responsible for deriving "
                "the canonical mapping result from the configured source "
                "parameters. Typical examples include AGXX structural subtype "
                "logic such as `GepKnoten.funktionag` or "
                "`Ueberlauf_Foerderaggregat.art`."
            )
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

