from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any
from collections.abc import Mapping, Sequence

from ..models.validation import (
    Change,
    ChangeOperation,
    ClassifiedChange,
    ClassifiedChanges,
)

from ..models.review import (
    ReviewFeature,
)

from ..capabilities.review import (
    ChangeFeatureProvider,
)


@dataclass(slots=True)
class ChangeReviewExportService:
    """
    Prepare classified changes as review features.

    This service is hook-side and storage-format independent.

    It does not:

    - write GeoPackages;
    - write PostgreSQL rows;
    - access QGIS;
    - access DatabaseUtils;
    - infer geometry attributes from names.

    It converts ClassifiedChanges into ReviewFeature objects grouped by
    canonical class. Plugin-side services can then persist those features into
    tww_diff or another storage backend.

    Geometry attributes are metadata-driven through
    geometry_attribute_names_by_class.
    """

    feature_provider: ChangeFeatureProvider

    geometry_attribute_names_by_class: Mapping[
        str,
        Sequence[
            str,
        ],
    ] = field(
        default_factory=dict,
    )

    def export(
        self,
        classified: ClassifiedChanges,
    ) -> dict[
        str,
        list[
            ReviewFeature,
        ],
    ]:
        """
        Build review features grouped by canonical class.
        """

        features_by_class: dict[
            str,
            list[
                ReviewFeature,
            ],
        ] = {}

        for classified_change in self._classified_changes(
            classified,
        ):
            feature = self._feature_for_classified_change(
                classified_change,
            )

            features_by_class.setdefault(
                feature.class_id,
                [],
            ).append(
                feature,
            )

        return features_by_class

    def _classified_changes(
        self,
        classified: ClassifiedChanges,
    ) -> tuple[
        ClassifiedChange,
        ...
    ]:
        return (
            *classified.created_objects,
            *classified.altered_objects,
            *classified.deleted_objects,
            *classified.unpermitted_changes,
        )

    def _feature_for_classified_change(
        self,
        classified_change: ClassifiedChange,
    ) -> ReviewFeature:
        change = classified_change.change

        old_feature = self.feature_provider.old_feature(
            change,
        )

        new_feature = self.feature_provider.new_feature(
            change,
        )

        attributes = self._review_attributes(
            classified_change=classified_change,
        )

        geometries = self._review_geometries(
            change=change,
            old_feature=old_feature,
            new_feature=new_feature,
        )

        self._add_geometry_changed_flags(
            change=change,
            attributes=attributes,
        )

        return ReviewFeature(
            class_id=change.table_name,
            object_id=change.object_id,
            attributes=attributes,
            geometries=geometries,
        )

    def _review_attributes(
        self,
        classified_change: ClassifiedChange,
    ) -> dict[
        str,
        Any,
    ]:
        change = classified_change.change

        return {
            "obj_id": change.object_id,
            "is_created": self._is_created(
                change,
            ),
            "is_altered": self._is_altered(
                change,
            ),
            "is_deleted": self._is_deleted(
                change,
            ),
            "import_values": self._import_values(
                change,
            ),
            "canonical_values": self._canonical_values(
                change,
            ),
            "changed_attributes": self._changed_attributes_payload(
                change,
            ),
            "unpermitted_values": self._unpermitted_values(
                classified_change,
            ),
            "permission_findings": tuple(
                classified_change.metadata.permission_findings,
            ),
            "validation_findings": tuple(
                classified_change.metadata.validation_findings,
            ),
        }

    def _import_values(
        self,
        change: Change,
    ) -> dict[
        str,
        Any,
    ]:
        if self._is_deleted(
            change,
        ):
            return {}

        return dict(
            change.new_values,
        )

    def _canonical_values(
        self,
        change: Change,
    ) -> dict[
        str,
        Any,
    ]:
        if self._is_created(
            change,
        ):
            return dict(
                change.new_values,
            )

        if self._is_deleted(
            change,
        ):
            return dict(
                change.old_values,
            )

        values = dict(
            change.old_values,
        )

        values.update(
            change.new_values,
        )

        return values

    def _unpermitted_values(
        self,
        classified_change: ClassifiedChange,
    ) -> dict[
        str,
        Any,
    ]:
        change = classified_change.change

        attribute_names = {
            finding.attribute_name
            for finding in classified_change.metadata.findings
            if finding.attribute_name is not None
        }

        if not attribute_names:
            return {}

        values = {}

        for attribute_name in attribute_names:
            if attribute_name in change.new_values:
                values[attribute_name] = change.new_values[
                    attribute_name
                ]
                continue

            if attribute_name in change.old_values:
                values[attribute_name] = change.old_values[
                    attribute_name
                ]

        return values

    def _changed_attributes_payload(
        self,
        change: Change,
    ) -> tuple[
        dict[
            str,
            Any,
        ],
        ...
    ]:
        payload = []

        for attribute in change.changed_attributes:
            attribute_name = attribute.attribute_name

            payload.append(
                {
                    "attribute_name": attribute_name,
                    "old_value": change.old_values.get(
                        attribute_name,
                    ),
                    "new_value": change.new_values.get(
                        attribute_name,
                    ),
                }
            )

        return tuple(
            payload,
        )

    def _review_geometries(
        self,
        *,
        change: Change,
        old_feature: ReviewFeature | None,
        new_feature: ReviewFeature | None,
    ) -> dict[
        str,
        Any,
    ]:
        if self._is_created(
            change,
        ):
            return self._new_geometries(
                change=change,
                new_feature=new_feature,
            )

        if self._is_deleted(
            change,
        ):
            return self._old_geometries(
                change=change,
                old_feature=old_feature,
            )

        geometries = {}

        geometries.update(
            self._old_geometries(
                change=change,
                old_feature=old_feature,
            )
        )

        geometries.update(
            self._new_geometries(
                change=change,
                new_feature=new_feature,
            )
        )

        return geometries

    def _old_geometries(
        self,
        *,
        change: Change,
        old_feature: ReviewFeature | None,
    ) -> dict[
        str,
        Any,
    ]:
        if old_feature is not None:
            return dict(
                old_feature.geometries,
            )

        return self._geometry_values_from_mapping(
            class_id=change.table_name,
            values=change.old_values,
        )

    def _new_geometries(
        self,
        *,
        change: Change,
        new_feature: ReviewFeature | None,
    ) -> dict[
        str,
        Any,
    ]:
        if new_feature is not None:
            return dict(
                new_feature.geometries,
            )

        return self._geometry_values_from_mapping(
            class_id=change.table_name,
            values=change.new_values,
        )

    def _add_geometry_changed_flags(
        self,
        *,
        change: Change,
        attributes: dict[
            str,
            Any,
        ],
    ) -> None:
        changed_geometry_names = set(
            self._changed_geometry_attributes(
                change,
            )
        )

        for geometry_attribute_name in self._geometry_attribute_names(
            change.table_name,
        ):
            attributes[
                f"{geometry_attribute_name}_changed"
            ] = (
                geometry_attribute_name
                in changed_geometry_names
            )

            attributes[
                f"{geometry_attribute_name}_changed_without_permission"
            ] = (
                geometry_attribute_name
                in changed_geometry_names
                and bool(
                    attributes["permission_findings"]
                    or attributes["validation_findings"]
                )
            )

    def _changed_geometry_attributes(
        self,
        change: Change,
    ) -> tuple[
        str,
        ...
    ]:
        geometry_attribute_names = set(
            self._geometry_attribute_names(
                change.table_name,
            )
        )

        return tuple(
            attribute.attribute_name
            for attribute in change.changed_attributes
            if attribute.attribute_name in geometry_attribute_names
        )

    def _geometry_values_from_mapping(
        self,
        *,
        class_id: str,
        values: Mapping[
            str,
            Any,
        ],
    ) -> dict[
        str,
        Any,
    ]:
        geometry_attribute_names = set(
            self._geometry_attribute_names(
                class_id,
            )
        )

        return {
            key: value
            for key, value in values.items()
            if key in geometry_attribute_names
        }

    def _geometry_attribute_names(
        self,
        class_id: str,
    ) -> tuple[
        str,
        ...
    ]:
        return tuple(
            self.geometry_attribute_names_by_class.get(
                class_id,
                (),
            )
        )

    def _is_created(
        self,
        change: Change,
    ) -> bool:
        return (
            change.operation
            == ChangeOperation.INSERT
        )

    def _is_altered(
        self,
        change: Change,
    ) -> bool:
        return (
            change.operation
            == ChangeOperation.UPDATE
        )

    def _is_deleted(
        self,
        change: Change,
    ) -> bool:
        return (
            change.operation
            == ChangeOperation.DELETE
        )