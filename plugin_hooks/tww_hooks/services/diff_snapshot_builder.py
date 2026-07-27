from __future__ import annotations

from dataclasses import dataclass

from ..models.diff_snapshot import (
    DiffSnapshot,
    SnapshotMetadata,
    SnapshotObject,
)
from ..models.effects import (
    EffectDocument,
)


@dataclass(slots=True)
class DiffSnapshotBuilder:
    """
    Builds diff snapshots from effect documents.
    """

    def build(
        self,
        document: EffectDocument,
    ) -> DiffSnapshot:
        objects: dict[
            tuple[str, tuple],
            SnapshotObject,
        ] = {}

        for effect in document.effects:
            key = (
                effect.identity.class_id,
                tuple(
                    sorted(
                        effect.identity.attributes.items(),
                    )
                ),
            )

            if key not in objects:
                objects[key] = SnapshotObject(
                    identity=effect.identity,
                )

        metadata = SnapshotMetadata(
            created_at=document.created_at,
            source_model=document.source.model,
            source_class_id=document.source.class_id,
            source_object_id=document.source.object_id,
        )

        return DiffSnapshot(
            metadata=metadata,
            objects=tuple(
                objects.values(),
            ),
            effects=document.effects,
        )