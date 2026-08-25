from __future__ import annotations

from collections.abc import Sequence
from typing import Any

from teksi_hooks.models.canonical_object import (
    CanonicalAttributeMetadata,
    CanonicalClassMetadata,
    CanonicalModelMetadata,
    CanonicalValueMetadata,
    LocalizedMetadata,
)

from teksi_wastewater.hooks.adapters import (
    tww_canonical_model_adapter as adapter_module,
)
from teksi_wastewater.hooks.adapters.tww_canonical_model_adapter import (
    TwwCanonicalModelAdapter,
    TwwLanguage,
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
                "name_de": "Abwasserbauwerk",
                "name_fr": "Ouvrage des eaux usées",
                "name_it": "Manufatto delle acque di scarico",
                "name_en": "Wastewater structure",
            },
            {
                "source_id": 2,
                "class_id": "reach",
                "name_de": "Haltung",
                "name_fr": "Tronçon",
                "name_it": "Tratta",
                "name_en": "Reach",
            },
        ],
    )

    adapter = TwwCanonicalModelAdapter()

    classes = adapter.classes()

    assert classes == {
        "wastewater_structure": CanonicalClassMetadata(
            source_id=1,
            identifier="wastewater_structure",
            localized=LocalizedMetadata(
                names={
                    "de": "Abwasserbauwerk",
                    "fr": "Ouvrage des eaux usées",
                    "it": "Manufatto delle acque di scarico",
                    "en": "Wastewater structure",
                },
            ),
        ),
        "reach": CanonicalClassMetadata(
            source_id=2,
            identifier="reach",
            localized=LocalizedMetadata(
                names={
                    "de": "Haltung",
                    "fr": "Tronçon",
                    "it": "Tratta",
                    "en": "Reach",
                },
            ),
        ),
    }


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
                "field_name_de": "Status",
                "field_name_fr": "État",
                "field_name_it": "Stato",
                "field_name_en": "Status",
            },
            {
                "source_id": 11,
                "class_id": "wastewater_structure",
                "attribute_id": "detail_geometry3d_geometry",
                "field_datatype": "geometry",
                "field_name_de": "Detailgeometrie",
                "field_name_fr": "Géométrie détaillée",
                "field_name_it": "Geometria dettagliata",
                "field_name_en": "Detail geometry",
            },
        ],
    )

    adapter = TwwCanonicalModelAdapter()

    attributes = adapter.attributes(
        class_id="wastewater_structure",
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
        localized=LocalizedMetadata(
            names={
                "de": "Status",
                "fr": "État",
                "it": "Stato",
                "en": "Status",
            },
        ),
    )

    geometry_attribute = attributes[
        (
            "wastewater_structure",
            "detail_geometry3d_geometry",
        )
    ]

    assert geometry_attribute == CanonicalAttributeMetadata(
        source_id=11,
        identifier="detail_geometry3d_geometry",
        field_datatype="geometry",
        localized=LocalizedMetadata(
            names={
                "de": "Detailgeometrie",
                "fr": "Géométrie détaillée",
                "it": "Geometria dettagliata",
                "en": "Detail geometry",
            },
        ),
    )


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
                "value_name_de": "geplant",
                "value_name_fr": "planifié",
                "value_name_it": "pianificato",
                "value_name_en": "planned",
            },
            {
                "source_id": 101,
                "class_id": "wastewater_structure",
                "attribute_id": "status",
                "value_id": "other.in_operation",
                "value_name_de": "in Betrieb",
                "value_name_fr": "en service",
                "value_name_it": "in esercizio",
                "value_name_en": "in operation",
            },
        ],
    )

    adapter = TwwCanonicalModelAdapter()

    values = adapter.values(
        class_id="wastewater_structure",
        attribute_id="status",
    )

    assert values[
        (
            "wastewater_structure",
            "status",
            "other.planned",
        )
    ] == CanonicalValueMetadata(
        source_id=100,
        identifier="other.planned",
        localized=LocalizedMetadata(
            names={
                "de": "geplant",
                "fr": "planifié",
                "it": "pianificato",
                "en": "planned",
            },
        ),
    )

    assert values[
        (
            "wastewater_structure",
            "status",
            "other.in_operation",
        )
    ] == CanonicalValueMetadata(
        source_id=101,
        identifier="other.in_operation",
        localized=LocalizedMetadata(
            names={
                "de": "in Betrieb",
                "fr": "en service",
                "it": "in esercizio",
                "en": "in operation",
            },
        ),
    )


def test_tww_canonical_model_adapter_builds_canonical_model(
    monkeypatch,
) -> None:
    _patch_database_utils(
        monkeypatch,
        class_rows=[
            {
                "source_id": 1,
                "class_id": "reach",
                "name_de": "Haltung",
                "name_fr": "Tronçon",
                "name_it": "Tratta",
                "name_en": "Reach",
            },
        ],
        attribute_rows=[
            {
                "source_id": 10,
                "class_id": "reach",
                "attribute_id": "progression_geometry",
                "field_datatype": "geometry",
                "field_name_de": "Verlauf",
                "field_name_fr": "Tracé",
                "field_name_it": "Tracciato",
                "field_name_en": "Progression geometry",
            },
        ],
        value_rows=[
            {
                "source_id": 100,
                "class_id": "reach",
                "attribute_id": "status",
                "value_id": "active",
                "value_name_de": "aktiv",
                "value_name_fr": "actif",
                "value_name_it": "attivo",
                "value_name_en": "active",
            },
        ],
    )

    adapter = TwwCanonicalModelAdapter()

    metadata = adapter.canonical_model()

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

    assert metadata.classes["reach"].localized.names == {
        "de": "Haltung",
        "fr": "Tronçon",
        "it": "Tratta",
        "en": "Reach",
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
                "name_de": "Haltung",
                "name_fr": "Tronçon",
                "name_it": "Tratta",
                "name_en": "Reach",
            },
        ],
    )

    adapter = TwwCanonicalModelAdapter()

    metadata = adapter.class_metadata(
        "reach",
    )

    assert metadata is not None
    assert metadata.identifier == "reach"

    assert metadata.localized.names == {
        "de": "Haltung",
        "fr": "Tronçon",
        "it": "Tratta",
        "en": "Reach",
    }

    assert adapter.class_metadata(
        "unknown",
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
                "field_name_de": "Verlauf",
                "field_name_fr": "Tracé",
                "field_name_it": "Tracciato",
                "field_name_en": "Progression geometry",
            },
        ],
    )

    adapter = TwwCanonicalModelAdapter()

    metadata = adapter.attribute_metadata(
        "reach",
        "progression_geometry",
    )

    assert metadata is not None
    assert metadata.identifier == "progression_geometry"
    assert metadata.field_datatype == "geometry"

    assert metadata.localized.names == {
        "de": "Verlauf",
        "fr": "Tracé",
        "it": "Tracciato",
        "en": "Progression geometry",
    }

    assert adapter.attribute_metadata(
        "reach",
        "unknown",
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
                "value_name_de": "geplant",
                "value_name_fr": "planifié",
                "value_name_it": "pianificato",
                "value_name_en": "planned",
            },
        ],
    )

    adapter = TwwCanonicalModelAdapter()

    metadata = adapter.value_metadata(
        "wastewater_structure",
        "status",
        "other.planned",
    )

    assert metadata is not None
    assert metadata.identifier == "other.planned"

    assert metadata.localized.names == {
        "de": "geplant",
        "fr": "planifié",
        "it": "pianificato",
        "en": "planned",
    }

    assert adapter.value_metadata(
        "wastewater_structure",
        "status",
        "unknown",
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
                "field_name_de": "Verlauf",
                "field_name_fr": "Tracé",
                "field_name_it": "Tracciato",
                "field_name_en": "Progression geometry",
            },
            {
                "source_id": 11,
                "class_id": "reach",
                "attribute_id": "identifier",
                "field_datatype": "text",
                "field_name_de": "Bezeichnung",
                "field_name_fr": "Désignation",
                "field_name_it": "Identificatore",
                "field_name_en": "Identifier",
            },
        ],
    )

    adapter = TwwCanonicalModelAdapter()

    assert adapter.is_geometry_attribute(
        "reach",
        "progression_geometry",
    )

    assert not adapter.is_geometry_attribute(
        "reach",
        "identifier",
    )

    assert not adapter.is_geometry_attribute(
        "reach",
        "missing_attribute",
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
                "field_name_de": "Verlauf",
                "field_name_fr": "Tracé",
                "field_name_it": "Tracciato",
                "field_name_en": "Progression geometry",
            },
            {
                "source_id": 11,
                "class_id": "reach",
                "attribute_id": "identifier",
                "field_datatype": "text",
                "field_name_de": "Bezeichnung",
                "field_name_fr": "Désignation",
                "field_name_it": "Identificatore",
                "field_name_en": "Identifier",
            },
            {
                "source_id": 12,
                "class_id": "wastewater_structure",
                "attribute_id": "detail_geometry3d_geometry",
                "field_datatype": " geometry ",
                "field_name_de": "Detailgeometrie",
                "field_name_fr": "Géométrie détaillée",
                "field_name_it": "Geometria dettagliata",
                "field_name_en": "Detail geometry",
            },
        ],
    )

    adapter = TwwCanonicalModelAdapter()

    assert adapter.geometry_attribute_names(
        "reach",
    ) == (
        "progression_geometry",
    )

    assert adapter.geometry_attribute_names(
        "wastewater_structure",
    ) == (
        "detail_geometry3d_geometry",
    )


def test_tww_canonical_model_adapter_uses_custom_schema_and_all_language_columns(
    monkeypatch,
) -> None:
    queries = _patch_database_utils(
        monkeypatch,
    )

    adapter = TwwCanonicalModelAdapter(
        schema="custom_sys",
    )

    adapter.classes()

    adapter.attributes(
        class_id="reach",
    )

    adapter.values(
        class_id="reach",
        attribute_id="status",
    )

    combined = "\n".join(
        queries,
    )

    assert '"custom_sys"' in combined

    for column_name in (
        "name_de",
        "name_fr",
        "name_it",
        "name_en",
        "field_name_de",
        "field_name_fr",
        "field_name_it",
        "field_name_en",
        "value_name_de",
        "value_name_fr",
        "value_name_it",
        "value_name_en",
    ):
        assert column_name in combined

    assert "'reach'" in combined
    assert "'status'" in combined


def test_tww_canonical_model_adapter_omits_empty_localizations() -> None:
    adapter = TwwCanonicalModelAdapter()

    localized = adapter._localized_metadata(
        row={
            "name_de": "Haltung",
            "name_fr": None,
            "name_it": "",
            "name_en": "Reach",
        },
        name_prefix="name",
    )

    assert localized == LocalizedMetadata(
        names={
            "de": "Haltung",
            "en": "Reach",
        },
    )


def test_tww_canonical_model_adapter_respects_configured_languages() -> None:
    adapter = TwwCanonicalModelAdapter(
        languages=(
            TwwLanguage.DE,
            TwwLanguage.FR,
        ),
    )

    localized = adapter._localized_metadata(
        row={
            "name_de": "Haltung",
            "name_fr": "Tronçon",
            "name_it": "Tratta",
            "name_en": "Reach",
        },
        name_prefix="name",
    )

    assert localized == LocalizedMetadata(
        names={
            "de": "Haltung",
            "fr": "Tronçon",
        },
    )


def test_tww_canonical_model_adapter_returns_empty_localized_metadata() -> None:
    adapter = TwwCanonicalModelAdapter()

    localized = adapter._localized_metadata(
        row={
            "name_de": None,
            "name_fr": "",
            "name_it": None,
            "name_en": "",
        },
        name_prefix="name",
    )

    assert localized == LocalizedMetadata()