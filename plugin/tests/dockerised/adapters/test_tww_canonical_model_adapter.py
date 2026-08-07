import pytest

from teksi_wastewater.hooks.adapters.tww_canonical_model_adapter import (
    TwwCanonicalModelAdapter,
)
from tww_hooks.models.canonical_object import (
    Localization,
)


pytestmark = pytest.mark.no_qgis


def test_tww_canonical_model_adapter_loads_classes(
    clean_db_once,
) -> None:
    adapter = TwwCanonicalModelAdapter()

    classes = adapter.classes()

    assert classes

    assert all(
        class_id == metadata.identifier
        for class_id, metadata in classes.items()
    )

    assert all(
        metadata.source_id is not None
        for metadata in classes.values()
    )


def test_tww_canonical_model_adapter_loads_attributes(
    clean_db_once,
) -> None:
    adapter = TwwCanonicalModelAdapter()

    attributes = adapter.attributes()

    assert attributes

    assert any(
        metadata.identifier == "obj_id"
        for metadata in attributes.values()
    )

    assert all(
        attribute_id == metadata.identifier
        for (
            _class_id,
            attribute_id,
        ),
        metadata in attributes.items()
    )

    assert all(
        metadata.source_id is not None
        for metadata in attributes.values()
    )


def test_tww_canonical_model_adapter_loads_values(
    clean_db_once,
) -> None:
    adapter = TwwCanonicalModelAdapter()

    values = adapter.values()

    assert values

    assert all(
        value_id == metadata.identifier
        for (
            _class_id,
            _attribute_id,
            value_id,
        ),
        metadata in values.items()
    )

    assert all(
        metadata.source_id is not None
        for metadata in values.values()
    )


def test_tww_canonical_model_adapter_loads_localized_classes(
    clean_db_once,
) -> None:
    adapter = TwwCanonicalModelAdapter()

    classes = adapter.classes(
        language=Localization.de,
    )

    assert classes

    assert any(
        Localization.de in metadata.localized.names
        for metadata in classes.values()
    )


def test_tww_canonical_model_adapter_loads_localized_attributes(
    clean_db_once,
) -> None:
    adapter = TwwCanonicalModelAdapter()

    attributes = adapter.attributes(
        language=Localization.de,
    )

    assert attributes

    assert any(
        Localization.de in metadata.localized.names
        for metadata in attributes.values()
    )


def test_tww_canonical_model_adapter_loads_localized_values(
    clean_db_once,
) -> None:
    adapter = TwwCanonicalModelAdapter()

    values = adapter.values(
        language=Localization.de,
    )

    assert values

    assert any(
        Localization.de in metadata.localized.names
        for metadata in values.values()
    )


def test_tww_canonical_model_adapter_loads_geometry_metadata(
    clean_db_once,
) -> None:
    adapter = TwwCanonicalModelAdapter()

    attributes = adapter.attributes()

    geometry_items = [
        (
            class_id,
            attribute_id,
            metadata,
        )
        for (
            class_id,
            attribute_id,
        ),
        metadata in attributes.items()
        if metadata.field_datatype is not None
        and metadata.field_datatype.strip().lower() == "geometry"
    ]

    assert geometry_items

    class_id, attribute_id, metadata = geometry_items[0]

    assert metadata.identifier == attribute_id

    assert adapter.is_geometry_attribute(
        class_id=class_id,
        attribute_id=attribute_id,
    )

    assert (
        attribute_id
        in adapter.geometry_attribute_names(
            class_id,
        )
    )


def test_tww_canonical_model_adapter_loads_complete_model(
    clean_db_once,
) -> None:
    adapter = TwwCanonicalModelAdapter()

    metadata = adapter.canonical_model()

    assert metadata.classes
    assert metadata.attributes
    assert metadata.values