from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Protocol
from collections.abc import Sequence

from tww_hooks.capabilities.canonical_model import (
    CanonicalModelCapability,
)
from tww_hooks.capabilities.relation_lookup import (
    RelationLookupCapability,
)
from tww_hooks.models.canonical_model import (
    CanonicalModelMetadata,
)
from tww_hooks.models.canonical_object import (
    CanonicalObjectIdentity,
)
from tww_hooks.models.change import (
    Change,
)
from tww_hooks.models.effects import (
    Effect,
    EffectDocument,
)
from tww_hooks.services.change_builder import (
    ChangeBuilder,
)

from ...interlis import config
from ..adapters.tww_canonical_model_adapter import (
    TwwCanonicalModelAdapter,
)
from ..adapters.tww_interlis_service_adapter import (
    TwwInterlisContext,
)
from ..adapters.tww_quarantine_runner import (
    TwwQuarantineRunner,
)
from ..adapters.tww_relation_lookup_adapter import (
    TwwRelationLookupAdapter,
)

from tww_hooks.models.validation import (
    ValidationFinding,
)



class QuarantineEffectProjector(Protocol):
    """
    Protocol for projecting imported quarantine data into canonical effects.

    Implementations are responsible for reading the ili2pg quarantine schema,
    mapping source rows through canonical metadata, and producing an
    EffectDocument.
    """

    def effect_document_from_quarantine(
        self,
        *,
        schema: str,
        source_model: str,
        canonical_metadata: CanonicalModelMetadata,
    ) -> EffectDocument:
        """
        Project the current quarantine schema into a canonical effect document.
        """




@dataclass(slots=True)
class ChangeCreationResult:
    """
    Mutable result of a change creation workflow.

    The result can be enriched incrementally while a long-running workflow is
    executing, for example while waiting for user confirmation or while
    exporting review artifacts.
    """

    import_model: str | None = None

    created_models: list[str] = field(
        default_factory=list,
    )

    effect_document: EffectDocument | None = None

    changes: list[Change] = field(
        default_factory=list,
    )

    validation_findings: list[ValidationFinding] = field(
        default_factory=list,
    )

    review_artifacts: dict[str, Path] = field(
        default_factory=dict,
    )

@dataclass(slots=True)
class TwwChangeCreationService:
    """
    Plugin-side service for creating canonical changes from imported data.

    The service coordinates:

    - importing an XTF into quarantine;
    - validating the quarantine schema;
    - loading canonical metadata;
    - projecting quarantine data into canonical effects;
    - resolving live/current objects;
    - building row-level Change objects.

    The service does not persist changes. It creates a reviewable change set.
    """

    quarantine_runner: TwwQuarantineRunner = field(
        default_factory=TwwQuarantineRunner,
    )

    canonical_model: CanonicalModelCapability = field(
        default_factory=TwwCanonicalModelAdapter,
    )

    effect_projector: QuarantineEffectProjector | None = None

    change_builder: ChangeBuilder = field(
        default_factory=ChangeBuilder,
    )

    live_relation_lookup: RelationLookupCapability | None = None

    def create_changes_from_xtf(
        self,
        *,
        xtf_file: Path,
        context: TwwInterlisContext,
        validation_log_path: Path,
        import_schema: str = config.IMPORT_SCHEMA,
        live_schema: str = config.TWW_OD_SCHEMA,
    ) -> ChangeCreationResult:
        """
        Create canonical changes from an XTF.

        This method imports the XTF into the import-side quarantine schema,
        validates the quarantine schema, projects the imported data into an
        EffectDocument, and builds Change objects by comparing the effects
        against the current live database state.
        """

        self._ensure_projector()

        import_model, created_models = (
            self.quarantine_runner.import_xtf_to_quarantine(
                xtf_file=xtf_file,
                context=context,
                schema=import_schema,
            )
        )

        self.quarantine_runner.validate_quarantine_or_raise(
            model_names=(
                import_model,
            ),
            log_path=validation_log_path,
            srid=context.srid,
            schema=import_schema,
        )

        return self.create_changes_from_quarantine(
            source_model=import_model,
            created_models=created_models,
            import_schema=import_schema,
            live_schema=live_schema,
        )

    def create_changes_from_quarantine(
        self,
        *,
        source_model: str,
        created_models: Sequence[str] = (),
        import_schema: str = config.IMPORT_SCHEMA,
        live_schema: str = config.TWW_OD_SCHEMA,
    ) -> ChangeCreationResult:
        """
        Create canonical changes from an already populated quarantine schema.

        This method assumes quarantine import and validation have already
        happened or are intentionally handled by the caller.
        """

        self._ensure_projector()

        canonical_metadata = self.canonical_model.canonical_model()

        effect_document = self.effect_projector.effect_document_from_quarantine(
            schema=import_schema,
            source_model=source_model,
            canonical_metadata=canonical_metadata,
        )

        changes = self._build_changes(
            effect_document=effect_document,
            live_schema=live_schema,
        )

        return ChangeCreationResult(
            import_model=source_model,
            created_models=tuple(
                created_models,
            ),
            effect_document=effect_document,
            changes=changes,
        )

    def _build_changes(
        self,
        *,
        effect_document: EffectDocument,
        live_schema: str,
    ) -> tuple[
        Change,
        ...
    ]:
        relation_lookup = self._live_relation_lookup(
            live_schema,
        )

        changes: list[
            Change
        ] = []

        for identity, effects in self._effects_by_identity(
            effect_document.effects,
        ).items():
            current_object = relation_lookup.current_object(
                identity,
            )

            change = self.change_builder.build(
                identity=identity,
                current_object=current_object,
                effects=effects,
            )

            changes.append(
                change,
            )

        return tuple(
            changes,
        )

    def _effects_by_identity(
        self,
        effects: Sequence[
            Effect,
        ],
    ) -> dict[
        CanonicalObjectIdentity,
        tuple[
            Effect,
            ...
        ],
    ]:
        grouped: dict[
            CanonicalObjectIdentity,
            list[
                Effect
            ],
        ] = {}

        for effect in effects:
            grouped.setdefault(
                effect.identity,
                [],
            ).append(
                effect,
            )

        return {
            identity: tuple(
                grouped_effects,
            )
            for identity, grouped_effects in grouped.items()
        }

    def _live_relation_lookup(
        self,
        live_schema: str,
    ) -> RelationLookupCapability:
        if self.live_relation_lookup is not None:
            return self.live_relation_lookup

        return TwwRelationLookupAdapter(
            schema=live_schema,
        )

    def _ensure_projector(
        self,
    ) -> None:
        if self.effect_projector is None:
            raise RuntimeError(
                "TwwChangeCreationService requires an effect_projector. "
                "Provide a QuarantineEffectProjector implementation before "
                "creating changes."
            )