from dataclasses import dataclass
from typing import Sequence

from tww_hooks.capabilities.relationlookup import RelationLookupCapability, RelatedObject

@dataclass(slots=True)
class FakeRelationLookupCapability(
    RelationLookupCapability,
):

    result: Sequence[RelatedObject]

    def related_objects(
        self,
        **kwargs,
    ) -> Sequence:
        return self.result