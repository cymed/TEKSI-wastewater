from __future__ import annotations

from teksi_hooks.models.canonical_object import (
    CanonicalObjectIdentity,
)

from teksi_wastewater.hooks.adapters.tww_relation_lookup_adapter import (
    TwwRelationLookupAdapter,
)
from teksi_wastewater.utils.database_utils import (
    DatabaseUtils,
)


def test_tww_relation_lookup_adapter_returns_canonical_identities(
    monkeypatch,
) -> None:
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

    assert len(
        objects,
    ) == 1

    assert objects[0].class_id == "wastewater_structure"

    assert objects[0].attributes == {
        "obj_id": "ch000000ws000001",
    }


def test_tww_relation_lookup_adapter_returns_empty_tuple_without_matches(
    monkeypatch,
) -> None:
    monkeypatch.setattr(
        DatabaseUtils,
        "fetchall",
        lambda query: [],
    )

    adapter = TwwRelationLookupAdapter(
        schema="tww_app",
    )

    objects = adapter.canonical_objects(
        local_class_id="wastewater_networkelement",
        related_class_id="wastewater_structure",
        local_attribute="fk_wastewater_structure",
        related_attribute="obj_id",
        value="missing",
    )

    assert objects == ()


def test_tww_relation_lookup_adapter_current_object_returns_none_without_match(
    monkeypatch,
) -> None:
    monkeypatch.setattr(
        DatabaseUtils,
        "fetchall_dict",
        lambda query: [],
    )

    adapter = TwwRelationLookupAdapter(
        schema="tww_od",
    )

    current = adapter.current_object(
        CanonicalObjectIdentity(
            class_id="wastewater_structure",
            attributes={
                "obj_id": "ch000000ws000001",
            },
        )
    )

    assert current is None


def test_tww_relation_lookup_adapter_current_object_returns_canonical_object(
    monkeypatch,
) -> None:
    monkeypatch.setattr(
        DatabaseUtils,
        "fetchall_dict",
        lambda query: [
            {
                "obj_id": "ch000000ws000001",
                "status": "operational",
                "fk_provider": "ch000000provider1",
                "last_modification": "2026-01-01T12:00:00",
            }
        ],
    )

    adapter = TwwRelationLookupAdapter(
        schema="tww_od",
    )

    identity = CanonicalObjectIdentity(
        class_id="wastewater_structure",
        attributes={
            "obj_id": "ch000000ws000001",
        },
    )

    current = adapter.current_object(
        identity,
    )

    assert current is not None

    assert current.identity == identity

    assert current.values == {
        "status": "operational",
        "fk_provider": "ch000000provider1",
        "last_modification": "2026-01-01T12:00:00",
    }

    assert current.last_modification == "2026-01-01T12:00:00"


def test_tww_relation_lookup_adapter_current_object_excludes_identity_attributes(
    monkeypatch,
) -> None:
    monkeypatch.setattr(
        DatabaseUtils,
        "fetchall_dict",
        lambda query: [
            {
                "obj_id": "ch000000ws000001",
                "secondary_id": "abc",
                "status": "operational",
                "last_modification": "2026-01-01T12:00:00",
            }
        ],
    )

    adapter = TwwRelationLookupAdapter(
        schema="tww_od",
    )

    identity = CanonicalObjectIdentity(
        class_id="wastewater_structure",
        attributes={
            "obj_id": "ch000000ws000001",
            "secondary_id": "abc",
        },
    )

    current = adapter.current_object(
        identity,
    )

    assert current is not None

    assert current.identity == identity

    assert current.values == {
        "status": "operational",
        "last_modification": "2026-01-01T12:00:00",
    }

    assert current.last_modification == "2026-01-01T12:00:00"


def test_tww_relation_lookup_adapter_current_object_uses_first_row(
    monkeypatch,
) -> None:
    monkeypatch.setattr(
        DatabaseUtils,
        "fetchall_dict",
        lambda query: [
            {
                "obj_id": "ch000000ws000001",
                "status": "first",
                "last_modification": "2026-01-01T12:00:00",
            },
            {
                "obj_id": "ch000000ws000001",
                "status": "second",
                "last_modification": "2026-01-02T12:00:00",
            },
        ],
    )

    adapter = TwwRelationLookupAdapter(
        schema="tww_od",
    )

    current = adapter.current_object(
        CanonicalObjectIdentity(
            class_id="wastewater_structure",
            attributes={
                "obj_id": "ch000000ws000001",
            },
        )
    )

    assert current is not None

    assert current.values["status"] == "first"

    assert current.last_modification == "2026-01-01T12:00:00"


def test_tww_relation_lookup_adapter_current_object_supports_non_obj_id_identity(
    monkeypatch,
) -> None:
    monkeypatch.setattr(
        DatabaseUtils,
        "fetchall_dict",
        lambda query: [
            {
                "identifier": "external-1",
                "status": "operational",
                "last_modification": "2026-01-01T12:00:00",
            }
        ],
    )

    adapter = TwwRelationLookupAdapter(
        schema="tww_od",
    )

    identity = CanonicalObjectIdentity(
        class_id="wastewater_structure",
        attributes={
            "identifier": "external-1",
        },
    )

    current = adapter.current_object(
        identity,
    )

    assert current is not None

    assert current.identity == identity

    assert current.values == {
        "status": "operational",
        "last_modification": "2026-01-01T12:00:00",
    }

    assert current.last_modification == "2026-01-01T12:00:00"