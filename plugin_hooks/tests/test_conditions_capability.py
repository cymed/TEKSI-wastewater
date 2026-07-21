from tww_hooks.capabilities.conditions import (
    ConditionEvaluationContext,
    ConditionsCapability,
)
from tww_hooks.models.conditions import (
    AllOfCondition,
    AnyOfCondition,
    LocalCondition,
)


def test_conditions_capability_evaluates_local_equals() -> None:
    capability = ConditionsCapability()

    condition = LocalCondition(
        attribute="status",
        operator="equals",
        value="operational",
    )

    context = ConditionEvaluationContext(
        local_values={
            "status": "operational",
        },
    )

    assert capability.evaluate(
        condition,
        context,
    )


def test_conditions_capability_evaluates_local_in() -> None:
    capability = ConditionsCapability()

    condition = LocalCondition(
        attribute="status",
        operator="in",
        value=[
            "other.planned",
            "other.calculation_alternative",
        ],
    )

    context = ConditionEvaluationContext(
        local_values={
            "status": "other.planned",
        },
    )

    assert capability.evaluate(
        condition,
        context,
    )


def test_conditions_capability_evaluates_local_is_null() -> None:
    capability = ConditionsCapability()

    condition = LocalCondition(
        attribute="fk_wastewater_structure",
        operator="is_null",
        value=True,
    )

    context = ConditionEvaluationContext(
        local_values={
            "fk_wastewater_structure": None,
        },
    )

    assert capability.evaluate(
        condition,
        context,
    )


def test_conditions_capability_evaluates_any_of() -> None:
    capability = ConditionsCapability()

    condition = AnyOfCondition(
        conditions=(
            LocalCondition(
                attribute="status",
                operator="equals",
                value="inoperative",
            ),
            LocalCondition(
                attribute="status",
                operator="equals",
                value="operational",
            ),
        ),
    )

    context = ConditionEvaluationContext(
        local_values={
            "status": "operational",
        },
    )

    assert capability.evaluate(
        condition,
        context,
    )


def test_conditions_capability_evaluates_all_of() -> None:
    capability = ConditionsCapability()

    condition = AllOfCondition(
        conditions=(
            LocalCondition(
                attribute="status",
                operator="equals",
                value="operational",
            ),
            LocalCondition(
                attribute="fk_provider",
                operator="equals",
                value="ch000000geping01",
            ),
        ),
    )

    context = ConditionEvaluationContext(
        local_values={
            "status": "operational",
            "fk_provider": "ch000000geping01",
        },
    )

    assert capability.evaluate(
        condition,
        context,
    )


def test_conditions_capability_returns_false_for_non_matching_condition() -> None:
    capability = ConditionsCapability()

    condition = LocalCondition(
        attribute="status",
        operator="equals",
        value="operational",
    )

    context = ConditionEvaluationContext(
        local_values={
            "status": "inoperative",
        },
    )

    assert not capability.evaluate(
        condition,
        context,
    )