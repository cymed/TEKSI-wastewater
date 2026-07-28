from collections import deque
from dataclasses import dataclass

from ..capabilities.rights import RightsCapability
from ..capabilities.validation import ValidationRegistry
from ..models.validation import (
    ValidationContext,
    ValidationFinding,
    ValidationSeverity,
)


@dataclass(slots=True)
class ValidationEvaluator:
    """
    Evaluates configured attribute and transition validations.
    """

    rights: RightsCapability
    registry: ValidationRegistry

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
        rules = self.rights.try_transition_rules(
            class_id,
            attribute_name,
        )

        if not rules:
            return ()

        if self._is_allowed_transition(
            rules,
            old_value,
            new_value,
        ):
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

    def _is_allowed_transition(
        self,
        rules,
        old_value: str | None,
        new_value: str | None,
    ) -> bool:
        if old_value == new_value:
            return True

        # Direct edge
        if any(
            rule.from_value == old_value
            and rule.to_value == new_value
            for rule in rules
        ):
            return True

        if not self.rights.allow_transitive_transitions:
            return False

        return self._has_path(
            rules,
            old_value,
            new_value,
        )

    def _has_path(
        self,
        rules,
        start: str | None,
        target: str | None,
    ) -> bool:
        graph: dict[
            str,
            set[str],
        ] = {}

        for rule in rules:
            if (
                rule.from_value is None
                or rule.to_value is None
            ):
                continue

            graph.setdefault(
                rule.from_value,
                set(),
            ).add(
                rule.to_value,
            )

        queue = deque(
            [start],
        )

        visited: set[
            str | None
        ] = set()

        while queue:
            current = queue.popleft()

            if current == target:
                return True

            if current in visited:
                continue

            visited.add(
                current,
            )

            for neighbour in graph.get(
                current,
                (),
            ):
                queue.append(
                    neighbour,
                )

        return False

    def validate_attribute(
        self,
        *,
        class_id: str,
        attribute_name: str,
        old_value,
        new_value,
    ) -> tuple[
        ValidationFinding,
        ...
    ]:
        validations = self.rights.try_validations(
            class_id,
            attribute_name,
        )

        if not validations:
            return ()

        findings: list[
            ValidationFinding
        ] = []

        context = ValidationContext(
            attribute_name=attribute_name,
            old_value=old_value,
            new_value=new_value,
        )

        for validation in validations:
            validator = self.registry.validation(
                validation.id,
            )

            findings.extend(
                validator(
                    validation=validation,
                    context=context,
                )
            )

        return tuple(
            findings,
        )