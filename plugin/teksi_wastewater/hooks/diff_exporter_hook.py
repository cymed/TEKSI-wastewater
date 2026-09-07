from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Mapping
from uuid import uuid4
import yaml


from teksi_hooks.hook import (
    HookBase,
    HookContext,
    HookMetadata,
)

from teksi_hooks.models.oid import Standardoid

from teksi_hooks.evaluators.rights import RightsEvaluator,RightsEvaluationContext

from teksi_hooks.parsers.rights_parser import RightsParser
from teksi_hooks.parsers.provider_rights_parser import ProviderRightsParser
from teksi_hooks.parsers.validation import ValidationParser
from teksi_hooks.parsers.model_mapping_parser import ModelMappingParser

from teksi_hooks.resolver.provider_resolver import ProviderResolver
from teksi_hooks.resolver.rights_resolver import RightsResolver

from teksi_hooks.exceptions import RightsEvaluationError

from teksi_hooks.capabilities.connection import DatabaseConnectionFactory
from teksi_hooks.capabilities.rights import (
    RightsCapability,
    DerivedRightsCapability,
    SubclassRightsCapability,
)
from teksi_hooks.capabilities.privilege import ResolvedProviderCapability
from teksi_hooks.capabilities.conditions import ConditionsCapability

from teksi_wastewater.interlis import (
    config,
)
from teksi_wastewater.hooks.adapters.tww_canonical_model_adapter import (
    TwwCanonicalModelAdapter,
)
from teksi_wastewater.hooks.adapters.tww_quarantine_runner import (
    TwwQuarantineRunner,
)
from teksi_wastewater.hooks.adapters.tww_database_connection_factory import (
    TwwDatabaseConnectionFactory,
)
from teksi_wastewater.hooks.adapters.tww_interlis_service_adapter import (
    TwwInterlisServiceAdapter,
)
from teksi_wastewater.hooks.adapters.tww_relation_lookup_adapter import (
    TwwRelationLookupAdapter,
)
from teksi_wastewater.hooks.services.tww_change_creation_service import (
    ChangeObjectProviderFactory,
    QuarantineEffectProjector,
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
                config.IMPORT_SCHEMA_INCR
            )
        hook_config_dir = (
            self._optional_path(
                parameters.get(
                    "hook_config_dir",
                )
            )
            or (
                Path(
                    os.environ["TWW_DIFF_CONF_DIR"],
                )
                if "TWW_DIFF_CONF_DIR" in os.environ
                else None
            )
        )

        provider_oid = Standardoid(parameters["provider_oid"])
        dataowner_oid = Standardoid(parameters["dataowner_oid"])

        model_config_dir = self._model_config_dir()

        validation_definition = ValidationParser().parse_file(
            model_config_dir
            / "validation.yaml",
        )

        incremental_mapping = ModelMappingParser().parse_file(
            model_config_dir
            / "agxx_mapping.yaml",
        )

        provider_rights_path,rights_definition_path = self._eval_rights_profile(
            hook_config_dir,
            parameters.get(
                "rights_profile",
                'default',
            )
        )
        rights_definition=RightsParser().parse_file(
            rights_definition_path
        )
        raw_provider_rights=ProviderRightsParser().parse_file(
            provider_rights_path
        )
        resolved_providers = ProviderResolver.resolve_all(raw_provider_rights)
        resolved_provider = resolved_providers[provider_oid]

        rights_context = RightsEvaluationContext(
            provider_oid=provider_oid,
            dataowner_oid=dataowner_oid,
            context_values={
                "provider_oid": provider_oid,
                "dataowner_oid": dataowner_oid,
            },
        )

        connection_factory = context.capability(
            DatabaseConnectionFactory,
        )

        if not isinstance(
            connection_factory,
            TwwDatabaseConnectionFactory,
        ):
            raise TypeError(
                "The TWW diff hook requires TwwDatabaseConnectionFactory."
            )

        interlis_service = TwwInterlisServiceAdapter(
            connection_factory=connection_factory,
        )

        quarantine_runner = TwwQuarantineRunner(
            interlis_service=interlis_service,
        )

        canonical_model = TwwCanonicalModelAdapter(
            connection_factory=connection_factory,
        )
        canonical_metadata=canonical_model.canonical_model()

        diff_schema_service = TwwDiffSchemaService(
            connection_factory=connection_factory,
        )
        relation_lookup = TwwRelationLookupAdapter(
            schema=live_schema,
            connection_factory=connection_factory,
        )


        resolved_rights = RightsResolver().resolve(
            definition=rights_definition,
            validation_definition=validation_definition,
            canonical_metadata=canonical_metadata,
        )

        rights_capability = RightsCapability(
            resolved_rights,
        )

        provider_capability = ResolvedProviderCapability(
            resolved_provider,
        )

        conditions_capability = ConditionsCapability()

        derived_rights_capability = DerivedRightsCapability(
            resolved_rights,
        )

        subclass_rights_capability = SubclassRightsCapability(
            resolved_rights,
        )

        rights_evaluator = RightsEvaluator(
            rights=rights_capability,
            provider=provider_capability,
            conditions=conditions_capability,
            derived_rights=derived_rights_capability,
            relation_lookup=relation_lookup,
            subclass_rights=subclass_rights_capability,
        )

        service = TwwChangeCreationService(
            connection_factory=connection_factory,
            quarantine_runner=quarantine_runner,
            canonical_model=canonical_model,
            effect_projector=context.capability(
                QuarantineEffectProjector,
            ),
            rights_evaluator=rights_evaluator,
            object_provider_factory=context.capability(
                ChangeObjectProviderFactory,
            ),
            diff_schema_service=diff_schema_service,
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
                "resolved_provider": (
                    str(resolved_provider)
                    if resolved_provider is not None
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
    ) -> tuple[
        Path,
        Path,
    ]:
        """
        Resolve the provider-rights and provider-privileges templates configured
        for one rights profile.

        Paths in ``rights_profiles.yaml`` are resolved relative to the configured
        validation directory.
        """

        if config_dir is None:
            raise RightsEvaluationError.from_message(
                "Config directory is not set."
            )

        profiles_path = (
            config_dir
            / "rights_profiles.yaml"
        )

        if not profiles_path.is_file():
            raise RightsEvaluationError.from_message(
                "Rights-profile configuration does not exist: "
                f"{profiles_path}"
            )

        with profiles_path.open(
            encoding="utf-8",
        ) as file:
            raw_profiles: Any = yaml.safe_load(
                file,
            )

        if not isinstance(
            raw_profiles,
            Mapping,
        ):
            raise RightsEvaluationError.from_message(
                "Rights-profile configuration must contain a mapping "
                f"of profile identifiers: {profiles_path}"
            )

        raw_profile = raw_profiles.get(
            rights_profile,
        )

        if raw_profile is None:
            available_profiles = ", ".join(
                sorted(
                    str(
                        profile_name,
                    )
                    for profile_name in raw_profiles
                )
            )

            raise RightsEvaluationError.from_message(
                f"Unknown rights profile {rights_profile!r}. "
                f"Available profiles: {available_profiles or 'none'}."
            )

        if not isinstance(
            raw_profile,
            Mapping,
        ):
            raise RightsEvaluationError.from_message(
                f"Rights profile {rights_profile!r} must be a mapping."
            )

        provider_rights_path = (
            self._profile_template_path(
                config_dir=config_dir,
                profile_name=rights_profile,
                profile=raw_profile,
                key="provider_rights",
            )
        )

        rights_definition_path = (
            self._profile_template_path(
                config_dir=config_dir,
                profile_name=rights_profile,
                profile=raw_profile,
                key="rights_definition",
            )
        )

        missing_paths = [
            path
            for path in (
                provider_rights_path,
                rights_definition_path,
            )
            if not path.is_file()
        ]

        if missing_paths:
            raise RightsEvaluationError.from_message(
                f"Rights profile {rights_profile!r} is incomplete. Missing: "
                + ", ".join(
                    str(
                        path,
                    )
                    for path in missing_paths
                )
            )

        return (
            provider_rights_path,
            rights_definition_path,
        )

    def _profile_template_path(
        self,
        *,
        config_dir: Path,
        profile_name: str,
        profile: Mapping[
            str,
            Any,
        ],
        key: str,
    ) -> Path:
        """
        Resolve one template path from a rights-profile definition.

        Relative paths are resolved against ``config_dir``. Absolute paths remain
        supported for explicitly configured external templates.
        """

        raw_path = profile.get(
            key,
        )

        if not isinstance(
            raw_path,
            str,
        ) or not raw_path.strip():
            raise RightsEvaluationError.from_message(
                f"Rights profile {profile_name!r} must define a non-empty "
                f"{key!r} path."
            )

        path = Path(
            raw_path,
        ).expanduser()

        if not path.is_absolute():
            path = (
                config_dir
                / path
            )

        return path.resolve()

    def _model_config_dir(
        self,
    ) -> Path:
        """
        Return the absolute path to immutable model configuration shipped with
        the hook.
        """

        path = (
            Path(
                __file__,
            ).resolve().parent
            / "config"
            / "model"
        )

        if not path.is_dir():
            raise RuntimeError(
                "Model configuration directory does not exist: "
                f"{path}"
            )

        return path