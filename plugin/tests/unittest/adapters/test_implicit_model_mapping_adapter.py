from __future__ import annotations

import pytest

from teksi_hooks.models.mapping import (
    AttributeMapping,
    ClassMapping,
    ModelMapping,
    ValueMapping,
)

from teksi_wastewater.hooks.adapters.tww_implicit_model_mapping_adapter import (
    TwwImplicitModelMappingAdapter,
)
from teksi_wastewater.utils.database_utils import (
    DatabaseUtils,
)


def _fake_fetchall(
    query,
):
    query_text = str(
        query,
    )

    if "dictionary_od_field" in query_text and "dictionary_od_values" not in query_text:
        return [
            (
                "wastewater_structure",
                "status",
                "Abwasserbauwerk",
                "Status",
            ),
            (
                "reach",
                "progression_geometry",
                "Haltung",
                "Geometrie",
            ),
            (
                "reach",
                "obj_id",
                "Haltung",
                "ObjektID",
            ),
            (
                "ignored_table",
                "ignored_field",
                None,
                "IgnoredAttribute",
            ),
            (
                "ignored_table",
                "ignored_field",
                "IgnoredClass",
                None,
            ),
        ]

    if "dictionary_od_values" in query_text:
        return [
            (
                "Abwasserbauwerk",
                "Status",
                "in_Betrieb",
                1234,
                "operational",
            ),
            (
                "Abwasserbauwerk",
                "Status",
                None,
                9999,
                "ignored",
            ),
        ]

    if "dictionary_od_table" in query_text:
        return [
            (
                "wastewater_structure",
                "Abwasserbauwerk",
            ),
            (
                "reach",
                "Haltung",
            ),
            (
                "ignored_table",
                None,
            ),
        ]

    raise AssertionError(
        f"Unexpected query: {query_text}"
    )


def test_implicit_model_mapping_loads_model_mapping(
    monkeypatch,
) -> None:
    monkeypatch.setattr(
        DatabaseUtils,
        "fetchall",
        _fake_fetchall,
    )

    adapter = TwwImplicitModelMappingAdapter(
        language="de",
    )

    mapping = adapter.model_mapping()

    assert isinstance(
        mapping,
        ModelMapping,
    )

    assert mapping.is_ssot is False

    assert set(
        mapping.classes,
    ) == {
        "Abwasserbauwerk",
        "Haltung",
    }

    wastewater_structure = mapping.classes[
        "Abwasserbauwerk"
    ]

    assert isinstance(
        wastewater_structure,
        ClassMapping,
    )

    assert wastewater_structure.canonical_class_id == "wastewater_structure"

    assert set(
        wastewater_structure.attributes,
    ) == {
        "Status",
    }

    status = wastewater_structure.attributes[
        "Status"
    ]

    assert isinstance(
        status,
        AttributeMapping,
    )

    assert status.canonical_class_id == "wastewater_structure"
    assert status.canonical_attr_id == "status"

    assert status.values == {
        "in_Betrieb": ValueMapping(
            canonical_value_id=1234,
            value="operational",
        ),
    }


def test_implicit_model_mapping_rejects_unknown_language() -> None:
    with pytest.raises(
        ValueError,
        match="Unsupported language",
    ):
        TwwImplicitModelMappingAdapter(
            language="es",
        )


def test_implicit_model_mapping_class_definition(
    monkeypatch,
) -> None:
    monkeypatch.setattr(
        DatabaseUtils,
        "fetchall",
        _fake_fetchall,
    )

    adapter = TwwImplicitModelMappingAdapter(
        language="de",
    )

    class_mapping = adapter.class_definition(
        "Abwasserbauwerk",
    )

    assert class_mapping.canonical_class_id == "wastewater_structure"


def test_implicit_model_mapping_try_class_definition_returns_none(
    monkeypatch,
) -> None:
    monkeypatch.setattr(
        DatabaseUtils,
        "fetchall",
        _fake_fetchall,
    )

    adapter = TwwImplicitModelMappingAdapter(
        language="de",
    )

    assert (
        adapter.try_class_definition(
            "DoesNotExist",
        )
        is None
    )


def test_implicit_model_mapping_attribute_definition(
    monkeypatch,
) -> None:
    monkeypatch.setattr(
        DatabaseUtils,
        "fetchall",
        _fake_fetchall,
    )

    adapter = TwwImplicitModelMappingAdapter(
        language="de",
    )

    attribute_mapping = adapter.attribute_definition(
        "Abwasserbauwerk",
        "Status",
    )

    assert attribute_mapping.canonical_class_id == "wastewater_structure"
    assert attribute_mapping.canonical_attr_id == "status"


def test_implicit_model_mapping_try_attribute_definition_returns_none(
    monkeypatch,
) -> None:
    monkeypatch.setattr(
        DatabaseUtils,
        "fetchall",
        _fake_fetchall,
    )

    adapter = TwwImplicitModelMappingAdapter(
        language="de",
    )

    assert (
        adapter.try_attribute_definition(
            "Abwasserbauwerk",
            "Missing",
        )
        is None
    )


def test_implicit_model_mapping_value_mapping(
    monkeypatch,
) -> None:
    monkeypatch.setattr(
        DatabaseUtils,
        "fetchall",
        _fake_fetchall,
    )

    adapter = TwwImplicitModelMappingAdapter(
        language="de",
    )

    value_mapping = adapter.value_mapping(
        "Abwasserbauwerk",
        "Status",
        "in_Betrieb",
    )

    assert value_mapping == ValueMapping(
        canonical_value_id=1234,
        value="operational",
    )


def test_implicit_model_mapping_try_value_mapping_returns_none(
    monkeypatch,
) -> None:
    monkeypatch.setattr(
        DatabaseUtils,
        "fetchall",
        _fake_fetchall,
    )

    adapter = TwwImplicitModelMappingAdapter(
        language="de",
    )

    assert (
        adapter.try_value_mapping(
            "Abwasserbauwerk",
            "Status",
            "missing_value",
        )
        is None
    )