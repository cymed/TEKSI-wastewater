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
class CanonicalClassMetadata:
    """
    Canonical metadata for a TEKSI Wastewater class/table.
    """
    class_source_id: int = field(
        metadata={
            "doc": (
                "Numeric class identifier from "
                "tww_sys.dictionary_od_field.class_id. This corresponds to "
                "dictionary_od_table.id, although the database table may not "
                "declare a foreign key."
            )
        },
    )

    class_id: str = field(
        metadata={
            "doc": (
                "Canonical class identifier. This corresponds to "
                "tww_sys.dictionary_od_table.tablename."
            )
        },
    )

    localized: LocalizedMetadata = field(
        default_factory=LocalizedMetadata,
        metadata={
            "doc": (
                "Localized technical class names loaded from "
                "dictionary_od_table.name_{lang} columns."
            )
        },
    )

@dataclass(slots=True, frozen=True)
class CanonicalAttributeMetadata:
    """
    Canonical metadata for a TEKSI Wastewater attribute/field.
    """

    class_source_id: int = field(
        metadata={
            "doc": (
                "Numeric class identifier from "
                "tww_sys.dictionary_od_field.class_id. This corresponds to "
                "dictionary_od_table.id, although the database table may not "
                "declare a foreign key."
            )
        },
    )

    attribute_source_id: int = field(
        metadata={
            "doc": (
                "Numeric attribute identifier from "
                "tww_sys.dictionary_od_field.attribute_id."
            )
        },
    )

    attribute_id: str = field(
        metadata={
            "doc": (
                "Canonical attribute identifier. This corresponds to "
                "tww_sys.dictionary_od_field.field_name."
            )
        },
    )

    field_datatype: str | None = field(
        default=None,
        metadata={
            "doc": (
                "Source field datatype from canonical metadata. For TEKSI "
                "Wastewater dictionary metadata this corresponds to "
                "tww_sys.dictionary_od_field.field_datatype. Geometry attributes "
                "are identified with field_datatype='geometry'."
            )
        },
    )

    localized: LocalizedMetadata = field(
        default_factory=LocalizedMetadata,
        metadata={
            "doc": (
                "Localized technical attribute names loaded from "
                "dictionary_od_field.field_name_{lang} columns."
            )
        },
    )

@dataclass(slots=True, frozen=True)
class CanonicalValueMetadata:
    """
    Canonical metadata for a TEKSI Wastewater value-list value.
    """

    class_source_id: int = field(
        metadata={
            "doc": (
                "Numeric class identifier from "
                "tww_sys.dictionary_od_values.class_id. This corresponds to "
                "dictionary_od_table.id, although the database table may not "
                "declare a foreign key."
            )
        },
    )

    attribute_source_id: int = field(
        metadata={
            "doc": (
                "Numeric attribute identifier from "
                "tww_sys.dictionary_od_values.attribute_id. This corresponds "
                "to dictionary_od_field.attribute_id, although the database "
                "table may not declare a foreign key."
            )
        },
    )

    value_source_id: int = field(
        metadata={
            "doc": (
                "Numeric value identifier from "
                "tww_sys.dictionary_od_values.value_id."
            )
        },
    )

    value_id: str = field(
        metadata={
            "doc": (
                "Canonical value identifier. This corresponds to "
                "tww_sys.dictionary_od_values.value_name."
            )
        },
    )

    localized: LocalizedMetadata = field(
        default_factory=LocalizedMetadata,
        metadata={
            "doc": (
                "Localized technical value names loaded from "
                "dictionary_od_values.value_name_{lang} columns."
            )
        },
    )

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
                "Class metadata keyed by canonical class_source_id."
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
                "(class_source_id, attribute_source_id)."
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
                "(class_source_id, attribute_source_id, value_source_id)."
            )
        },
    )