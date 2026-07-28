import pytest

from tww_hooks.models.canonical_object import (
    CanonicalObject,
    CanonicalObjectIdentity,
)
from tww_hooks.models.effects import (
    UpdateAttributeEffect,
)
from tww_hooks.models.validation import (
    ChangeOperation,
)
from tww_hooks.services.change_builder import (
    ChangeBuilder,
)


@pytest.fixture
def wastewater_structure() -> CanonicalObject:
    return CanonicalObject(
        identity=CanonicalObjectIdentity(
            class_id="wastewater_structure",
            attributes={
                "obj_id": "ch987654WS123456",
            },
        ),
        values={
            "status": "other.planned",
            "remark": "",
            "status_survey_year": 2020,
            "fk_provider": "ch000000geping01",
        },
    )


def test_change_builder_builds_insert() -> None:
    builder = ChangeBuilder()

    effect = UpdateAttributeEffect(
        identity=CanonicalObjectIdentity(
            class_id="wastewater_structure",
            attributes={
                "obj_id": "ch987654WS123456",
            },
        ),
        tww_attribute_id="status",
        value="operational",
    )

    change = builder.build(
        current_object=None,
        effects=(effect,),
    )

    assert (
        change.operation
        == ChangeOperation.INSERT
    )

    assert change.old_values == {}

    assert change.new_values == {
        "status": "operational",
    }


def test_change_builder_builds_update(
    wastewater_structure,
) -> None:
    builder = ChangeBuilder()

    change = builder.build(
        current_object=wastewater_structure,
        effects=(
            UpdateAttributeEffect(
                identity=wastewater_structure.identity,
                tww_attribute_id="status",
                value="operational",
            ),
            UpdateAttributeEffect(
                identity=wastewater_structure.identity,
                tww_attribute_id="remark",
                value="Survey completed",
            ),
            UpdateAttributeEffect(
                identity=wastewater_structure.identity,
                tww_attribute_id="status_survey_year",
                value=2024,
            ),
        ),
    )

    assert (
        change.operation
        == ChangeOperation.UPDATE
    )

    assert change.old_values == {
        "status": "other.planned",
        "remark": "",
        "status_survey_year": 2020,
        "fk_provider": "ch000000geping01",
    }

    assert change.new_values == {
        "status": "operational",
        "remark": "Survey completed",
        "status_survey_year": 2024,
        "fk_provider": "ch000000geping01",
    }

    assert len(
        change.changed_attributes,
    ) == 3


def test_change_builder_preserves_unchanged_attributes(
    wastewater_structure,
) -> None:
    builder = ChangeBuilder()

    change = builder.build(
        current_object=wastewater_structure,
        effects=(
            UpdateAttributeEffect(
                identity=wastewater_structure.identity,
                tww_attribute_id="status",
                value="operational",
            ),
        ),
    )

    assert (
        change.new_values["fk_provider"]
        == "ch000000geping01"
    )

    changed_attributes = {
        attribute_change.attribute_name
        for attribute_change in change.changed_attributes
    }

    assert "status" in changed_attributes

    assert (
        "fk_provider"
        not in changed_attributes
    )

    assert (
        "remark"
        not in changed_attributes
    )

    assert (
        "status_survey_year"
        not in changed_attributes
    )


def test_change_builder_changed_attributes_contain_expected_values(
    wastewater_structure,
) -> None:
    builder = ChangeBuilder()

    change = builder.build(
        current_object=wastewater_structure,
        effects=(
            UpdateAttributeEffect(
                identity=wastewater_structure.identity,
                tww_attribute_id="status",
                value="operational",
            ),
        ),
    )

    assert len(
        change.changed_attributes,
    ) == 1

    changed = next(
        iter(
            change.changed_attributes,
        )
    )

    assert (
        changed.attribute_name
        == "status"
    )

    assert (
        changed.old_value
        == "other.planned"
    )

    assert (
        changed.new_value
        == "operational"
    )


def test_change_builder_rejects_empty_effects() -> None:
    builder = ChangeBuilder()

    with pytest.raises(
        ValueError,
    ):
        builder.build(
            current_object=None,
            effects=(),
        )