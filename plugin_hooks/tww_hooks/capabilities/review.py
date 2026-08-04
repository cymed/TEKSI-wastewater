from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Protocol
from collections.abc import Mapping, Sequence

from ..models.validation import (
    Change,
)

from ..models.review import ReviewFeature

class ChangeFeatureProvider(Protocol):
    """
    Provides canonical attribute and geometry values for changes.

    Implementations may read from:

    - live canonical tables
    - import quarantine schema
    - export quarantine schema
    - QGIS layers
    - later: canonical feature repository
    """

    def old_feature(
        self,
        change: Change,
    ) -> ReviewFeature | None:
        """
        Return the old/live feature for a change.
        Used mainly for deleted objects and diff context.
        """

    def new_feature(
        self,
        change: Change,
    ) -> ReviewFeature | None:
        """
        Return the new/projected feature for a change.
        Used mainly for created and altered objects.
        """

class ReviewArtifactWriter(Protocol):
    """
    Writes grouped review features to an artifact.

    The first implementation will write GeoPackages, but the service should
    not depend on that detail.
    """

    def write(
        self,
        path: Path,
        layers: Mapping[
            str,
            Sequence[
                ReviewFeature,
            ],
        ],
    ) -> None:
        """
        Write layers to the given path.
        """
