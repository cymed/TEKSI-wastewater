from __future__ import annotations

from dataclasses import dataclass

from tww_hooks.capabilities.review import (
    ChangeFeatureProvider,
)
from tww_hooks.models.review import (
    ReviewFeature,
)
from tww_hooks.models.validation import (
    Change,
)

from ..adapters.tww_relation_lookup_adapter import (
    TwwRelationLookupAdapter,
)


@dataclass(slots=True)
class TwwChangeFeatureProvider(
    ChangeFeatureProvider,
):
    """
    Plugin-side provider for old and new review features.

    This adapter translates canonical Change objects into ReviewFeature
    instances by reading from TEKSI Wastewater schemas or future projected
    feature stores.
    """

    live_lookup: TwwRelationLookupAdapter

    new_lookup: TwwRelationLookupAdapter | None = None

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
            attributes=dict(
                current_object.values,
            ),
            geometries=self._geometry_values(
                current_object.values,
            ),
        )

    def new_feature(
        self,
        change: Change,
    ) -> ReviewFeature | None:
        attributes = {

            change.old_values,
            change.new_values,
        }

        return ReviewFeature(
            class_id=change.table_name,
            object_id=change.object_id,
            attributes=attributes,
            geometries=self._geometry_values(
                attributes,
            ),
        )

    def   _geometry_values(
        self,
        values,
    ):
        return {
            key: value
            for key, value in values.items  
            if self._looks_like_geometry_attribute(
                key,
            )
        }

    def _looks_like_geometry_attribute(
            self,
            attribute_name  : str,
    ) -> bool:
        lowered = attribute_name.lower()

        return (
            lowered == "geometry"
            or lowered == "geom"
            or lowered.startswith(
                "geom_",
            )
            or lowered.endswith(
                "_geometry",
            )
            or lowered.endswith(
                "_geom",
            )
        )