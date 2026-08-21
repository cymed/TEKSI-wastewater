from __future__ import annotations

from dataclasses import dataclass
from collections.abc import Callable, Mapping
from typing import ClassVar

from teksi_hooks.exceptions import Finding
from teksi_hooks.services.finding_translator import FINDING_MESSAGE_TEMPLATES


TWW_FINDING_MESSAGE_TEMPLATES: Mapping[
    str,
    str,
] = {
    "invalid_geometry": (
        "The geometry is invalid."
    ),
    "quarantine_validation_failed": (
        "Quarantine validation failed: {reason}"
    ),
}


@dataclass(slots=True)
class TwwFindingTranslator:
    """
    Translate framework and wastewater finding messages through QGIS.

    Framework-owned templates are extended by wastewater-specific templates.
    The original finding message is used as a fallback when no template exists
    or when the template cannot be formatted with the finding details.
    """

    tr: Callable[
        [
            str,
        ],
        str,
    ]

    templates:ClassVar[
        Mapping[str,str]
    ] = {
        **FINDING_MESSAGE_TEMPLATES,
        **TWW_FINDING_MESSAGE_TEMPLATES,
    }

    def translate(
        self,
        finding: Finding,
    ) -> str:
        """
        Return the localized presentation message for a finding.
        """

        code = getattr(
            finding,
            "code",
            None,
        )

        if code is None:
            return self.tr(
                finding.message,
            )

        template = self.templates.get(
            code,
        )

        if template is None:
            return self.tr(
                finding.message,
            )

        translated_template = self.tr(
            template,
        )

        try:
            return translated_template.format(
                **finding.details,
            )
        except (
            KeyError,
            IndexError,
            ValueError,
        ):
            return self.tr(
                finding.message,
            )