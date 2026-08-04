from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from tww_hooks.services.change_review_export_service import (
    ChangeReviewExportService,
)

from ..adapters.tww_change_feature_provider import (
    TwwChangeFeatureProvider,
)
from ..adapters.tww_gpkg_review_artifact_writer import (
    TwwGpkgReviewArtifactWriter,
)


@dataclass(slots=True)
class TwwChangeReviewExportService:
    """
    Plugin-side factory/wrapper for GeoPackage review export.
    """

    output_dir: Path

    def service(
        self,
    ) -> ChangeReviewExportService:
        return ChangeReviewExportService(
            output_dir=self.output_dir,
            feature_provider=TwwChangeFeatureProvider(),
            writer=TwwGpkgReviewArtifactWriter(),
            file_extension="gpkg",
        )