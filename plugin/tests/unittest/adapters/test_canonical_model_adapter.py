from __future__ import annotations

from collections.abc import Sequence
from typing import Any

import pytest

from teksi_hooks.models.canonical_object import (
    CanonicalAttributeMetadata,
    CanonicalClassMetadata,
    CanonicalModelMetadata,
    CanonicalValueMetadata,
    Localization,
)

from teksi_wastewater.hooks.adapters import tww_canonical_model_adapter as adapter_module
from teksi_wastewater.hooks.adapters.tww_canonical_model_adapter import (
    TwwCanonicalModelAdapter,
)


def _patch_database_utils(
    monkeypatch,
    *,
    class_rows: Sequence[dict[str, Any]] = (),
    attribute_rows: Sequence[dict[str, Any]] = (),
    value_rows: Sequence[dict[str, Any]] = (),
) -> list:
    queries: list[str] = []

    def wrap_identifier(
        value: str,
    ) -> str:
        return f'"{value}"'

    def wrap_literal(
        value: Any,
    ) -> str:
        return repr(
            value,
        )

    def compose_sql(
        query: str,
        *args,
        **kwargs,
    ) -> str:
        if kwargs:
            return query.format(
                **kwargs,
            )

        return query

    def fetchall_dict(
        query,
    ) -> list[dict[str, Any]]:
        query_text = str(
            query,
        )

        queries.append(
            query_text,
        )

        if "dictionary_od_values" in query_text:
            return list(
                value_rows,
            )

        if "dictionary_od_field" in query_text:
            return list(
                attribute_rows,
            )

        if "dictionary_od_table" in query_text:
            return list(
                class_rows,
            )

        raise AssertionError(
            f"Unexpected query: {query_text}"
        )

    monkeypatch.setattr(
        adapter_module.DatabaseUtils,
        "wrap_identifier",
        staticmethod(
            wrap_identifier,
        ),
    )
    monkeypatch.setattr(
        adapter_module.DatabaseUtils,
        "wrap_literal",
        staticmethod(
            wrap_literal,
        ),
    )
    monkeypatch.setattr(
        adapter_module.DatabaseUtils,
        "compose_sql",
        staticmethod(
            compose_sql,
        ),
    )
    monkeypatch.setattr(
        adapter_module.DatabaseUtils,
        "fetchall_dict",
        staticmethod(
            fetchall_dict,
        ),
    )

    return queries


def test_tww_canonical_model_adapter_loads_classes(
    monkeypatch,
) -> None:
    _patch_database_utils(
        monkeypatch,
        class_rows=[
            {
                "source_id": 1,
                "class_id": "wastewater_structure",
                "localized_name": "Abwasserbauwerk",
            },
            {
                "source_id": 2,
                "class_id": "reach",
                "localized_name": "Haltung",
            },
        ],
    )

    adapter = TwwCanonicalModelAdapter()

    classes = adapter.classes(
        language=Localization.de,
    )

    assert classes == {
        "wastewater_structure": CanonicalClassMetadata(
            source_id=1,
            identifier="wastewater_structure",
            localized=classes["wastewater_structure"].localized,
        ),
        "reach": CanonicalClassMetadata(
            source_id=2,
            identifier="reach",
            localized=classes["reach"].localized,
        ),
    }

    assert classes["wastewater_structure"].localized.name(
        Localization.de,
    ) == "Abwasserbauwerk"
    assert classes["reach"].localized.name(
        Localization.de,
    ) == "Haltung"


def test_tww_canonical_model_adapter_loads_attributes(
    monkeypatch,
) -> None:
    _patch_database_utils(
        monkeypatch,
        attribute_rows=[
            {
                "source_id": 10,
                "class_id": "wastewater_structure",
                "attribute_id": "status",
                "field_datatype": "integer",
                "localized_name": "Status",
            },
            {
                "source_id": 11,
                "class_id": "wastewater_structure",
                "attribute_id": "detail_geometry3d_geometry",
                "field_datatype": "geometry",
                "localized_name": "Detailgeometrie",
            },
        ],
    )

    adapter = TwwCanonicalModelAdapter()

    attributes = adapter.attributes(
        class_id="wastewater_structure",
        language=Localization.de,
    )

    assert attributes[
        (
            "wastewater_structure",
            "status",
        )
    ] == CanonicalAttributeMetadata(
        source_id=10,
        identifier="status",
        field_datatype="integer",
        localized=attributes[
            (
                "wastewater_structure",
                "status",
            )
        ].localized,
    )

    geometry_attribute = attributes[
        (
            "wastewater_structure",
            "detail_geometry3d_geometry",
        )
    ]

    assert geometry_attribute.identifier == "detail_geometry3d_geometry"
    assert geometry_attribute.field_datatype == "geometry"
    assert geometry_attribute.localized.name(
        Localization.de,
    ) == "Detailgeometrie"


def test_tww_canonical_model_adapter_loads_values(
    monkeypatch,
) -> None:
    _patch_database_utils(
        monkeypatch,
        value_rows=[
            {
                "source_id": 100,
                "class_id": "wastewater_structure",
                "attribute_id": "status",
                "value_id": "other.planned",
                "localized_name": "geplant",
            },
            {
                "source_id": 101,
                "class_id": "wastewater_structure",
                "attribute_id": "status",
                "value_id": "other.in_operation",
                "localized_name": "in Betrieb",
            },
        ],
    )

    adapter = TwwCanonicalModelAdapter()

    values = adapter.values(
        class_id="wastewater_structure",
        attribute_id="status",
        language=Localization.de,
    )

    planned = values[
        (
            "wastewater_structure",
            "status",
            "other.planned",
        )
    ]

    assert planned == CanonicalValueMetadata(
        source_id=100,
        identifier="other.planned",
        localized=planned.localized,
    )
    assert planned.localized.name(
        Localization.de,
    ) == "geplant"

    in_operation = values[
        (
            "wastewater_structure",
            "status",
            "other.in_operation",
        )
    ]

    assert in_operation.identifier == "other.in_operation"
    assert in_operation.localized.name(
        Localization.de,
    ) == "in Betrieb"


def test_tww_canonical_model_adapter_builds_canonical_model(
    monkeypatch,
) -> None:
    _patch_database_utils(
        monkeypatch,
        class_rows=[
            {
                "source_id": 1,
                "class_id": "reach",
                "localized_name": "Haltung",
            },
        ],
        attribute_rows=[
            {
                "source_id": 10,
                "class_id": "reach",
                "attribute_id": "progression_geometry",
                "field_datatype": "geometry",
                "localized_name": "Verlauf",
            },
        ],
        value_rows=[
            {
                "source_id": 100,
                "class_id": "reach",
                "attribute_id": "status",
                "value_id": "active",
                "localized_name": "aktiv",
            },
        ],
    )

    adapter = TwwCanonicalModelAdapter()

    metadata = adapter.canonical_model(
        language=Localization.de,
    )

    assert isinstance(
        metadata,
        CanonicalModelMetadata,
    )
    assert set(
        metadata.classes,
    ) == {
        "reach",
    }
    assert set(
        metadata.attributes,
    ) == {
        (
            "reach",
            "progression_geometry",
        ),
    }
    assert set(
        metadata.values,
    ) == {
        (
            "reach",
            "status",
            "active",
        ),
    }


def test_tww_canonical_model_adapter_returns_single_class_metadata(
    monkeypatch,
) -> None:
    _patch_database_utils(
        monkeypatch,
        class_rows=[
            {
                "source_id": 1,
                "class_id": "reach",
                "localized_name": "Haltung",
            },
        ],
    )

    adapter = TwwCanonicalModelAdapter()

    metadata = adapter.class_metadata(
        "reach",
        language=Localization.de,
    )

    assert metadata is not None
    assert metadata.identifier == "reach"
    assert metadata.localized.name(
        Localization.de,
    ) == "Haltung"

    assert adapter.class_metadata(
        "unknown",
        language=Localization.de,
    ) is None


def test_tww_canonical_model_adapter_returns_single_attribute_metadata(
    monkeypatch,
) -> None:
    _patch_database_utils(
        monkeypatch,
        attribute_rows=[
            {
                "source_id": 10,
                "class_id": "reach",
                "attribute_id": "progression_geometry",
                "field_datatype": "geometry",
                "localized_name": "Verlauf",
            },
        ],
    )

    adapter = TwwCanonicalModelAdapter()

    metadata = adapter.attribute_metadata(
        "reach",
        "progression_geometry",
        language=Localization.de,
    )

    assert metadata is not None
    assert metadata.identifier == "progression_geometry"
    assert metadata.field_datatype == "geometry"

    assert adapter.attribute_metadata(
        "reach",
        "unknown",
        language=Localization.de,
    ) is None


def test_tww_canonical_model_adapter_returns_single_value_metadata(
    monkeypatch,
) -> None:
    _patch_database_utils(
        monkeypatch,
        value_rows=[
            {
                "source_id": 100,
                "class_id": "wastewater_structure",
                "attribute_id": "status",
                "value_id": "other.planned",
                "localized_name": "geplant",
            },
        ],
    )

    adapter = TwwCanonicalModelAdapter()

    metadata = adapter.value_metadata(
        "wastewater_structure",
        "status",
        "other.planned",
        language=Localization.de,
    )

    assert metadata is not None
    assert metadata.identifier == "other.planned"
    assert metadata.localized.name(
        Localization.de,
    ) == "geplant"

    assert adapter.value_metadata(
        "wastewater_structure",
        "status",
        "unknown",
        language=Localization.de,
    ) is None


def test_tww_canonical_model_adapter_detects_geometry_attributes(
    monkeypatch,
) -> None:
    _patch_database_utils(
        monkeypatch,
        attribute_rows=[
            {
                "source_id": 10,
                "class_id": "reach",
                "attribute_id": "progression_geometry",
                "field_datatype": "geometry",
                "localized_name": "Verlauf",
            },
            {
                "source_id": 11,
                "class_id": "reach",
                "attribute_id": "identifier",
                "field_datatype": "text",
                "localized_name": "Bezeichnung",
            },
        ],
    )

    adapter = TwwCanonicalModelAdapter()

    assert adapter.is_geometry_attribute(
        "reach",
        "progression_geometry",
        language=Localization.de,
    )

    assert not adapter.is_geometry_attribute(
        "reach",
        "identifier",
        language=Localization.de,
    )

    assert not adapter.is_geometry_attribute(
        "reach",
        "missing_attribute",
        language=Localization.de,
    )


def test_tww_canonical_model_adapter_returns_geometry_attribute_names(
    monkeypatch,
) -> None:
    _patch_database_utils(
        monkeypatch,
        attribute_rows=[
            {
                "source_id": 10,
                "class_id": "reach",
                "attribute_id": "progression_geometry",
                "field_datatype": "geometry",
                "localized_name": "Verlauf",
            },
            {
                "source_id": 11,
                "class_id": "reach",
                "attribute_id": "identifier",
                "field_datatype": "text",
                "localized_name": "Bezeichnung",
            },
            {
                "source_id": 12,
                "class_id": "wastewater_structure",
                "attribute_id": "detail_geometry3d_geometry",
                "field_datatype": " geometry ",
                "localized_name": "Detailgeometrie",
            },
        ],
    )

    adapter = TwwCanonicalModelAdapter()

    assert adapter.geometry_attribute_names(
        "reach",
        language=Localization.de,
    ) == (
        "progression_geometry",
    )

    assert adapter.geometry_attribute_names(
        "wastewater_structure",
        language=Localization.de,
    ) == (
        "detail_geometry3d_geometry",
    )


def test_tww_canonical_model_adapter_uses_schema_and_language_in_queries(
    monkeypatch,
) -> None:
    queries = _patch_database_utils(
        monkeypatch,
        class_rows=[],
        attribute_rows=[],
        value_rows=[],
    )

    adapter = TwwCanonicalModelAdapter(
        schema="custom_sys",
    )

    adapter.classes(
        language=Localization.fr,
    )
    adapter.attributes(
        class_id="reach",
        language=Localization.fr,
    )
    adapter.values(
        class_id="reach",
        attribute_id="status",
        language=Localization.fr,
    )

    combined = "\n".join(
        queries,
    )

    assert '"custom_sys"' in combined
    assert "name_fr" in combined
    assert "field_name_fr" in combined
    assert "value_name_fr" in combined
    assert "reach" in combined
    assert "status" in combined


def test_tww_canonical_model_adapter_empty_localized_metadata() -> None:
    adapter = TwwCanonicalModelAdapter()

    localized = adapter._localized_metadata(
        language=Localization.de,
        value=None,
    )

    assert localized == LocalizedMetadata()
