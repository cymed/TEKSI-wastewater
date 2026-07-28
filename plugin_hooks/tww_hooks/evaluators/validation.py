from dataclasses import dataclass

from ..capabilities.rights import RightsCapability
from ..models.validation import (
    ValidationFinding,
    ValidationSeverity
)


@dataclass(slots=True)
class ValidationEvaluator:
    """
    Evaluates configured attribute and transition validations.
    """

    rights: RightsCapability

def validate_transition(
    self,
    *,
    class_id: str,
    attribute_name: str,
    old_value: str | None,
    new_value: str | None,
) -> tuple[
    ValidationFinding,
    ...
]:
    rules = self.rights.transitions(
        class_id,
        attribute_name,
    )

    if not rules:
        return ()

    allowed = any(
        rule.from_value == old_value
        and rule.to_value == new_value
        for transition in rules
        for rule in transition.ruleset
    )

    if allowed:
        return ()

    return (
        ValidationFinding(
            code="invalid_transition",
            severity=ValidationSeverity.ERROR,
            message=(
                f"Transition "
                f"{old_value!r} -> {new_value!r} "
                f"is not allowed."
            ),
            attribute_name=attribute_name,
        ),
    )