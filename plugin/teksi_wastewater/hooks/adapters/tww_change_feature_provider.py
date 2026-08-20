from __future__ import annotations

from dataclasses import dataclass

from teksi_hooks.capabilities.review import (
    ChangeObjectProvider,
)
from teksi_hooks.capabilities.relation_lookup import (
    RelationLookupCapability,
)
from teksi_hooks.models.canonical_object import (
    CanonicalObject,
)
from teksi_hooks.models.validation import (
    Change,
)


@dataclass(slots=True)
class TwwChangeObjectProvider(
    ChangeObjectProvider,
):
    """
    Plugin-side provider for canonical object state used during review export.

    The provider supplies old and new canonical objects. Transformation into
    ReviewFeature instances is handled by the hook-side
    ChangeReviewExportService.
    """

    live_lookup: RelationLookupCapability

    new_lookup: RelationLookupCapability | None = None

    def old_object(
        self,
        change: Change,
    ) -> CanonicalObject | None:
        """
        Return the current persisted canonical object.
        """

        return self.live_lookup.current_object(
            change.identity,
        )

    def new_object(
        self,
        change: Change,
    ) -> CanonicalObject | None:
        """
        Return the proposed canonical object represented by the change.
        """

        if self.new_lookup is not None:
            current = self.new_lookup.current_object(
                change.identity,
            )

            if current is not None:
                return current

        return CanonicalObject(
            identity=change.identity,
            values=dict(
                change.new_values,
            ),
        )