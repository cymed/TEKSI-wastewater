from __future__ import annotations

from dataclasses import dataclass, field
from collections.abc import Mapping
from datetime import datetime
from enum import StrEnum
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

@dataclass(slots=True, frozen=True)
class CanonicalIdentityMapping:
    """
    Mapping from source object identity to canonical object identity.
    """

    source_attribute: str = field(
        metadata={
            "doc": (
                "Source object identity."
            )
        },
    )
    canonical_attribute: str = field(
        metadata={
            "doc": (
                "Canonical object identity."
            )
        },
    )

class Localization(StrEnum):
    """
    Supported row-level change operations.
    """

    fr = "fr"
    de = "de"

@dataclass(slots=True, frozen=True)
class LocalizedMetadata:
    """
    Generic localized metadata.

    This model is intentionally reusable for classes, attributes and values.
    """

    names: dict[
        str,
        str,
    ] = field(
        default_factory=dict,
        metadata={
            "doc": (
                "Localized technical names keyed by language code. "
                "Examples: {'de': 'Absperr_Drosselorgan'}, "
                "{'fr': '...'}."
            )
        },
    )

    display_names: dict[
        str,
        str,
    ] = field(
        default_factory=dict,
        metadata={
            "doc": (
                "Localized technical names keyed by language code. "
                "Examples: {'de': 'Absperr_Drosselorgan'}, "
                "{'fr': '...'}."
            )
        },
    )

    def name(
        self,
        language: str,
    ) -> str | None:
        """
        Return the localized technical name for a language.
        """

        return self.names.get(
            language,
        )

    def display_name(
        self,
        language: str,
    ) -> str | None:
        """
        Return the localized display name for a language.
        Defaults to technical name if no display name is found.
        """

        name =  self.display_names.get(
            language,
        )

        if not name:
            name =  self.names.get(
                language,
            )
        return name


@dataclass(slots=True, frozen=True)
class CanonicalModelElementMetadata:
    """
    Base metadata for a canonical TEKSI Wastewater model element.

    The concrete subclass determines the element level:

    - class
    - attribute
    - value-list value
    """

    source_id: int = field(
        metadata={
            "doc": (
                "Numeric source identifier from the corresponding "
                "tww_sys dictionary table. The meaning is scoped by the "
                "concrete metadata level."
            )
        },
    )

    identifier: str = field(
        metadata={
            "doc": (
                "Canonical string identifier for this model element. The "
                "meaning is scoped by the concrete metadata level."
            )
        },
    )

    localized: LocalizedMetadata = field(
        default_factory=LocalizedMetadata,
        metadata={
            "doc": (
                "Localized technical names for this model element."
            )
        },
    )

@dataclass(slots=True, frozen=True)
class CanonicalClassMetadata(CanonicalModelElementMetadata):
    """
    Canonical metadata for a TEKSI Wastewater class/table.

    source_id:
        tww_sys.dictionary_od_table.id

    identifier:
        tww_sys.dictionary_od_table.tablename
    """


@dataclass(slots=True, frozen=True)
class CanonicalAttributeMetadata(CanonicalModelElementMetadata):
    """
    Canonical metadata for a TEKSI Wastewater attribute/field.

    source_id:
        tww_sys.dictionary_od_field.attribute_id

    identifier:
        tww_sys.dictionary_od_field.field_name
    """

    field_datatype: str | None = field(
        default=None,
        metadata={
            "doc": (
                "Source field datatype from canonical metadata. For TEKSI "
                "Wastewater dictionary metadata this corresponds to "
                "tww_sys.dictionary_od_field.field_datatype. Geometry "
                "attributes are identified with field_datatype='geometry'."
            )
        },
    )


@dataclass(slots=True, frozen=True)
class CanonicalValueMetadata(CanonicalModelElementMetadata):
    """
    Canonical metadata for a TEKSI Wastewater value-list value.

    source_id:
        tww_sys.dictionary_od_values.value_id

    identifier:
        tww_sys.dictionary_od_values.value_name
    """


@dataclass(slots=True, frozen=True)
class CanonicalModelMetadata:
    """
    Aggregate canonical metadata for TEKSI Wastewater classes, attributes and
    values.

    This is intentionally a data-only model. Lookup behavior belongs to
    CanonicalModelCapability implementations.
    """

    classes: dict[
        str,
        CanonicalClassMetadata,
    ] = field(
        default_factory=dict,
        metadata={
            "doc": (
                "Class metadata keyed by canonical class_id."
            )
        },
    )

    attributes: dict[
        tuple[
            str,
            str,
        ],
        CanonicalAttributeMetadata,
    ] = field(
        default_factory=dict,
        metadata={
            "doc": (
                "Attribute metadata keyed by "
                "(class_id, attribute_id)."
            )
        },
    )

    values: dict[
        tuple[
            str,
            str,
            str,
        ],
        CanonicalValueMetadata,
    ] = field(
        default_factory=dict,
        metadata={
            "doc": (
                "Value metadata keyed by "
                "(class_id, attribute_id, value_id)."
            )
        },
    )