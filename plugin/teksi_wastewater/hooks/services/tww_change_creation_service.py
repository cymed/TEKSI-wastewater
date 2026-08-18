from __future__ import annotations

from collections import defaultdict
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from pathlib import Path
from typing import Protocol

from teksi_hooks.capabilities.canonical_object import (
    CanonicalGeometryCapability,
    CanonicalModelCapability,
)
from teksi_hooks.capabilities.relation_lookup import (
    RelationLookupCapability,
)
from teksi_hooks.capabilities.review import (
    ChangeObjectProvider,
)
from teksi_hooks.evaluators.rights import (
    RightsEvaluationContext,
    RightsEvaluator,
)
from teksi_hooks.models.canonical_object import (
    CanonicalModelMetadata,
    CanonicalObjectIdentity,
)
from teksi_hooks.models.effects import (
    EffectDocument,
    UpdateAttributeEffect,
)
from teksi_hooks.models.review import (
    ReviewFeature,
)
from teksi_hooks.models.validation import (
    Change,
    ClassifiedChanges,
    ValidationFinding,
)
from teksi_hooks.services.change_builder import (
    ChangeBuilder,
)
from teksi_hooks.services.change_classifier import (
    ChangeClassifier,
)
from teksi_hooks.services.change_review_export import (
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
from ..adapters.tww_relation_lookup_adapter import (
    TwwRelationLookupAdapter,
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


class ChangeObjectProviderFactory(Protocol):
    """
    Factory protocol for creating a canonical object provider for review
    feature preparation.
    """

    def change_object_provider(
        self,
        *,
        live_schema: str,
        import_schema: str,
        canonical_metadata: CanonicalModelMetadata,
    ) -> ChangeObjectProvider:
        """
        Return a ChangeObjectProvider implementation.
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

    classified_changes: ClassifiedChanges | None = None

    features_by_class: dict[str, list[ReviewFeature]] = field(
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

    object_provider_factory: ChangeObjectProviderFactory | None = None

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
        metadata: dict[str, str] | None = None,
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
            log_path=self._validation_log_path(
                validation_log_path=validation_log_path,
                xtf_file=xtf_file,
                name="validate_import_quarantine",
            ),
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
        created_models: Sequence[str] = (),
        import_schema: str = config.IMPORT_SCHEMA,
        live_schema: str = config.TWW_OD_SCHEMA,
        metadata: dict[str, str] | None = None,
    ) -> ChangeCreationResult:
        """
        Create a tww_diff review job from an already populated quarantine
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

        relation_lookup = self._live_relation_lookup(
            live_schema,
        )

        changes = self._build_changes(
            effect_document=effect_document,
            relation_lookup=relation_lookup,
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
            object_provider=(
                self.object_provider_factory.change_object_provider(
                    live_schema=live_schema,
                    import_schema=import_schema,
                    canonical_metadata=canonical_metadata,
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

    def _build_changes(
        self,
        *,
        effect_document: EffectDocument,
        relation_lookup: RelationLookupCapability,
    ) -> tuple[Change, ...]:
        """
        Build row-level Change objects from update effects.

        Constraint effects such as EnforceExistsEffect and
        EnforceNotExistsEffect are intentionally not converted into changes.
        They should be evaluated as findings.
        """

        effects_by_identity: dict[
            tuple,
            list[UpdateAttributeEffect],
        ] = defaultdict(
            list,
        )

        identities: dict[
            tuple,
            CanonicalObjectIdentity,
        ] = {}

        for effect in effect_document.effects:
            if not isinstance(
                effect,
                UpdateAttributeEffect,
            ):
                continue

            key = effect.identity.key()

            identities[key] = effect.identity

            effects_by_identity[key].append(
                effect,
            )

        changes: list[Change] = []

        for key, effects in effects_by_identity.items():
            identity = identities[key]

            current_object = relation_lookup.current_object(
                identity,
            )

            changes.append(
                self.change_builder.build(
                    current_object=current_object,
                    effects=tuple(
                        effects,
                    ),
                )
            )

        return tuple(
            changes,
        )

    def _live_relation_lookup(
        self,
        live_schema: str,
    ) -> RelationLookupCapability:
        """
        Return the relation lookup used against the live canonical schema.
        """

        if self.live_relation_lookup is not None:
            return self.live_relation_lookup

        return TwwRelationLookupAdapter(
            schema=live_schema,
        )

    def _geometry_attribute_map(
        self,
        canonical_metadata: CanonicalModelMetadata,
    ) -> dict[str, tuple[str, ...]]:
        """
        Return geometry attribute names keyed by canonical class id.
        """

        geometry_capability = CanonicalGeometryCapability(
            metadata=canonical_metadata,
        )

        return {
            class_id: geometry_capability.geometry_attribute_names(
                class_id,
            )
            for class_id in canonical_metadata.classes
        }

    def _ensure_ready_for_diff_job(
        self,
    ) -> None:
        """
        Ensure required collaborators are configured.
        """

        missing = []

        if self.effect_projector is None:
            missing.append(
                "effect_projector",
            )

        if self.rights_evaluator_factory is None:
            missing.append(
                "rights_evaluator_factory",
            )

        if self.object_provider_factory is None:
            missing.append(
                "object_provider_factory",
            )

        if missing:
            raise RuntimeError(
                "TwwChangeCreationService is not ready for diff job "
                f"creation. Missing: {', '.join(missing)}"
            )

    def _validation_log_path(
        self,
        *,
        validation_log_path: Path | None,
        xtf_file: Path | None = None,
        name: str,
    ) -> Path:
        """
        Return the validation log path.
        """

        if validation_log_path is not None:
            return validation_log_path

        if xtf_file is not None:
            return xtf_file.with_name(
                f"{xtf_file.stem}_{name}.log"
            )

        return Path(
            f"{name}.log"
        )