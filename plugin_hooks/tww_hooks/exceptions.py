from dataclasses import dataclass, field
from enum import StrEnum
from collections.abc import Iterable

from teksi_hooks.exceptions import (
    TeksiHookError,
)

class Severity(StrEnum):
    """
    Severity levels used by findings.
    """

    INFO = "info"
    WARNING = "warning"
    ERROR = "error"

@dataclass(slots=True, frozen=True)
class Finding():
    """
    Base class for findings.
    """

    severity: Severity = field(
        metadata={
            "doc": (
                "Severity level assigned to the finding."
            )
        },
    )

    message: str = field(
        metadata={
            "doc": (
                "Human-readable description of the validation issue."
            )
        },
    )

class TwwHookError(
    TeksiHookError,
):
    """
    Base class for framework failures backed by findings.
    """

    def __init__(
        self,
        findings: tuple[Finding, ...],
    ):
        self.findings = findings

        super().__init__(
            "\n".join(
                finding.message
                for finding in findings
            )
        )

    @classmethod
    def raise_if_errors(
        cls,
        findings: Iterable[Finding],
    ) -> None:
        errors = tuple(
            finding
            for finding in findings
            if finding.severity == Severity.ERROR
        )

        if errors:
            raise cls(errors)


class ValidationError(
    TwwHookError,
):
    """
    Base class for validation-related failures.
    """


class EffectValidationError(
    ValidationError,
):
    """
    EffectDocument contains invalid or contradictory effects.
    """


class RightsEvaluationError(
    TwwHookError,
):
    """
    Rights evaluation could not be completed.
    """


class SnapshotValidationError(
    ValidationError,
):
    """
    Snapshot validation failed due to invalid snapshot state.
    """
