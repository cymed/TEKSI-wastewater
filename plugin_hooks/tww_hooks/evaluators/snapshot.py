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

