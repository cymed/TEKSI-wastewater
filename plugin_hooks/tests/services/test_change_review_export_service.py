from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import pytest

from tww_hooks.models.review import (
    ReviewFeature,
)
from tww_hooks.models.validation import (
    Change,
    ChangeClassification,
    ChangeClassificationMetadata,
    ChangeOperation,
    ClassifiedChange,
    ClassifiedChanges,
    ValidationFinding,
)
from tww_hooks.services.change_review_export import (
    ChangeReviewExportService,
)


@dataclass(slots=True)
class FakeChangeFeatureProvider:
    old_features: dict[
        tuple[
            str,
            str,
        ],
        ReviewFeature,
    ]

    new_features: dict[
        tuple[
            str,
            str,
        ],
        ReviewFeature,
    ]

    def old_feature(
        self,
        change: Change,
    ) -> ReviewFeature | None:
        return self.old_features.get(
            (
                change.table_name,
                change.object_id,
            )
        )

    def new_feature(
        self,
        change: Change,
    ) -> ReviewFeature | None:
        return self.new_features.get(
            (
                change.table_name,
                change.object_id,
            )
        )


def test_change_review_export_service_groups_features_by_class() -> None:
    change = Change(
        table_name="reach",
        object_id="ch000000re000001",
        operation=ChangeOperation.UPDATE,
        old_values={
            "obj_id": "ch000000re000001",
            "status": "old",
        },
        new_values={
            "status": "new",
        },
    )

    classified = ClassifiedChanges(
        altered_objects=[
            ClassifiedChange(
                change=change,
                metadata=ChangeClassificationMetadata(
                    classification=ChangeClassification.ALTERED_OBJECT,
                    permitted=True,
                ),
            )
        ],
    )

    service = ChangeReviewExportService(
        feature_provider=FakeChangeFeatureProvider(
            old_features={},
            new_features={},
        ),
        geometry_attribute_names_by_class={},
    )

    features_by_class = service.export(
        classified,
    )

    assert set(
        features_by_class,
    ) == {
        "reach",
    }

    assert len(
        features_by_class["reach"],
    ) == 1

    feature = features_by_class["reach"][0]

    assert feature.class_id == "reach"
    assert feature.object_id == "ch000000re000001"

    assert feature.attributes["obj_id"] == "ch000000re000001"
    assert feature.attributes["is_created"] is False
    assert feature.attributes["is_altered"] is True
    assert feature.attributes["is_deleted"] is False

    assert feature.attributes["import_values"] == {
        "status": "new",
    }

    assert feature.attributes["canonical_values"] == {
        "obj_id": "ch000000re000001",
        "status": "new",
    }

    assert feature.attributes["unpermitted_values"] == {}
    assert feature.attributes["permission_findings"] == ()
    assert feature.attributes["validation_findings"] == ()


def test_change_review_export_service_created_feature_uses_import_values() -> None:
    change = Change(
        table_name="wastewater_structure",
        object_id="ch000000ws000001",
        operation=ChangeOperation.INSERT,
        old_values={},
        new_values={
            "obj_id": "ch000000ws000001",
            "status": "created",
        },
    )

    classified = ClassifiedChanges(
        created_objects=[
            ClassifiedChange(
                change=change,
                metadata=ChangeClassificationMetadata(
                    classification=ChangeClassification.CREATED_OBJECT,
                    permitted=True,
                ),
            )
        ],
    )

    service = ChangeReviewExportService(
        feature_provider=FakeChangeFeatureProvider(
            old_features={},
            new_features={},
        ),
        geometry_attribute_names_by_class={},
    )

    features_by_class = service.export(
        classified,
    )

    feature = features_by_class["wastewater_structure"][0]

    assert feature.attributes["is_created"] is True
    assert feature.attributes["is_altered"] is False
    assert feature.attributes["is_deleted"] is False

    assert feature.attributes["import_values"] == {
        "obj_id": "ch000000ws000001",
        "status": "created",
    }

    assert feature.attributes["canonical_values"] == {
        "obj_id": "ch000000ws000001",
        "status": "created",
    }


def test_change_review_export_service_deleted_feature_uses_old_values() -> None:
    change = Change(
        table_name="reach",
        object_id="ch000000re000002",
        operation=ChangeOperation.DELETE,
        old_values={
            "obj_id": "ch000000re000002",
            "status": "deleted",
        },
        new_values={},
    )

    classified = ClassifiedChanges(
        deleted_objects=[
            ClassifiedChange(
                change=change,
                metadata=ChangeClassificationMetadata(
                    classification=ChangeClassification.DELETED_OBJECT,
                    permitted=True,
                ),
            )
        ],
    )

    service = ChangeReviewExportService(
        feature_provider=FakeChangeFeatureProvider(
            old_features={},
            new_features={},
        ),
        geometry_attribute_names_by_class={},
    )

    features_by_class = service.export(
        classified,
    )

    feature = features_by_class["reach"][0]

    assert feature.attributes["is_created"] is False
    assert feature.attributes["is_altered"] is False
    assert feature.attributes["is_deleted"] is True

    assert feature.attributes["import_values"] == {}

    assert feature.attributes["canonical_values"] == {
        "obj_id": "ch000000re000002",
        "status": "deleted",
    }


def test_change_review_export_service_uses_metadata_driven_geometry_attributes() -> None:
    change = Change(
        table_name="reach",
        object_id="ch000000re000003",
        operation=ChangeOperation.UPDATE,
        old_values={
            "obj_id": "ch000000re000003",
            "progression_geometry": "LINESTRING(0 0, 1 1)",
            "status": "old",
        },
        new_values={
            "progression_geometry": "LINESTRING(0 0, 2 2)",
            "status": "new",
        },
    )

    classified = ClassifiedChanges(
        altered_objects=[
            ClassifiedChange(
                change=change,
                metadata=ChangeClassificationMetadata(
                    classification=ChangeClassification.ALTERED_OBJECT,
                    permitted=True,
                ),
            )
        ],
    )

    service = ChangeReviewExportService(
        feature_provider=FakeChangeFeatureProvider(
            old_features={},
            new_features={},
        ),
        geometry_attribute_names_by_class={
            "reach": (
                "progression_geometry",
            ),
        },
    )

    features_by_class = service.export(
        classified,
    )

    feature = features_by_class["reach"][0]

    assert feature.geometries == {
        "progression_geometry": "LINESTRING(0 0, 2 2)",
    }

    assert feature.attributes["progression_geometry_changed"] is True
    assert (
        feature.attributes[
            "progression_geometry_changed_without_permission"
        ]
        is False
    )


def test_change_review_export_service_ignores_geometry_like_names_not_in_metadata() -> None:
    change = Change(
        table_name="reach",
        object_id="ch000000re000004",
        operation=ChangeOperation.UPDATE,
        old_values={
            "obj_id": "ch000000re000004",
            "geom_fake": "not a real geometry attribute",
        },
        new_values={
            "geom_fake": "still not a real geometry attribute",
        },
    )

    classified = ClassifiedChanges(
        altered_objects=[
            ClassifiedChange(
                change=change,
                metadata=ChangeClassificationMetadata(
                    classification=ChangeClassification.ALTERED_OBJECT,
                    permitted=True,
                ),
            )
        ],
    )

    service = ChangeReviewExportService(
        feature_provider=FakeChangeFeatureProvider(
            old_features={},
            new_features={},
        ),
        geometry_attribute_names_by_class={
            "reach": (),
        },
    )

    features_by_class = service.export(
        classified,
    )

    feature = features_by_class["reach"][0]

    assert feature.geometries == {}
    assert "geom_fake_changed" not in feature.attributes


def test_change_review_export_service_marks_rejected_geometry_change() -> None:
    finding = ValidationFinding(
        code="invalid_geometry",
        severity="error",
        message="Geometry is invalid.",
        attribute_name="progression_geometry",
    )

    change = Change(
        table_name="reach",
        object_id="ch000000re000005",
        operation=ChangeOperation.UPDATE,
        old_values={
            "obj_id": "ch000000re000005",
            "progression_geometry": "LINESTRING(0 0, 1 1)",
        },
        new_values={
            "progression_geometry": "LINESTRING(0 0, 2 2)",
        },
    )

    classified = ClassifiedChanges(
        unpermitted_changes=[
            ClassifiedChange(
                change=change,
                metadata=ChangeClassificationMetadata(
                    classification=ChangeClassification.UNPERMITTED_CHANGE,
                    permitted=True,
                    validation_findings=(
                        finding,
                    ),
                ),
            )
        ],
    )

    service = ChangeReviewExportService(
        feature_provider=FakeChangeFeatureProvider(
            old_features={},
            new_features={},
        ),
        geometry_attribute_names_by_class={
            "reach": (
                "progression_geometry",
            ),
        },
    )

    features_by_class = service.export(
        classified,
    )

    feature = features_by_class["reach"][0]

    assert feature.attributes["unpermitted_values"] == {
        "progression_geometry": "LINESTRING(0 0, 2 2)",
    }

    assert feature.attributes["progression_geometry_changed"] is True
    assert (
        feature.attributes[
            "progression_geometry_changed_without_permission"
        ]
        is True
    )

    assert feature.attributes["validation_findings"] == (
        finding,
    )


def test_change_review_export_service_prefers_provider_features_for_geometries() -> None:
    change = Change(
        table_name="reach",
        object_id="ch000000re000006",
        operation=ChangeOperation.UPDATE,
        old_values={
            "obj_id": "ch000000re000006",
            "progression_geometry": "LINESTRING(0 0, 1 1)",
        },
        new_values={
            "progression_geometry": "LINESTRING(0 0, 2 2)",
        },
    )

    old_feature = ReviewFeature(
        class_id="reach",
        object_id="ch000000re000006",
        attributes={
            "obj_id": "ch000000re000006",
        },
        geometries={
            "progression_geometry": "LINESTRING(10 10, 11 11)",
        },
    )

    new_feature = ReviewFeature(
        class_id="reach",
        object_id="ch000000re000006",
        attributes={
            "obj_id": "ch000000re000006",
        },
        geometries={
            "progression_geometry": "LINESTRING(20 20, 21 21)",
        },
    )

    classified = ClassifiedChanges(
        altered_objects=[
            ClassifiedChange(
                change=change,
                metadata=ChangeClassificationMetadata(
                    classification=ChangeClassification.ALTERED_OBJECT,
                    permitted=True,
                ),
            )
        ],
    )

    service = ChangeReviewExportService(
        feature_provider=FakeChangeFeatureProvider(
            old_features={
                (
                    "reach",
                    "ch000000re000006",
                ): old_feature,
            },
            new_features={
                (
                    "reach",
                    "ch000000re000006",
                ): new_feature,
            },
        ),
        geometry_attribute_names_by_class={
            "reach": (
                "progression_geometry",
            ),
        },
    )

    features_by_class = service.export(
        classified,
    )

    feature = features_by_class["reach"][0]

    assert feature.geometries == {
        "progression_geometry": "LINESTRING(20 20, 21 21)",
    }