from __future__ import annotations

from dataclasses import dataclass
from typing import Any
from collections.abc import Mapping

from teksi_hooks.capabilities.review import (
    ChangeObjectProvider,
)
from teksi_hooks.models.review import (
    ReviewFeature,
)
from teksi_hooks.models.validation import (
    Change,
)
from teksi_hooks.capabilities.canonical_object import (
    CanonicalGeometryCapability,
)
from teksi_hooks.capabilitites.relation_lookup import (
    RelationLookupCapability,
)


@dataclass(slots=True)
class TwwChangeObjectProvider(
    ChangeObjectProvider,
):
    """
    Plugin-side provider for review feature state.

    The provider supplies old and new feature representations used by
    ChangeReviewExportService when preparing review features.

    Geometry extraction and change analysis are handled by the hook-side
    ChangeReviewExportService.
    """

    live_lookup: RelationLookupCapability
    geometry_capability: CanonicalGeometryCapability
    new_lookup: RelationLookupCapability | None = None

    def old_feature(
        self,
        change: Change,
    ) -> ReviewFeature | None:
        current_object = self.live_lookup.current_object(
            change.identity,
        )

        if current_object is None:
            return None

        return ReviewFeature(
            class_id=change.table_name,
            object_id=change.object_id,
            attributes=self._attribute_values(
                change.table_name,
                current_object.values,
            ),
            geometries=self._geometry_values(
                change.table_name,
                current_object.values,
            ),
        )

    def new_feature(
        self,
        change: Change,
    ) -> ReviewFeature | None:
        """
        Return the proposed feature state represented by the change.
        """

        return ReviewFeature(
            class_id=change.table_name,
            object_id=change.object_id,
            attributes=self._attribute_values(
                change.table_name,
                change.new_values,
            ),
            geometries=self._geometry_values(
                change.table_name,
                change.new_values,
            ),
        )

    def _geometry_values(
        self,
        class_id: str,
        values: Mapping[str, Any],
    ) -> dict[str, Any]:
        return {
            key: value
            for key, value in values.items()
            if self.geometry_capability.is_geometry_attribute(
                class_id,
                key,
            )
        }
    
    def _attribute_values(
        self,
        class_id: str,
        values: Mapping[str, Any],
    ) -> dict[str, Any]:
        return {
            key: value
            for key, value in values.items()
            if not self.geometry_capability.is_geometry_attribute(
                class_id,
                key,
            )
        }