from dataclasses import dataclass, field
from pathlib import Path
from collections.abc import Sequence

from ..interlis import config
from .tww_interlis_service_adapter import (
    TwwInterlisContext,
    TwwInterlisServiceAdapter,
)
from ..interlis.utils.ili2db import InterlisTools

from tww_hooks.exceptions import (
    Severity,
)
from tww_hooks.models.validation import (
    ValidationFinding,
)


from .exceptions import QuarantineValidationError 

@dataclass(slots=True)
class TwwQuarantineRunner:
    """
    Plugin-side runner for the TEKSI Wastewater quarantine workflow.

    The runner exposes the real workflow steps and hides the current
    importer/exporter quarantine flags behind method names.
    """

    interlis_service: TwwInterlisServiceAdapter = field(
        default_factory=TwwInterlisServiceAdapter,
    )
    interlis_tools: InterlisTools = field(
            default_factory=InterlisTools,
            )

    def import_xtf_to_quarantine(
        self,
        xtf_file: Path,
        schema: str = config.IMPORT_SCHEMA,
    ) -> None:
        self.interlis_service.import_xtf(
            xtf_file=xtf_file,
            context=TwwInterlisContext(
                schema=schema,
                to_quarantine_only=True,
            ),
        )

    def import_quarantine_to_live(
        self,
        xtf_file: Path,
        schema: str = config.IMPORT_SCHEMA,
    ) -> None:
        
        self.interlis_service.import_xtf(
            xtf_file=xtf_file,
            context=TwwInterlisContext(
                schema=schema,
                to_quarantine_only=True,
            ),
        )

    def export_live_to_quarantine(
        self,
        xtf_file: Path | None,
        export_models: Sequence[str],
        schema: str = config.EXPORT_SCHEMA,
    ) -> None:
        self.interlis_service.export_xtf(
            xtf_file=xtf_file,
            export_models=export_models,
            context=TwwInterlisContext(
                schema=schema,
                to_quarantine_only=True,
            ),
        )

    def export_quarantine_to_xtf(
        self,
        xtf_file: Path,
        export_models: Sequence[str],
        schema: str = config.EXPORT_SCHEMA,
    ) -> None:
        self.interlis_service.export_xtf(
            xtf_file=xtf_file,
            export_models=export_models,
            context=TwwInterlisContext(
                schema=schema,
                to_quarantine_only=True,
            ),
        )


    def validate_quarantine(
        self,
        models: Sequence[str],
        log_path: Path,
        srid: int = 2056,
        schema: str = config.IMPORT_SCHEMA,
    ) -> tuple[
        ValidationFinding,
        ...
    ]:
        """
        Validate the quarantine schema using ili2pg --validate.

        Returns an empty tuple if validation succeeds.
        Returns validation findings if validation fails.
        """

        try:
            self.interlis_tools.validate_db_data(
                schema=schema,
                log_path=str(
                    log_path,
                ),
                models=tuple(
                    models,
                ),
                srid=srid,
            )
        except Exception as exception:
            findings = self._validation_findings_from_log(
                log_path,
            )

            if findings:
                return findings

            return (
                ValidationFinding(
                    code="quarantine_validation_failed",
                    severity=Severity.ERROR,
                    message=str(
                        exception,
                    ),
                    attribute_name=None,
                ),
            )

        return ()

    def validate_quarantine_or_raise(
        self,
        models: Sequence[str],
        log_path: Path,
        srid: int = 2056,
        schema: str = config.IMPORT_SCHEMA,
    ) -> None:
        findings = self.validate_quarantine(
            schema=schema,
            models=models,
            log_path=log_path,
            srid=srid,
        )

        errors = tuple(
            finding
            for finding in findings
            if finding.severity == Severity.ERROR
        )

        if errors:
            raise QuarantineValidationError(
                findings=errors,
                log_path=str(
                    log_path,
                ),
            )

    def _validation_findings_from_log(
        self,
        log_path: Path,
    ) -> tuple[
        ValidationFinding,
        ...
    ]:
        """
        Extract validation findings from the ili2pg validation log.
        """

        if not log_path.exists():
            return ()

        findings: list[
            ValidationFinding
        ] = []

        for line in log_path.read_text(
            encoding="utf-8",
            errors="replace",
        ).splitlines():
            message = line.strip()

            if not message:
                continue

            lowered = message.lower()

            if (
                "error" not in lowered
                and "failed" not in lowered
                and "invalid" not in lowered
            ):
                continue

            findings.append(
                ValidationFinding(
                    code="quarantine_validation_failed",
                    severity=Severity.ERROR,
                    message=message,
                    attribute_name=None,
                )
            )

        return tuple(
            findings,
        )