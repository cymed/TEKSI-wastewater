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

from ..helpers import (
    FakeQueryResult,
    FakeColumn,
    fake_connection_factory,
)

CLASS_QUERY_RESULT = FakeQueryResult(
    columns=(
        FakeColumn(
            "class_id",
        ),
        FakeColumn(
            "source_class_id",
        ),
    ),
    rows=(
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
    ),
)


ATTRIBUTE_QUERY_RESULT = FakeQueryResult(
    columns=(
        FakeColumn(
            "class_id",
        ),
        FakeColumn(
            "attribute_id",
        ),
        FakeColumn(
            "source_class_id",
        ),
        FakeColumn(
            "source_attribute_id",
        ),
    ),
    rows=(
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
    ),
)


VALUE_QUERY_RESULT = FakeQueryResult(
    columns=(
        FakeColumn(
            "source_class_id",
        ),
        FakeColumn(
            "source_attribute_id",
        ),
        FakeColumn(
            "source_value_id",
        ),
        FakeColumn(
            "canonical_value_id",
        ),
        FakeColumn(
            "canonical_value",
        ),
    ),
    rows=(
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
    ),
)


@pytest.fixture
def implicit_mapping_adapter():
    connection_factory, cursor = fake_connection_factory(
        results=(
            FakeQueryResult(
                contains="dictionary_od_table",
                columns=CLASS_QUERY_RESULT.columns,
                rows=CLASS_QUERY_RESULT.rows,
            ),
            FakeQueryResult(
                contains="dictionary_od_field",
                excludes="dictionary_od_values",
                columns=ATTRIBUTE_QUERY_RESULT.columns,
                rows=ATTRIBUTE_QUERY_RESULT.rows,
            ),
            FakeQueryResult(
                contains="dictionary_od_values",
                columns=VALUE_QUERY_RESULT.columns,
                rows=VALUE_QUERY_RESULT.rows,
            ),
        )
    )

    adapter = TwwImplicitModelMappingAdapter(
        language="de",
        connection_factory=connection_factory,
    )

    return (
        adapter,
        cursor,
    )
    
def test_implicit_model_mapping_loads_model_mapping(
    implicit_mapping_adapter,
) -> None:
    adapter, cursor = implicit_mapping_adapter

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

    assert (
        wastewater_structure.canonical_class_id
        == "wastewater_structure"
    )

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

    assert (
        status.canonical_class_id
        == "wastewater_structure"
    )

    assert status.canonical_attr_id == "status"

    assert status.values == {
        "in_Betrieb": ValueMapping(
            canonical_value_id=1234,
            value="operational",
        ),
    }

    assert len(
        cursor.executed,
    ) == 3

    
def test_implicit_model_mapping_rejects_unknown_language() -> None:
    with pytest.raises(
        ValueError,
        match="Unsupported language",
    ):
        TwwImplicitModelMappingAdapter(
            language="es",
        )


def test_implicit_model_mapping_class_definition(
    implicit_mapping_adapter,
) -> None:
    adapter, _ = implicit_mapping_adapter

    class_mapping = adapter.class_definition(
        "Abwasserbauwerk",
    )

    assert (
        class_mapping.canonical_class_id
        == "wastewater_structure"
    )


def test_implicit_model_mapping_try_class_definition_returns_none(
    implicit_mapping_adapter,
) -> None:
    adapter, _ = implicit_mapping_adapter

    assert (
        adapter.try_class_definition(
            "DoesNotExist",
        )
        is None
    )


def test_implicit_model_mapping_attribute_definition(
    implicit_mapping_adapter,
) -> None:
    adapter, _ = implicit_mapping_adapter

    attribute_mapping = adapter.attribute_definition(
        "Abwasserbauwerk",
        "Status",
    )

    assert (
        attribute_mapping.canonical_class_id
        == "wastewater_structure"
    )

    assert (
        attribute_mapping.canonical_attr_id
        == "status"
    )


def test_implicit_model_mapping_try_attribute_definition_returns_none(
    implicit_mapping_adapter,
) -> None:
    adapter, _ = implicit_mapping_adapter

    assert (
        adapter.try_attribute_definition(
            "Abwasserbauwerk",
            "Missing",
        )
        is None
    )


def test_implicit_model_mapping_value_mapping(
    implicit_mapping_adapter,
) -> None:
    adapter, _ = implicit_mapping_adapter

    value_mapping = adapter.value_mapping(
        "Abwasserbauwerk",
        "Status",
        "in_Betrieb",
    )

    assert value_mapping == ValueMapping(
        canonical_value_id=1234,
        value="operational",
    )