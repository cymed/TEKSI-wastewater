from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any
from collections.abc import Mapping, Sequence

from ..models.validation import (
    ClassifiedChange,
    ClassifiedChanges,
)

from ..models.review import ReviewFeature
from ..capabilities.review import ChangeFeatureProvider,ReviewArtifactWriter

@dataclass(slots=True)
class ChangeReviewExportService:
    """
    Export classified changes as review artifacts.

    The service creates one artifact per review category:

    - created_objects
    - altered_objects
    - deleted_objects
    - unpermitted_changes

    By default, GeoPackages are expected, but the actual writer is abstracted
    so other storage types can follow later.
    """

    output_dir: Path

    feature_provider: ChangeFeatureProvider

    writer: ReviewArtifactWriter

    def export(
        self,
        classified: ClassifiedChanges,
    ) -> dict[
        str,
        Path,
    ]:
        self.output_dir.mkdir(
            parents=True,
            exist_ok=True,
        )

        artifacts = {}

        artifacts["created_objects"] = self._export_group(
            name="created_objects",
            changes=classified.created_objects,
            mode="created",
        )

        artifacts["altered_objects"] = self._export_group(
            name="altered_objects",
            changes=classified.altered_objects,
            mode="altered",
        )

        artifacts["deleted_objects"] = self._export_group(
            name="deleted_objects",
            changes=classified.deleted_objects,
            mode="deleted",
        )

        artifacts["unpermitted_changes"] = self._export_group(
            name="unpermitted_changes",
            changes=classified.unpermitted_changes,
            mode="unpermitted",
        )

        return artifacts

    def _export_group(
        self,
        *,
        name: str,
        changes: Sequence[
            ClassifiedChange,
        ],
        mode: str,
    ) -> Path:
        path = self.output_dir / f"{name}.gpkg"

        layers = self._features_by_class(
            changes=changes,
            mode=mode,
        )

        self.writer.write(
            path=path,
            layers=layers,
        )

        return path

    def _features_by_class(
            self,
        *,
        changes: Sequence[
            ClassifiedChange,
        ],
        mode: str,
    ) -> dict[
        str,
        list[
            ReviewFeature,
        ],
    ]:
        layers: dict[
            str,
            list[
                ReviewFeature,
            ],
        ] = {}

        for classified_change in changes:
            feature = self._feature_for_classified_change(
                classified_change=classified_change,
                mode=mode,
            )

            if feature is None:
                continue

            layers.setdefault(
                feature.class_id,
                [],
            ).append(
                feature,
            )

        return layers

    def _feature_for_classified_change(
        self,
        *,
        classified_change: ClassifiedChange,
        mode: str,
    ) -> ReviewFeature | None:
        change = classified_change.change

        if mode == "created":
            return self._created_feature(
                classified_change,
            )

        if mode == "altered":
            return self._altered_feature(
                classified_change,
            )

        if mode == "deleted":
            return self._deleted_feature(
                classified_change,
            )

        if mode == "unpermitted":
            return self._unpermitted_feature(
                classified_change,
            )

        raise ValueError(
            f"Unsupported review export mode: {mode}"
        )

    def _created_feature(
        self,
        classified_change: ClassifiedChange,
    ) -> ReviewFeature:
        change = classified_change.change

        new_feature = self.feature_provider.new_feature(
            change,
        )
        attributes = dict(
            change.new_values,
        )

        geometries = (
            dict(
                new_feature.geometries,
            )
            if new_feature is not None
            else self._geometry_values_from_mapping(
                change.new_values,
            )
        )
        self._add_common_review_attributes(
            attributes=attributes,
            classified_change=classified_change,
        )
        self._add_geometry_changed_flags(
            attributes=attributes,
            geometry_attribite_names=geometries.keys(),
            changed_geometry_attribute_names=self._changed_geometry_attributes(
                change,
            ),
        )

        return ReviewFeature(
            class_id=change.table_name,
            object_id=change.object_id,
            attributes=attributes,
            geometries=geometries,
        )

    def _altered_feature(
        self,
        classified_change: ClassifiedChange,
    ) -> ReviewFeature:
        change = classified_change.change

        new_feature = self.feature_provider.new_feature(
            change,
        )

        old_feature = self.feature_provider.old_feature(
            change,
        )

        attributes = {}

        if old_feature is not None:
            attributes.update(
                old_feature.attributes,
            )

        attributes.update(
            change.new_values,
        )

        geometries = {}

        if old_feature is not None:
            geometries.update(
                old_feature.geometries,
            )
        if new_feature is not None:
            geometries.update(
                new_feature.geometries,
            )

        self._add_common_review_attributes(
            attributes=attributes,
            classified_change=classified_change,
        )

        self._add_geometry_changed_flags(
            attributes=attributes,
            geometry_attribute_names=geometries.keys(),
            changed_geometry_attribute_names=self._changed_geometry_attributes(
                change,
            ),
        )
        return ReviewFeature(
            class_id=change.table_name,
            object_id=change.object_id,
            attributes=attributes,
            geometries=geometries,
        )

    def _deleted_feature(
        self,
        classified_change: ClassifiedChange,
    ) -> ReviewFeature:
        change = classified_change.change

        old_feature = self.feature_provider.old_feature(
            change,
        )

        if old_feature is not None:
            attributes = dict(
                old_feature.attributes,
            )
            geometries = dict(
                old_feature.geometries,
            )
        else:
            attributes = dict(
                change.old_values,
            )
            geometries = self._geometry_values_from_mapping(
                change.old_values,
            )

        self._add_common_review_attributes(
            attributes=attributes,
            classified_change=classified_change,
        )

        self._add_geometry_changed_flags(
            attributes=attributes,
            geometry_attribute_names=geometries.keys(),
            changed_geometry_attribute_names=(),
        )

        return ReviewFeature(
            class_id=change.table_name,
            object_id=change.object_id,
            attributes=attributes,
            geometries=geometries,
        )

    def _unpermitted_feature(
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

        unpermitted_attributes = self._unpermitted_attribute_names(
            classified_change,
        )

        attributes = {}

        for attribute_name in unpermitted_attributes:
            if attribute_name in change.new_values:
                attributes[attribute_name] = change.new_values[
                    attribute_name
                ]
                continue

            if attribute_name in change.old_values:
                attributes[attribute_name] = change.old_values[
                    attribute_name
                ]

        geometries = {}

        if old_feature is not None:
            geometries.update(
                old_feature.geometries,
            )
        else:
            geometries.update(
                self._geometry_values_from_mapping(
                    change.old_values,
                )
            )

        if new_feature is not None:
            geometries.update(
                new_feature.geometries,
            )
        else:
            geometries.update(
                self._geometry_values_from_mapping(
                    change.new_values,
                )
            )

        self._add_common_review_attributes(
            attributes=attributes,
            classified_change=classified_change,
        )

        self._add_geometry_changed_flags(
            attributes=attributes,
            geometry_attribute_names=geometries.keys(),
            changed_geometry_attribute_names=self._changed_geometry_attributes(
                change,
            ),
            suffix="_changed_without_permission",
        )

        return ReviewFeature(
            class_id=change.table_name,
            object_id=change.object_id,
            attributes=attributes,
            geometries=geometries,
        )

    def _unpermitted_attribute_names(
        self,
        classified_change: ClassifiedChange,
    ) -> tuple[
        str,
        ...
    ]:
        change = classified_change.change

        attribute_names = {
            finding.attribute_name
            for finding in classified_change.metadata.findings
            if finding.attribute_name is not None
        }

        if attribute_names:
            return tuple(
                sorted(
                    attribute_names,
                )
            )

        return tuple(
            attribute.attribute_name
            for attribute in change.changed_attributes
        )

    def _add_common_review_attributes(
        self,
        *,
        attributes: dict[
            str,
            Any,
        ],
        classified_change: ClassifiedChange,
    ) -> None:
        change = classified_change.change
        metadata = classified_change.metadata

        attributes["_tww_object_id"] = change.object_id
        attributes["_tww_class_id"] = change.table_name
        attributes["_change_operation"] = change.operation.value
        attributes["_change_classification"] = (
            metadata.classification.value
        )
        attributes["_change_permitted"] = metadata.permitted
        attributes["_change_reason"] = metadata.reason
        attributes["_finding_count"] = len(
            metadata.findings,
        )

    def _add_geometry_changed_flags(
        self,
        *,
        attributes: dict[
            str,
            Any,
        ],
        geometry_attribute_names,
        changed_geometry_attribute_names,
        suffix: str = "_changed",
    ) -> None:
        changed_geometry_names = set(
            changed_geometry_attribute_names,
        )

        for geometry_attribute_name in geometry_attribute_names:
            attributes[
                f"{geometry_attribute_name}{suffix}"
            ] = (
                geometry_attribute_name
                in changed_geometry_names
            )

    def _changed_geometry_attributes(
        self,
        change: Change,
    ) -> tuple[
        str,
        ...
    ]:
        changed = []

        for attribute in change.changed_attributes:
            if self._looks_like_geometry_attribute(
                attribute.attribute_name,
            ):
                changed.append(
                    attribute.attribute_name,
                )

        return tuple(
            changed,
        )

    def _geometry_values_from_mapping(
        self,
        values: Mapping[
            str,
            Any,
        ],
    ) -> dict[
        str,
        Any,
    ]:
        return {
            key: value
            for key, value in values.items()
            if self._looks_like_geometry_attribute(
                key,
            )
        }

    def _looks_like_geometry_attribute(
        self,
        attribute_name: str,
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
    def _add_geometry_changed_flags(
        self,
        *,
        attributes: dict[
            str,
            Any,
        ],
        geometry_attribute_names,
        changed_geometry_attribute_names,
        suffix: str = "_changed",
    ) -> None:
        changed_geometry_names = set(
            changed_geometry_attribute_names,
        )

        for geometry_attribute_name in geometry_attribute_names:
            attributes[
                f"{geometry_attribute_name}{suffix}"
            ] = (
                geometry_attribute_name
                in changed_geometry_names
            )

