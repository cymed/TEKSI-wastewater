from dataclasses import dataclass
from pathlib import Path
from collections.abc import Sequence

from ..interlis.interlis_importer_exporter import InterlisImporterExporter

from teksi_hooks.services import (
    InterlisContext,
    InterlisService,
)


@dataclass(slots=True, frozen=True)
class TwwInterlisContext(InterlisContext):
    """
    TWW-specific INTERLIS context.

    This exists only to adapt the current QGIS-bound importer/exporter, which
    still uses `to_quarantine_only` internally.
    """

    to_quarantine_only: bool = False


class TwwInterlisServiceAdapter(InterlisService):
    """
    Plugin-side adapter for the existing INTERLIS importer/exporter.

    This structure is intended to be replaced by TIT or another generic
    headless implementation later.
    """

    def __init__(
        self,
        importer_exporter: InterlisImporterExporter | None = None,
    ) -> None:
        self._importer_exporter = (
            importer_exporter
            if importer_exporter is not None
            else InterlisImporterExporter()
        )

    def _apply_context(
        self,
        context: InterlisContext,
    ) -> None:
        self._importer_exporter.schema = context.schema

        if isinstance(context, TwwInterlisContext):
            self._importer_exporter.to_quarantine_only = (
                context.to_quarantine_only
            )

    def import_xtf(
        self,
        xtf_file: Path,
        context: InterlisContext,
    ) -> None:
        self._apply_context(
            context,
        )

        self._importer_exporter.interlis_import(
            xtf_file_input=str(xtf_file),
        )

    def export_xtf(
        self,
        xtf_file: Path | None,
        export_models: Sequence[str],
        context: InterlisContext,
    ) -> None:
        self._apply_context(
            context,
        )

        self._importer_exporter.interlis_export(
            xtf_file_output=(
                str(xtf_file)
                if xtf_file is not None
                else None
            ),
            export_models=list(export_models),
        )

    def find_models(
        self,
        xtf_file: Path,
    ):
        return self._importer_exporter.find_import_ilimodels(
            xtf_file_input=str(xtf_file),
        )