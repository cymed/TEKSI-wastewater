from dataclasses import dataclass

from ..capabilities.relation_lookup import RelationLookupCapability

from ..models.snapshot import DiffSnapshot,SnapshotValidationFinding

@dataclass(slots=True)
class SnapshotValidationEvaluator:

    relation_lookup: RelationLookupCapability

    def validate(
        self,
        snapshot: DiffSnapshot,
    ) -> tuple[
        SnapshotValidationFinding,
        ...
    ]:
        raise NotImplementedError