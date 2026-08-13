from __future__ import annotations

from pathlib import Path

from teksi_hooks.hook import (
    HookBase,
    HookContext,
    HookMetadata,
)

from tww_hooks.models.rights import (
    RightsEvaluationContext,
)

from teksi_wastewater.interlis import (
    config,
)
from teksi_wastewater.hooks.adapters.tww_canonical_model_adapter import (
    TwwCanonicalModelAdapter,
)
from teksi_wastewater.hooks.adapters.tww_quarantine_runner import (
    TwwQuarantineRunner,
)
from teksi_wastewater.hooks.services.tww_change_creation_service import (
    ChangeFeatureProviderFactory,
    QuarantineEffectProjector,
    RightsEvaluatorFactory,
    TwwChangeCreationService,
)
from teksi_wastewater.hooks.services.tww_diff_schema_service import (
    TwwDiffSchemaService,
)


class Hook(
    HookBase,
):
    """
    Create a tww_diff review job from an XTF import.
    """

    required_capabilities = frozenset(
        {
            QuarantineEffectProjector,
            RightsEvaluatorFactory,
            ChangeFeatureProviderFactory,
        }
    )

    @property
    def metadata(
        self,
    ) -> HookMetadata:
        return HookMetadata(
            name="Create TWW Diff Review Job",
            description=(
                "Imports an XTF into quarantine, projects it to canonical "
                "changes, classifies validation and permission findings, and "
                "writes a pending review job into tww_diff."
            ),
        )

    def run_hook(
        self,
        context: HookContext,
    ) -> None:
        parameters = context.parameters

        job_id = parameters["job_id"]

        xtf_file = Path(
            parameters["xtf_input"],
        )

        import_schema = parameters.get(
            "import_schema",
            config.IMPORT_SCHEMA,
        )

        live_schema = parameters.get(
            "live_schema",
            config.TWW_OD_SCHEMA,
        )

        orgs_path = self._optional_path(
            parameters.get(
                "orgs_path",
            )
        )

        ag64_adaptation_path = self._optional_path(
            parameters.get(
                "ag64_adaptation_path",
            )
        )

        provider_rights_path = self._optional_path(
            parameters.get(
                "provider_rights_path",
            )
        )

        provider_privileges_path = self._optional_path(
            parameters.get(
                "provider_privileges_path",
            )
        )

        provider_oid = parameters["provider_oid"]
        dataowner_oid = parameters["dataowner_oid"]

        rights_context = RightsEvaluationContext(
            provider_oid=provider_oid,
            dataowner_oid=dataowner_oid,
            context_values={
                "provider_oid": provider_oid,
                "dataowner_oid": dataowner_oid,
            },
        )

        rights_evaluator_factory = context.capability(
            RightsEvaluatorFactory,
        )

        if hasattr(
            rights_evaluator_factory,
            "configure_templates",
        ):
            rights_evaluator_factory.configure_templates(
                provider_rights_path=provider_rights_path,
                provider_privileges_path=provider_privileges_path,
            )

        service = TwwChangeCreationService(
            quarantine_runner=TwwQuarantineRunner(),
            canonical_model=TwwCanonicalModelAdapter(),
            effect_projector=context.capability(
                QuarantineEffectProjector,
            ),
            rights_evaluator_factory=rights_evaluator_factory,
            feature_provider_factory=context.capability(
                ChangeFeatureProviderFactory,
            ),
            diff_schema_service=TwwDiffSchemaService(),
        )

        result = service.create_diff_job_from_xtf(
            job_id=job_id,
            xtf_file=xtf_file,
            orgs_path=orgs_path,
            ag64_adaptation_path=ag64_adaptation_path,
            rights_context=rights_context,
            import_schema=import_schema,
            live_schema=live_schema,
            metadata={
                "source_file": str(
                    xtf_file,
                ),
                "orgs_path": (
                    str(
                        orgs_path,
                    )
                    if orgs_path is not None
                    else None
                ),
                "ag64_adaptation_path": (
                    str(
                        ag64_adaptation_path,
                    )
                    if ag64_adaptation_path is not None
                    else None
                ),
                "provider_rights_path": (
                    str(
                        provider_rights_path,
                    )
                    if provider_rights_path is not None
                    else None
                ),
                "provider_privileges_path": (
                    str(
                        provider_privileges_path,
                    )
                    if provider_privileges_path is not None
                    else None
                ),
                "import_schema": import_schema,
                "live_schema": live_schema,
                "provider_oid": str(
                    provider_oid,
                ),
                "dataowner_oid": str(
                    dataowner_oid,
                ),
            },
        )

        context.logger.info(
            "Created tww_diff review job '%s' with %s rows.",
            result.job_id,
            (
                result.diff_schema_result.row_count
                if result.diff_schema_result is not None
                else "unknown"
            ),
        )

    def _optional_path(
        self,
        value,
    ) -> Path | None:
        if value in (
            None,
            "",
        ):
            return None

        return Path(
            value,
        )