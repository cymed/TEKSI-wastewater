from __future__ import annotations

from dataclasses import dataclass

from ..capabilities.relation_lookup import (
    RelationLookupCapability,
)
from ..models.diff_snapshot import (
    DiffSnapshot,
    SnapshotState,
    SnapshotValidationFinding,
)


@dataclass(slots=True)
class SnapshotValidationEvaluator:
    """
    Validates whether snapshot objects are still current.

    A snapshot may be reviewed long after it was generated. Validation
    therefore compares the stored last_modification value against the
    current database state.
    """

    relation_lookup: RelationLookupCapability

    def validate(
        self,
        snapshot: DiffSnapshot,
    ) -> tuple[
        SnapshotValidationFinding,
        ...
    ]:
        findings: list[
            SnapshotValidationFinding
        ] = []

        for snapshot_object in snapshot.objects:
            if snapshot_object.last_modification is None:
                raise ValueError("Snapshot object is missing last_modification.")
            
            current = self.relation_lookup.current_object(
                snapshot_object.identity,
            )

            if current is None:
                findings.append(
                    SnapshotValidationFinding(
                        identity=snapshot_object.identity,
                        state=SnapshotState.DELETED,
                    )
                )
                continue

            if (
                snapshot_object.last_modification
                != current.last_modification
            ):
                findings.append(
                    SnapshotValidationFinding(
                        identity=snapshot_object.identity,
                        state=SnapshotState.MODIFIED,
                    )
                )

        return tuple(
            findings,
        )

def test_rights_evaluator_returns_false_without_subclass_mapping(
    resolved_rights,
    resolved_providers,
) -> None:
    evaluator = RightsEvaluator(
        rights=RightsCapability(
            classes=resolved_rights,
        ),
        provider=ResolvedProviderCapability(
            provider=resolved_providers[
                Standardoid("ch000000geping01")
            ],
        ),
        conditions=ConditionsCapability(),
        derived_rights=DerivedRightsCapability(
            classes={},
        ),
        relation_lookup=FakeRelationLookupCapability(
            CanonicalDerivedRights(),
        ),
        subclass_rights=SubclassRightsCapability(
            parent_classes={},
        ),
    )

    context = RightsEvaluationContext(
        dataowner_oid=Standardoid(
            "ch000000awgde001",
        ),
        provider_oid=Standardoid(
            "ch000000geping01",
        ),
        operation=ChangeOperation.UPDATE,
    )

    assert not evaluator._can_update_via_subclass_rights(
        "maintenance_event",
        context,
    )