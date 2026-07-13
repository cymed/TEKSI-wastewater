from dataclasses import dataclass, field

from ..models.validation import ValidationFinding,ValidationSeverity


@dataclass(slots=True)
class ValidationCapability:
    findings: list[ValidationFinding] = field(
        default_factory=list,
    )

    def add(
        self,
        finding: ValidationFinding,
    ) -> None:
        self.findings.append(
            finding,
        )


    def error(
        self,
        message: str,
    ) -> None:
        self.findings.append(
            ValidationFinding(
                severity=ValidationSeverity.ERROR,
                message=message,
            )
        )

    def warning(
        self,
        message: str,
    ) -> None:
        self.findings.append(
            ValidationFinding(
                severity=ValidationSeverity.WARNING,
                message=message,
            )
        )

    def info(
        self,
        message: str,
    ) -> None:
        self.findings.append(
            ValidationFinding(
                severity=ValidationSeverity.INFO,
                message=message,
            )
        )

    @property
    def has_errors(
        self,
    ) -> bool:
        return any(
            finding.severity == "error"
            for finding in self.findings
        )