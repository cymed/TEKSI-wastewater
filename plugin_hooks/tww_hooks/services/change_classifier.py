from __future__ import annotations

from dataclasses import dataclass, replace
from collections.abc import Mapping, Sequence

from ..models.rights import (
    RightsEvaluationContext,
)
from ..models.validation import (
    ValidationFinding,
    ChangeClassification,
    ChangeClassificationMetadata,
    ClassifiedChange,
    ClassifiedChanges,
    Change,
    ChangeOperation,
)
from ..evaluators.rights import (
    RightsEvaluator,
)


ChangeKey = tuple[
    str,
    str,
    ChangeOperation,
]


@dataclass(slots=True)
class ChangeClassifier:
    """
    Classify changes into review/export groups.

    The classifier is framework-side because it depends only on hook models
    and rights evaluation.

    Classification rules:

    - INSERT + permitted -> created_objects
    - UPDATE + permitted -> altered_objects
    - DELETE + permitted -> deleted_objects
    - rights denied -> unpermitted_changes
    - validation error -> unpermitted_changes
    - unknown operation -> unpermitted_changes

    Validation warnings and info findings stay attached to the change but do
    not make it unpermitted.
    """

    rights_evaluator: RightsEvaluator

    def classify(
        self,
        changes: Sequence[
            Change,
        ],
        context: RightsEvaluationContext,
        findings_by_change_key: Mapping[
            ChangeKey,
            tuple[
                ValidationFinding,
                ...
            ],
        ] | None = None,
        metadata: dict[
            str,
            str,
        ] | None = None,
    ) -> ClassifiedChanges:
        """
        Classify a sequence of changes.

        Parameters
        ----------
        changes:
            Changes to classify.

        context:
            Base rights evaluation context. Operation, old_values and
            new_values are replaced per change before rights evaluation.

        findings_by_change_key:
            Optional validation findings keyed by
            (table_name, object_id, operation).

        metadata:
            Optional workflow-level metadata copied into the result.
        """

        findings_by_change_key = findings_by_change_key or {}

        result = ClassifiedChanges(
            metadata=metadata or {},
        )

        for change in changes:
            findings = findings_by_change_key.get(
                self.change_key(
                    change,
                ),
                (),
            )

            classified_change = self._classify_change(
                change=change,
                base_context=context,
                findings=findings,
            )

            result.add(
                classified_change,
            )

        return result

    def _classify_change(
        self,
        change: Change,
        base_context: RightsEvaluationContext,
        findings: tuple[
            ValidationFinding,
            ...
        ],
    ) -> ClassifiedChange:
        highest_severity = self._highest_severity(
            findings,
        )

        if self._has_error_finding(
            findings,
        ):
            return ClassifiedChange(
                change=change,
                metadata=ChangeClassificationMetadata(
                    classification=ChangeClassification.UNPERMITTED_CHANGE,
                    permitted=False,
                    severity=highest_severity,
                    reason=(
                        "Change has validation errors."
                    ),
                    validation_findings=findings,
                ),
            )

        context = self._context_for_change(
            base_context=base_context,
            change=change,
        )

        if not self._is_permitted(
            change=change,
            context=context,
        ):
            return ClassifiedChange(
                change=change,
                metadata=ChangeClassificationMetadata(
                    classification=ChangeClassification.UNPERMITTED_CHANGE,
                    permitted=False,
                    severity=highest_severity,
                    reason=(
                        "Change is not permitted by rights evaluation."
                    ),
                    validation_findings=findings,
                ),
            )

        classification = self._classification_for_operation(
            change.operation,
        )

        if classification == ChangeClassification.UNPERMITTED_CHANGE:
            return ClassifiedChange(
                change=change,
                metadata=ChangeClassificationMetadata(
                    classification=classification,
                    permitted=False,
                    severity=highest_severity,
                    reason=(
                        f"Unsupported change operation: {change.operation!r}."
                    ),
                    validation_findings=findings,
                ),
            )

        return ClassifiedChange(
            change=change,
            metadata=ChangeClassificationMetadata(
                classification=classification,
                permitted=True,
                severity=highest_severity,
                reason=None,
                validation_findings=findings,
            ),
        )

    def _context_for_change(
        self,
        base_context: RightsEvaluationContext,
        change: Change,
    ) -> RightsEvaluationContext:
        """
        Create a rights evaluation context for one change.
        """

        return replace(
            base_context,
            operation=change.operation,
            old_values=change.old_values,
            new_values=change.new_values,
        )

    def _is_permitted(
        self,
        change: Change,
        context: RightsEvaluationContext,
    ) -> bool:
        if change.operation == ChangeOperation.INSERT:
            return self.rights_evaluator.can_create(
                change.table_name,
                context,
            )

        if change.operation == ChangeOperation.UPDATE:
            return self.rights_evaluator.can_update(
                change.table_name,
                context,
            )

        if change.operation == ChangeOperation.DELETE:
            return self.rights_evaluator.can_delete(
                change.table_name,
                context,
            )

        return False

    def _classification_for_operation(
        self,
        operation: ChangeOperation,
    ) -> ChangeClassification:
        if operation == ChangeOperation.INSERT:
            return ChangeClassification.CREATED_OBJECT

        if operation == ChangeOperation.UPDATE:
            return ChangeClassification.ALTERED_OBJECT

        if operation == ChangeOperation.DELETE:
            return ChangeClassification.DELETED_OBJECT

        return ChangeClassification.UNPERMITTED_CHANGE

    def _has_error_finding(
        self,
        findings: Sequence[
            ValidationFinding,
        ],
    ) -> bool:
        return any(
            finding.severity.value == "error"
            for finding in findings
        )

    def _highest_severity(
        self,
        findings: Sequence[
            ValidationFinding,
        ],
    ):
        """
        Return the highest finding severity.

        Ordering is:

            error > warning > info
        """

        if not findings:
            return None

        severities = tuple(
            finding.severity
            for finding in findings
        )

        for severity_value in (
            "error",
            "warning",
            "info",
        ):
            for severity in severities:
                if severity.value == severity_value:
                    return severity

        return severities[0]

    def change_key(
        self,
        change: Change,
    ) -> ChangeKey:
        """
        Return a stable key for attaching findings to a change.

        This avoids using Change objects as dictionary keys, because Change is
        a workflow model and may be mutable.
        """

        return (
            change.table_name,
            change.object_id,
            change.operation,
        )