from dataclasses import dataclass, field

from ..models.validation import ValidationFinding,ValidationSeverity


@dataclass(slots=True)
class ValidationResult:
    _findings: list[ValidationFinding] = field(
        default_factory=list,
    )


    _findings: list[ValidationFinding] = field(
        default_factory=list,
    )

    @property
    def findings(
        self,
    ) -> tuple[ValidationFinding, ...]:
        return tuple(self._findings)


    def add(
        self,
        severity: ValidationSeverity,
        message: str,
    ) -> None:
        self.findings.append(
            ValidationFinding(
                severity=severity,
                message=message,
            )
        )


    def error(
        self,
        message: str,
    ) -> None:
        self.add(
            ValidationSeverity.ERROR,
            message,
        )


    def warning(
        self,
        message: str,
    ) -> None:
        self.add(
            ValidationSeverity.WARNING,
            message,
        )


    def info(
        self,
        message: str,
    ) -> None:
        self.add(
                severity=ValidationSeverity.INFO,
                message=message,
        )

    @property
    def has(
        self,
        severity=ValidationSeverity
    ) -> bool:
        return any(
            finding.severity == severity
            for finding in self.findings
        )

    @property
    def has_errors(self) -> bool:
        return self.has(ValidationSeverity.ERROR)

