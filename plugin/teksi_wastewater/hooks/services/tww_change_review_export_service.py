from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from tww_hooks.models.validation import (
    ClassifiedChanges,
)


@dataclass(slots=True)
class TwwChangeGpkgExportService:
    """
    Export classified changes to GeoPackage review artifacts.

    The service creates one GeoPackage per review category:

    - created_objects.gpkg
    - altered_objects.gpkg
    - deleted_objects.gpkg
    - unpermitted_changes.gpkg
    """

    output_dir: Path

    def export(
        self,
        classified: ClassifiedChanges,
    ) -> dict[str, Path]:
        self.output_dir.mkdir(
            parents=True,
            exist_ok=True,
        )

        artifacts = {}

        artifacts["created_objects"] = self._export_changes(
            name="created_objects",
            changes=classified.created_objects,
        )

        artifacts["altered_objects"] = self._export_changes(
            name="altered_objects",
            changes=classified.altered_objects,
        )

        artifacts["deleted_objects"] = self._export_changes(
            name="deleted_objects",
            changes=classified.deleted_objects,
        )

        artifacts["unpermitted_changes"] = self._export_changes(
            name="unpermitted_changes",
            changes=classified.unpermitted_changes,
        )

        return artifacts

    def _export_changes(
        self,
        name: str,
        changes,
    ) -> Path:
        path = self.output_dir / f"{name}.gpkg"

        # Placeholder for implementation.
        # This should eventually write one or more layers to the GeoPackage.
        #
        # Possible layer strategy:
        #   - one layer per canonical class
        #   - or one generic layer with attributes and no geometry
        #
        # Geometry source can come later from live DB / quarantine DB / QGIS layer.
        path.touch()

        return path
