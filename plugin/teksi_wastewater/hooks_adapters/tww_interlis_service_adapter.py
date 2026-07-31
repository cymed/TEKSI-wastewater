from dataclasses import dataclass, field
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
    TWW-specific INTERLIS import/export context.

    This context contains operation-level import/export options that are
    specific to the current TEKSI Wastewater importer/exporter.

    Database connection options remain outside this context and are handled by
    DatabaseUtils or by the CLI/runtime configuration layer.
    """

    srid: int = 2056

    logs_next_to_file: bool = False

    show_selection_dialog: bool = False

    filter_nulls: bool = False

    labels_file: Path | None = None

    selected_label_scale_indices: tuple[
        str,
        ...
    ] = field(
        default_factory=tuple,
    )

    selected_ids: tuple[
        str,
        ...
    ] = field(
        default_factory=tuple,
    )

    disable_validation: bool = False

    def apply(
        self,
        importer_exporter,
    ) -> None:
        """
        Apply context settings to the wrapped InterlisImporterExporter.

        This intentionally only applies stable operation context. Workflow
        routing flags, such as quarantine-only behavior, are handled by
        TwwQuarantineRunner.
        """

        importer_exporter.schema = self.schema

class TwwInterlisServiceAdapter(InterlisService):
    """
    Plugin-side adapter for the existing INTERLIS importer/exporter.

    The framework uses this through the generic InterlisService contract.

    Import is used to load XTF data into an ili2pg-managed schema, typically
    the quarantine or import schema. Downstream plugin adapters can then map
    the imported ili2pg structure to canonical TEKSI Wastewater objects,
    effects and changes.

    Export remains part of the adapter because it is still useful for
    INTERLIS round-trips, delivery workflows and future headless import/export
    implementations.

    This adapter intentionally keeps the current QGIS-bound
    InterlisImporterExporter behind a framework-facing service interface.
    It will be superseded by TIT.
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
        if isinstance(
            context,
            TwwInterlisContext,
        ):
            context.apply(
                self._importer_exporter,
            )
            return

        self._importer_exporter.schema = context.schema

    def import_xtf(
        self,
        xtf_file: Path,
        context: InterlisContext,
    ) -> None:
        self._apply_context(
            context,
        )

        if isinstance(
            context,
            TwwInterlisContext,
        ):
            self._importer_exporter.interlis_import(
                xtf_file_input=str(
                    xtf_file,
                ),
                show_selection_dialog=(
                    context.show_selection_dialog
                ),
                logs_next_to_file=(
                    context.logs_next_to_file
                ),
                filter_nulls=(
                    context.filter_nulls
                ),
                disable_validation=(
                    context.disable_validation
                ),
                srid=context.srid,
            )
            return

        self._importer_exporter.interlis_import(
            xtf_file_input=str(
                xtf_file,
            ),
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

        if isinstance(
            context,
            TwwInterlisContext,
        ):
            self._importer_exporter.interlis_export(
                xtf_file_output=(
                    str(
                        xtf_file,
                    )
                    if xtf_file is not None
                    else None
                ),
                export_models=list(
                    export_models,
                ),
                logs_next_to_file=(
                    context.logs_next_to_file
                ),
                labels_file=(
                    str(
                        context.labels_file,
                    )
                    if context.labels_file is not None
                    else None
                ),
                selected_labels_scales_indices=list(
                    context.selected_label_scale_indices,
                ),
                selected_ids=list(
                    context.selected_ids,
                ),
                srid=context.srid,
            )
            return

        self._importer_exporter.interlis_export(
            xtf_file_output=(
                str(
                    xtf_file,
                )
                if xtf_file is not None
                else None
            ),
            export_models=list(
                export_models,
            ),
        )

    def find_models(
        self,
        xtf_file: Path,
    ):
        return self._importer_exporter.find_import_ilimodels(
            xtf_file_input=str(xtf_file),
        )