from __future__ import annotations

import argparse
import logging
from pathlib import Path

from teksi_hooks.hook import (
    HookContext,
    HookHandler,
)

from teksi_wastewater.interlis import (
    config,
)
from teksi_wastewater.hooks.adapters.tww_change_feature_provider_factory import (
    TwwChangeFeatureProviderFactory,
)
from teksi_wastewater.hooks.adapters.tww_quarantine_effect_projector import (
    TwwQuarantineEffectProjector,
)
from teksi_wastewater.hooks.adapters.tww_rights_evaluator_factory import (
    TwwRightsEvaluatorFactory,
)

from tww_hooks.evaluators.rights import (
    RightsEvaluatorFactory,
)
from teksi_wastewater.hooks.services.tww_change_creation_service import (
    ChangeFeatureProviderFactory,
    QuarantineEffectProjector,
)

CONFIG_DIR_ENV = "TEKSI_WASTEWATER_HOOK_CONFIG_DIR"
logger = logging.getLogger(__name__)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Create a tww_diff review job from an XTF file.",
    )

    parser.add_argument(
        "--job-id",
        required=True,
        help="Stable identifier for the tww_diff job.",
    )

    parser.add_argument(
        "--xtf-input",
        required=True,
        type=Path,
        help="Path to the main XTF file to import.",
    )

    parser.add_argument(
        "--provider-oid",
        required=True,
        help="Provider organisation OID used for rights evaluation.",
    )

    parser.add_argument(
        "--dataowner-oid",
        required=True,
        help="Data owner organisation OID used for rights evaluation.",
    )

    parser.add_argument(
        "--import-schema",
        default=config.IMPORT_SCHEMA,
        help="Quarantine schema for the main import.",
    )

    parser.add_argument(
        "--import-schema-ag64",
        default=None,
        help=(
            "Quarantine schema for optional AG64 adaptation import. "
            "Defaults to '<import-schema>_ag64'."
        ),
    )

    parser.add_argument(
        "--orgs-path",
        type=Path,
        default=None,
        help="Optional organisation/reference XTF.",
    )

    parser.add_argument(
        "--ag64-adaptation-path",
        type=Path,
        default=None,
        help="Optional AG64 XTF for incremental adaptation.",
    )

    parser.add_argument(
        "--rights-profile",
        default=None,
        help=(
            "Optional rights profile identifier for installations hosting "
            "multiple entities with different rights patterns."
        ),
    )

    parser.add_argument(
        "--hook-config-dir",
        type=Path,
        default=None,
        help=(
            "Optional hook configuration directory. "
            "If omitted, packaged default hook configuration is used."
        ),
    )

    args = parser.parse_args()

    import_schema_ag64 = (
        args.import_schema_ag64
        or f"{args.import_schema}_ag64"
    )

    context = HookContext(
        parameters={
            "job_id": args.job_id,
            "xtf_input": args.xtf_input,
            "provider_oid": args.provider_oid,
            "dataowner_oid": args.dataowner_oid,
            "import_schema": args.import_schema,
            "import_schema_ag64": import_schema_ag64,
            "orgs_path": args.orgs_path,
            "ag64_adaptation_path": args.ag64_adaptation_path,
            "rights_profile": args.rights_profile,
        },
        logger=logger,
        capabilities={
            QuarantineEffectProjector: TwwQuarantineEffectProjector(),
            RightsEvaluatorFactory: TwwRightsEvaluatorFactory(
                config_dir=args.hook_config_dir,
                rights_profile=args.rights_profile,
            ),
            ChangeFeatureProviderFactory: TwwChangeFeatureProviderFactory(),
        },
    )

    hook_file = (
        Path(__file__)
        .resolve()
        .parents[1]
        / "diff_exporter_hook.py"
    )

    HookHandler(
        file=hook_file,
        base_path=hook_file.parent,
    ).run(
        context,
    )

    return 0


if __name__ == "__main__":
    raise SystemExit(
        main()
    )