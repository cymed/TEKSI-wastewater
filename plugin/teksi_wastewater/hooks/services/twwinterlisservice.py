
from pathlib import Path 
from ...interlis.interlis_importer_exporter import InterlisImporterExporter
from .interlis import InterlisService

class TWWInterlisService(
    InterlisService,
):
    # This structure is intended to be replaced by TIT
    def __init__(
        self,
        *,
        to_quarantine_only: bool = False,
        schema: str | None = None,
    ) -> None:
        self._importer_exporter = (
            InterlisImporterExporter()
        )

        self._importer_exporter.to_quarantine_only = (
            to_quarantine_only
        )

        self._importer_exporter.schema = schema

    def import_xtf(
        self,
        xtf_file: Path,
    ) -> None:
        self._importer_exporter.interlis_import(
            xtf_file_input=str(xtf_file),
        )


    def export_xtf(
        self,
        xtf_file: Path | None,
        export_models: list[str],
    ) -> None:
        self._importer_exporter.interlis_export(
            xtf_file_output=xtf_file,
            export_models=export_models,
        )


    def find_models(
        self,
        xtf_file: Path,
    ) -> list:
        return self._importer_exporter.find_import_ilimodels(
            xtf_file_input=str(xtf_file),
        )
