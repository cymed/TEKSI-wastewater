from __future__ import annotations

from collections import defaultdict
from collections.abc import Sequence
from dataclasses import dataclass, field, replace
from enum import StrEnum
from pathlib import Path
from typing import Any, Protocol

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
    Effect,
    EffectDocument,
    EnforceExistsEffect,
    EnforceNotExistsEffect,
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


class DiffJobMode(StrEnum):
    """
    Defines how an existing diff job is handled.
    """

    CREATE = "create"
    REPLACE = "replace"
    REFRESH = "refresh"


class QuarantineEffectProjector(Protocol):
    """
    Protocol for projecting imported quarantine data into canonical effects.

    Implementations read an ili2pg quarantine schema, apply the effective
    source-model mapping and produce an EffectDocument.
    """

    def effect_document_from_quarantine(
        self,
        *,
        schema: str,
        source_model: str,
        canonical_metadata: CanonicalModelMetadata,
    ) -> EffectDocument:
        """
        Project one populated quarantine schema into canonical effects.
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
        Return a rights evaluator using the supplied live relation lookup.
        """


class ChangeObjectProviderFactory(Protocol):
    """
    Factory protocol for creating a canonical object provider used during
    review-feature generation.
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
    Result of a change-creation workflow.

    The result exposes intermediate products for diagnostics, tests and
    subsequent review or persistence workflows.
    """

    job_id: str | None = None

    import_model: str | None = None

    incremental_import_model: str | None = None

    created_models: list[str] = field(
        default_factory=list,
    )

    incremental_created_models: list[str] = field(
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

    features_by_class: dict[
        str,
        list[ReviewFeature],
    ] = field(
        default_factory=dict,
    )

    diff_schema_result: DiffSchemaWriteResult | None = None


@dataclass(slots=True)
class TwwChangeCreationService:
    """
    Create a tww_diff review job from imported wastewater data.

    The service coordinates:

    - importing a base XTF into quarantine;
    - optionally importing an incremental XTF into a separate quarantine;
    - validating imported quarantine schemas;
    - loading canonical wastewater metadata;
    - projecting quarantine rows into canonical effects;
    - overlaying incremental effects on base-delivery effects;
    - resolving current canonical objects;
    - building row-level changes;
    - evaluating rights;
    - classifying changes;
    - preparing review features;
    - writing the resulting review job into tww_diff.

    Incremental effects override matching base effects only. A matching update
    effect is identified by canonical object identity and canonical attribute
    identifier.

    The service does not apply accepted changes to live data.
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
        job_mode: DiffJobMode,
        xtf_file: Path,
        rights_context: RightsEvaluationContext,
        orgs_path: Path | None = None,
        incremental_xtf: Path | None = None,
        incremental_import_schema: str | None = None,
        context: TwwInterlisContext | None = None,
        validation_log_path: Path | None = None,
        import_schema: str = config.IMPORT_SCHEMA,
        live_schema: str = config.TWW_OD_SCHEMA,
        metadata: dict[str, Any] | None = None,
    ) -> ChangeCreationResult:
        """
        Import one or two XTF deliveries and create a tww_diff review job.

        The source model is discovered from each XTF by the quarantine runner.
        No source-model identifier needs to be supplied by the caller.
        """

        self._ensure_ready_for_diff_job()
        self._assert_supported_job_mode(
            job_mode,
        )

        base_context = self._import_context(
            context=context,
            schema=import_schema,
            orgs_path=orgs_path,
        )

        import_model, created_models = (
            self.quarantine_runner.import_xtf_to_quarantine(
                xtf_file=xtf_file,
                context=base_context,
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

        incremental_import_model: str | None = None
        incremental_created_models: tuple[str, ...] = ()

        if incremental_xtf is not None:
            effective_incremental_schema = (
                incremental_import_schema
                or f"{import_schema}_incremental"
            )

            incremental_context = self._import_context(
                context=context,
                schema=effective_incremental_schema,
                orgs_path=None,
            )

            (
                incremental_import_model,
                incremental_created_models,
            ) = self.quarantine_runner.import_xtf_to_quarantine(
                xtf_file=incremental_xtf,
                context=incremental_context,
                schema=effective_incremental_schema,
            )

            self.quarantine_runner.validate_quarantine_or_raise(
                model_names=(
                    incremental_import_model,
                ),
                log_path=self._validation_log_path(
                    validation_log_path=None,
                    xtf_file=incremental_xtf,
                    name="validate_incremental_quarantine",
                ),
                schema=effective_incremental_schema,
            )
        else:
            effective_incremental_schema = None

        workflow_metadata = {
            **dict(
                metadata or {},
            ),
            "job_id": job_id,
            "job_mode": job_mode.value,
            "source_model": import_model,
            "source_file": str(
                xtf_file,
            ),
            "import_schema": import_schema,
            "live_schema": live_schema,
            "provider_oid": str(
                rights_context.provider_oid,
            ),
            "dataowner_oid": str(
                rights_context.dataowner_oid,
            ),
        }

        if orgs_path is not None:
            workflow_metadata["orgs_path"] = str(
                orgs_path,
            )

        if incremental_xtf is not None:
            workflow_metadata.update(
                {
                    "incremental_xtf": str(
                        incremental_xtf,
                    ),
                    "incremental_import_schema": (
                        effective_incremental_schema
                    ),
                    "incremental_source_model": (
                        incremental_import_model
                    ),
                }
            )

        return self.create_diff_job_from_quarantine(
            job_id=job_id,
            job_mode=job_mode,
            source_model=import_model,
            created_models=created_models,
            rights_context=rights_context,
            import_schema=import_schema,
            live_schema=live_schema,
            incremental_source_model=incremental_import_model,
            incremental_created_models=incremental_created_models,
            incremental_import_schema=effective_incremental_schema,
            metadata=workflow_metadata,
        )

    def create_diff_job_from_quarantine(
        self,
        *,
        job_id: str,
        job_mode: DiffJobMode,
        source_model: str,
        rights_context: RightsEvaluationContext,
        created_models: Sequence[str] = (),
        import_schema: str = config.IMPORT_SCHEMA,
        live_schema: str = config.TWW_OD_SCHEMA,
        incremental_source_model: str | None = None,
        incremental_created_models: Sequence[str] = (),
        incremental_import_schema: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> ChangeCreationResult:
        """
        Create a tww_diff review job from populated quarantine schemas.
        """

        self._ensure_ready_for_diff_job()
        self._assert_supported_job_mode(
            job_mode,
        )

        workflow_metadata = {
            **dict(
                metadata or {},
            ),
            "job_id": job_id,
            "job_mode": job_mode.value,
            "source_model": source_model,
            "import_schema": import_schema,
            "live_schema": live_schema,
            "provider_oid": str(
                rights_context.provider_oid,
            ),
            "dataowner_oid": str(
                rights_context.dataowner_oid,
            ),
        }

        if incremental_source_model is not None:
            workflow_metadata.update(
                {
                    "incremental_source_model": (
                        incremental_source_model
                    ),
                    "incremental_import_schema": (
                        incremental_import_schema
                    ),
                }
            )

        canonical_metadata = self.canonical_model.canonical_model()

        base_document = (
            self.effect_projector.effect_document_from_quarantine(
                schema=import_schema,
                source_model=source_model,
                canonical_metadata=canonical_metadata,
            )
        )

        if incremental_source_model is None:
            effect_document = base_document
        else:
            if incremental_import_schema is None:
                raise ValueError(
                    "incremental_import_schema is required when "
                    "incremental_source_model is configured."
                )

            incremental_document = (
                self.effect_projector.effect_document_from_quarantine(
                    schema=incremental_import_schema,
                    source_model=incremental_source_model,
                    canonical_metadata=canonical_metadata,
                )
            )

            effect_document = self._merge_effect_documents(
                base_document=base_document,
                incremental_document=incremental_document,
            )

        relation_lookup = self._live_relation_lookup(
            live_schema,
        )

        changes = self._build_changes(
            effect_document=effect_document,
            relation_lookup=relation_lookup,
        )

        rights_evaluator = (
            self.rights_evaluator_factory.rights_evaluator(
                relation_lookup=relation_lookup,
            )
        )

        classified_changes = ChangeClassifier(
            rights_evaluator=rights_evaluator,
        ).classify(
            changes=changes,
            context=rights_context,
            metadata=workflow_metadata,
        )

        object_provider = (
            self.object_provider_factory.change_object_provider(
                live_schema=live_schema,
                import_schema=import_schema,
                canonical_metadata=canonical_metadata,
            )
        )

        review_service = ChangeReviewExportService(
            object_provider=object_provider,
            geometry_attribute_names_by_class=(
                self._geometry_attribute_map(
                    canonical_metadata,
                )
            ),
        )

        features_by_class = review_service.export(
            classified_changes,
        )

        diff_schema_result = self.diff_schema_service.write(
            job_id=job_id,
            job_mode=job_mode,
            features_by_class=features_by_class,
            metadata=workflow_metadata,
            validation_success=True,
            job_status="pending",
        )

        return ChangeCreationResult(
            job_id=job_id,
            import_model=source_model,
            incremental_import_model=incremental_source_model,
            created_models=list(
                created_models,
            ),
            incremental_created_models=list(
                incremental_created_models,
            ),
            effect_document=effect_document,
            changes=list(
                changes,
            ),
            classified_changes=classified_changes,
            features_by_class=features_by_class,
            diff_schema_result=diff_schema_result,
        )

    def _merge_effect_documents(
        self,
        *,
        base_document: EffectDocument,
        incremental_document: EffectDocument,
    ) -> EffectDocument:
        """
        Overlay incremental effects onto a base effect document.

        Update effects are keyed by canonical identity and attribute. An
        incremental update replaces a matching base update while leaving
        unrelated base updates intact.

        Existence constraints are keyed by canonical identity and concrete
        effect type.
        """

        update_effects: dict[
            tuple[
                tuple,
                str,
            ],
            UpdateAttributeEffect,
        ] = {}

        constraint_effects: dict[
            tuple[
                tuple,
                type,
            ],
            Effect,
        ] = {}

        ordered_keys: list[
            tuple[
                str,
                tuple,
            ]
        ] = []

        def add_effect(
            effect: Effect,
        ) -> None:
            identity_key = effect.identity.key()

            if isinstance(
                effect,
                UpdateAttributeEffect,
            ):
                payload_key = (
                    identity_key,
                    effect.attribute_id,
                )
                order_key = (
                    "update",
                    payload_key,
                )

                if order_key not in ordered_keys:
                    ordered_keys.append(
                        order_key,
                    )

                update_effects[payload_key] = effect
                return

            if isinstance(
                effect,
                (
                    EnforceExistsEffect,
                    EnforceNotExistsEffect,
                ),
            ):
                payload_key = (
                    identity_key,
                    type(
                        effect,
                    ),
                )
                order_key = (
                    "constraint",
                    payload_key,
                )

                if order_key not in ordered_keys:
                    ordered_keys.append(
                        order_key,
                    )

                constraint_effects[payload_key] = effect
                return

            raise TypeError(
                f"Unsupported effect type: {type(effect)!r}"
            )

        for effect in base_document.effects:
            add_effect(
                effect,
            )

        for effect in incremental_document.effects:
            add_effect(
                effect,
            )

        merged_effects: list[Effect] = []

        for effect_kind, effect_key in ordered_keys:
            if effect_kind == "update":
                merged_effects.append(
                    update_effects[effect_key],
                )
                continue

            merged_effects.append(
                constraint_effects[effect_key],
            )

        return EffectDocument(
            source=base_document.source,
            effects=tuple(
                merged_effects,
            ),
            created_at=base_document.created_at,
            version=max(
                base_document.version,
                incremental_document.version,
            ),
        )

    def _build_changes(
        self,
        *,
        effect_document: EffectDocument,
        relation_lookup: RelationLookupCapability,
    ) -> tuple[Change, ...]:
        """
        Build row-level changes from update effects.

        EnforceExistsEffect and EnforceNotExistsEffect are constraints and
        therefore do not produce Change objects.
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
        Return the lookup used to access live canonical objects.
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
        Return geometry attribute identifiers keyed by canonical class.
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

    def _import_context(
        self,
        *,
        context: TwwInterlisContext | None,
        schema: str,
        orgs_path: Path | None,
    ) -> TwwInterlisContext:
        """
        Return an import context configured for one quarantine schema.
        """

        if context is None:
            return TwwInterlisContext(
                schema=schema,
                import_orgs=(
                    orgs_path is not None
                ),
                orgs_path=orgs_path,
            )

        return replace(
            context,
            schema=schema,
            import_orgs=(
                orgs_path is not None
            ),
            orgs_path=orgs_path,
        )

    def _assert_supported_job_mode(
        self,
        job_mode: DiffJobMode,
    ) -> None:
        """
        Reject workflow modes that are not implemented yet.
        """

        if job_mode == DiffJobMode.REFRESH:
            raise NotImplementedError(
                "Diff-job refresh is not implemented yet. "
                "Use 'create' or 'replace'."
            )

    def _ensure_ready_for_diff_job(
        self,
    ) -> None:
        """
        Ensure all required collaborators are configured.
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
                "TwwChangeCreationService is not ready for diff-job "
                f"creation. Missing: {', '.join(missing)}"
            )

    def _validation_log_path(
        self,
        *,
        validation_log_path: Path | None,
        xtf_file: Path,
        name: str,
    ) -> Path:
        """
        Return a validation log path.
        """

        if validation_log_path is not None:
            return validation_log_path

        return xtf_file.with_name(
            f"{xtf_file.stem}_{name}.log"
        )