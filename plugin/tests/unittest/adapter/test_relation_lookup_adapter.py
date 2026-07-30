from teksi_wastewater.utils.database_utils import DatabaseUtils
from teksi_wastewater.hooks_adapters.tww_relation_lookup_adapter import (
    TwwRelationLookupAdapter,
)


def test_tww_relation_lookup_adapter_returns_canonical_identities(
    monkeypatch,
):
    monkeypatch.setattr(
        DatabaseUtils,
        "fetchall",
        lambda query: [
            (
                "ch000000ws000001",
            ),
        ],
    )

    adapter = TwwRelationLookupAdapter(
        schema="tww_app",
    )

    objects = adapter.canonical_objects(
        local_class_id="wastewater_networkelement",
        related_class_id="wastewater_structure",
        local_attribute="fk_wastewater_structure",
        related_attribute="obj_id",
        value="ch000000ws000001",
    )

    assert len(objects) == 1

    assert (
        objects[0].class_id
        == "wastewater_structure"
    )

    assert objects[0].attributes == {
        "obj_id": "ch000000ws000001",
    }