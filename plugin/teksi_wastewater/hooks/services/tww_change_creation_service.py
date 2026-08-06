from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Protocol
from collections.abc import Sequence

from tww_hooks.capabilities.canonical_object import (
    CanonicalModelCapability,
)
from tww_hooks.capabilities.relation_lookup import (
    RelationLookupCapability,
)
from tww_hooks.models.canonical_object import (
    CanonicalModelMetadata,
)
from tww_hooks.models.effects import (
    EffectDocument,
)
from tww_hooks.models.review import (
    ReviewFeature,
)
from tww_hooks.models.rights import (
    RightsEvaluationContext,
)
from tww_hooks.models.validation import (
    Change,
    ClassifiedChanges,
    ValidationFinding,
)
from tww_hooks.evaluators.rights import (
    RightsEvaluator,
)
from tww_hooks.services.change_builder import (
    ChangeBuilder,
)
from tww_hooks.services.change_classifier import (
    ChangeClassifier,
)
from tww_hooks.services.change_review_export import (
    ChangeReviewExportService,
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
from .tww_diff_schema_service import (
    DiffSchemaWriteResult,
    TwwDiffSchemaService,
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


class RightsEvaluatorFactory(Protocol):
    """
    Factory protocol for creating a rights evaluator for a workflow run.
    """

    def rights_evaluator(
        self,
        *,
        relation_lookup: RelationLookupCapability,
    ) -> RightsEvaluator:
        """
        Return a rights evaluator using the supplied relation lookup.
        """


class ChangeFeatureProviderFactory(Protocol):
    """
    Factory protocol for creating a feature provider for review feature
    preparation.
    """

    def change_feature_provider(
        self,
        *,
        live_schema: str,
        import_schema: str,
    ):
        """
        Return a ChangeFeatureProvider implementation.
        """


@dataclass(slots=True)
class ChangeCreationResult:
    """
    Mutable result of a change creation workflow.

    The result can be enriched incrementally while a long-running workflow is
    executing, for example while waiting for user confirmation or while
    writing tww_diff state.
    """

    job_id: str | None = None

    import_model: str | None = None

    created_models: list[
        str
    ] = field(
        default_factory=list,
    )

    effect_document: EffectDocument | None = None

    changes: list[
        Change
    ] = field(
        default_factory=list,
    )

    validation_findings: list[
        ValidationFinding
    ] = field(
        default_factory=list,
    )

    classified_changes: ClassifiedChanges | None = None

    features_by_class: dict[
        str,
        list[
            ReviewFeature,
        ],
    ] = field(
        default_factory=dict,
    )

    diff_schema_result: DiffSchemaWriteResult | None = None


@dataclass(slots=True)
class TwwChangeCreationService:
    """
    Plugin-side service for creating a tww_diff review job from imported data.

    The service coordinates:

    - importing an XTF into quarantine;
    - validating the quarantine schema;
    - loading canonical metadata;
    - projecting quarantine data into canonical effects;
    - resolving live/current objects;
    - building row-level Change objects;
    - classifying changes;
    - preparing review features;
    - writing the result into tww_diff.

    The service does not persist accepted changes to live data.
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

    diff_schema_service: TwwDiffSchemaService = field(
        default_factory=TwwDiffSchemaService,
    )

    rights_evaluator_factory: RightsEvaluatorFactory | None = None

    feature_provider_factory: ChangeFeatureProviderFactory | None = None

    live_relation_lookup: RelationLookupCapability | None = None

    def create_diff_job_from_xtf(
        self,
        *,
        job_id: str,
        xtf_file: Path,
        rights_context: RightsEvaluationContext,
        context: TwwInterlisContext | None = None,
        validation_log_path: Path | None = None,
        import_schema: str = config.IMPORT_SCHEMA,
        live_schema: str = config.TWW_OD_SCHEMA,
        metadata: dict[
            str,
            str,
        ] | None = None,
    ) -> ChangeCreationResult:
        """
        Import an XTF into quarantine and create a tww_diff review job.
        """

        self._ensure_ready_for_diff_job()

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
            schema=import_schema,
        )

        return self.create_diff_job_from_quarantine(
            job_id=job_id,
            source_model=import_model,
            created_models=created_models,
            rights_context=rights_context,
            import_schema=import_schema,
            live_schema=live_schema,
            metadata={
                **dict(
                    metadata or {},
                ),
                "source_model": import_model,
                "source_file": str(
                    xtf_file,
                ),
                "import_schema": import_schema,
                "live_schema": live_schema,
            },
        )

    def create_diff_job_from_quarantine(
        self,
        *,
        job_id: str,
        source_model: str,
        rights_context: RightsEvaluationContext,
        created_models: Sequence[
            str
        ] = (),
        import_schema: str = config.IMPORT_SCHEMA,
        live_schema: str = config.TWW_OD_SCHEMA,
        metadata: dict[
            str,
            str,
        ] | None = None,
    ) -> ChangeCreationResult:
        """
        Create a tww_diff re*iew job from an already populated *uarantine
        schema.
        """

        self._ensure_ready_for_diff_job()

        workflow_metadata = dict(
            metadata or {},
        )

        workflow_metadata.setdefault(
            "source_model",
            source_model,
        )
        workflow_metadata.setdefault(
            "import_schema",
            import_schema,
        )
        workflow_metadata.setdefault(
            "live_schema",
            live_schema,
        )

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

        relation_lookup = self._live_relation_lookup(
            live_schema,
        )

        rights_evaluator = self.rights_evaluator_factory.rights_evaluator(
            relation_lookup=relation_lookup,
        )

        classified_changes = ChangeClassifier(
            rights_evaluator=rights_evaluator,
        ).classify(
            changes=changes,
            context=rights_context,
            metadata=workflow_metadata,
        )
        review_service = ChangeReviewExportService(
            feature_provider=(
                self.feature_provider_factory.change_feature_provider(
                    live_schema=live_schema,
                    import_schema=import_schema,
                )
            ),
            geometry_attribute_names_by_class=self._geometry_attribute_map(
                canonical_metadata,
            ),
        )

        features_by_class = review_service.export(
            classified_changes,
        )

        diff_schema_result = self.diff_schema_service.write(
            job_id=job_id,
            features_by_class=features_by_class,
            metadata=workflow_metadata,
            validation_success=True,
            job_status="pending",
            reset_job=True,
        )

        return ChangeCreationResult(
            job_id=job_id,
            import_model=source_model,
            created_models=list(
                created_models,
            ),
            effect_document=effect_document,
            changes=list(
                changes,
            ),
            classified_changes=classified_changes,
            features_by_class=features_by_class,
            diff_schema_result=diff_schema_result,
        )