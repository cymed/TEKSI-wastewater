# tests/evaluators/test_snapshot_validation_evaluator.py

from datetime import datetime, UTC

from tww_hooks.evaluators.snapshot import (
    SnapshotValidationEvaluator,
)
from tww_hooks.models.canonical_object import (
    CanonicalObject,
    CanonicalObjectIdentity,
)
from tww_hooks.models.diff_snapshot import (
    DiffSnapshot,
    SnapshotMetadata,
    SnapshotObject,
    SnapshotState,
)

def test_snapshot_validation_accepts_current_object() -> None:
    identity = CanonicalObjectIdentity(
        class_id="wastewater_structure",
        attributes={
            "obj_id": "ch000000ws000001",
        },
    )

    last_modification = datetime(
        2025,
        1,
        1,
        tzinfo=UTC,
    )

    snapshot = DiffSnapshot(
        metadata=SnapshotMetadata(
            created_at=datetime.now(
                UTC,
            ),
            source_model="ag64",
            source_class_id="GepKnoten",
            source_object_id="ch123456AG987654",
        ),
        objects=(
            SnapshotObject(
                identity=identity,
                last_modification=last_modification,
            ),
        ),
    )
    
    relation_lookup.objects = {
        identity: CanonicalObject(
            identity=identity,
            last_modification=last_modification,
        ),
    }

    evaluator = SnapshotValidationEvaluator(
        relation_lookup=relation_lookup,
    )

    findings = evaluator.validate(
        snapshot,
    )

    assert findings == ()


def test_snapshot_validation_detects_modified_object() -> None:
    identity = CanonicalObjectIdentity(
        class_id="wastewater_structure",
        attributes={
            "obj_id": "ch000000ws000001",
        },
    )

    snapshot = DiffSnapshot(
        metadata=SnapshotMetadata(
            created_at=datetime.now(
                UTC,
            ),
            source_model="ag64",
            source_class_id="GepKnoten",
            source_object_id="ch123456AG987654",
        ),
        objects=(
            SnapshotObject(
                identity=identity,
                last_modification=datetime(
                    2025,
                    1,
                    1,
                    tzinfo=UTC,
                ),
            ),
        ),
    )

    relation_lookup.objects = {
        identity: CanonicalObject(
            identity=identity,
            last_modification=datetime(
                2025,
                1,
                2,
                tzinfo=UTC,
            ),
        ),
    }

    evaluator = SnapshotValidationEvaluator(
        relation_lookup=relation_lookup,
    )

    findings = evaluator.validate(
        snapshot,
    )

    assert len(
        findings,
    ) == 1

    assert findings[0].identity == identity

    assert (
        findings[0].state
        == SnapshotState.MODIFIED
    )


def test_snapshot_validation_detects_deleted_object(relation_lookup) -> None:
    identity = CanonicalObjectIdentity(
        class_id="wastewater_structure",
        attributes={
            "obj_id": "ch000000ws000001",
        },
    )

    snapshot = DiffSnapshot(
        metadata=SnapshotMetadata(
            created_at=datetime.now(
                UTC,
            ),
            source_model="ag64",
            source_class_id="GepKnoten",
            source_object_id="ch123456AG987654",
        ),
        objects=(
            SnapshotObject(
                identity=identity,
                last_modification=datetime(
                    2025,
                    1,
                    1,
                    tzinfo=UTC,
                ),
            ),
        ),
    )

    evaluator = SnapshotValidationEvaluator(
        relation_lookup
    )

    findings = evaluator.validate(
        snapshot,
    )

    assert len(
        findings,
    ) == 1

    assert findings[0].identity == identity

    assert (
        findings[0].state
        == SnapshotState.DELETED
    )

def test_snapshot_validation_handles_multiple_objects() -> None:
    current_identity = CanonicalObjectIdentity(
        class_id="wastewater_structure",
        attributes={
            "obj_id": "ch000000ws000001",
        },
    )

    modified_identity = CanonicalObjectIdentity(
        class_id="wastewater_structure",
        attributes={
            "obj_id": "ch000000ws000002",
        },
    )

    deleted_identity = CanonicalObjectIdentity(
        class_id="wastewater_structure",
        attributes={
            "obj_id": "ch000000ws000003",
        },
    )

    snapshot = DiffSnapshot(
        metadata=SnapshotMetadata(
            source_model="ag64",
            source_class_id="GepKnoten",
            source_object_id="ch123456AG987654",
        ),
        objects=(
            SnapshotObject(
                identity=current_identity,
                last_modification=1,
            ),
            SnapshotObject(
                identity=modified_identity,
                last_modification=1,
            ),
            SnapshotObject(
                identity=deleted_identity,
                last_modification=1,
            ),
        ),
    )

    lookup = FakeRelationLookupCapability(
        objects={
            current_identity: CanonicalObject(
                identity=current_identity,
                last_modification=1,
            ),
            modified_identity: CanonicalObject(
                identity=modified_identity,
                last_modification=2,
            ),
        },
    )

    evaluator = SnapshotValidationEvaluator(
        relation_lookup=lookup,
    )

    findings = evaluator.validate(
        snapshot,
    )

    assert len(findings) == 2

    states = {
        finding.identity: finding.state
        for finding in findings
    }

    assert (
        states[modified_identity]
        == SnapshotState.MODIFIED
    )

    assert (
        states[deleted_identity]
        == SnapshotState.DELETED
    )