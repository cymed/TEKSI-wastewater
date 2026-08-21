from __future__ import annotations

from enum import StrEnum        
import os
from pathlib import Path
from uuid import uuid4


from teksi_hooks.hook import (
    HookBase,
    HookContext,
    HookMetadata,
)

from teksi_hooks.models.oid import Standardoid
from teksi_hooks.models.rights import RightsEvaluationContext

from teksi_hooks.exceptions import RightsEvaluationError
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
    ChangeObjectProviderFactory,
    QuarantineEffectProjector,
    RightsEvaluatorFactory,
    TwwChangeCreationService,
)
from teksi_wastewater.hooks.services.tww_diff_schema_service import (
    TwwDiffSchemaService,
    DiffJobMode,
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
            ChangeObjectProviderFactory,
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

        job_id = parameters.get("job_id",str(uuid4()))

        job_mode = DiffJobMode(
            parameters.get(
                "job_mode",
                DiffJobMode.CREATE,
            )
        )

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

        incremental_xtf = self._optional_path(
            parameters.get(
                "incremental_xtf",
            )
        )

        incremental_import_schema = parameters.get(
                "incremental_import_schema",
                None
            )

        hook_config_dir = (
            self._optional_path(parameters.hook_config_dir)
            or (
                Path(os.environ["TWW_DIFF_CONF_DIR"])
                if "TWW_DIFF_CONF_DIR" in os.environ
                else None
            )
        )

        provider_rights_path,provider_privileges_path = self._eval_rights_profile(
            hook_config_dir,
            parameters.get(
                "rights_profile",
                'default',
            )
        )

        provider_oid = Standardoid(parameters["provider_oid"])
        dataowner_oid = Standardoid(parameters["dataowner_oid"])

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
            object_provider_factory=context.capability(
                ChangeObjectProviderFactory,
            ),
            diff_schema_service=TwwDiffSchemaService(),
        )

        result = service.create_diff_job_from_xtf(
            job_id=job_id,
            job_mode=job_mode,
            xtf_file=xtf_file,
            orgs_path=orgs_path,
            incremental_xtf=incremental_xtf,
            incremental_import_schema=incremental_import_schema,
            rights_context=rights_context,
            import_schema=import_schema,
            live_schema=live_schema,
            metadata={
                "provider_rights_path": (
                    str(provider_rights_path)
                    if provider_rights_path is not None
                    else None
                ),
                "provider_privileges_path": (
                    str(provider_privileges_path)
                    if provider_privileges_path is not None
                    else None
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

    def _eval_rights_profile(
        self,
        config_dir: Path | None,
        rights_profile: str,
    ) -> tuple[Path | None, Path | None]:
        if config_dir is None:
            raise RightsEvaluationError.from_message("Config Directory not set.")
        
        profile_dir = config_dir / rights_profile

        provider_rights_path = (
            profile_dir / "provider-rights.yaml"
        )

        provider_privileges_path = (
            profile_dir / "provider-privileges.yaml"
        )

        return (
            provider_rights_path
            if provider_rights_path.exists()
            else None,
            provider_privileges_path
            if provider_privileges_path.exists()
            else None,
        )