from dataclasses import dataclass, field

from ..models.validation import (
    ValidationFinding,
    ValidationSeverity,
)


@dataclass(slots=True)
class ValidationResult:
    """
    Collects validation findings produced during hook execution.

    The internal finding list is mutable so validators can append findings.
    Consumers receive an immutable tuple through the `findings` property.
    """

    _findings: list[ValidationFinding] = field(
        default_factory=list,
    )

    @property
    def findings(
        self,
    ) -> tuple[ValidationFinding, ...]:
        """
        Return collected validation findings as an immutable tuple.
        """

        return tuple(
            self._findings,
        )

    def add(
        self,
        severity: ValidationSeverity,
        message: str,
    ) -> None:
        """
        Add a validation finding.
        """

        self._findings.append(
            ValidationFinding(
                severity=severity,
                message=message,
            )
        )

    def error(
        self,
        message: str,
    ) -> None:
        """
        Add an error finding.
        """

        self.add(
            ValidationSeverity.ERROR,
            message,
        )

    def warning(
        self,
        message: str,
    ) -> None:
        """
        Add a warning finding.
        """

        self.add(
            ValidationSeverity.WARNING,
            message,
        )

    def info(
        self,
        message: str,
    ) -> None:
        """
        Add an informational finding.
        """

        self.add(
            ValidationSeverity.INFO,
            message,
        )

    def has(
        self,
        severity: ValidationSeverity,
    ) -> bool:
        """
        Return whether at least one finding with the given severity exists.
        """

        return any(
            finding.severity == severity
            for finding in self._findings
        )

    @property
    def has_errors(
        self,
    ) -> bool:
        """
        Return whether at least one error finding exists.
        """

        return self.has(
            ValidationSeverity.ERROR,
        )