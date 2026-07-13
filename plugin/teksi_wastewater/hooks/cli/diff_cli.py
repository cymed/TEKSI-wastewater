
import argparse
import logging
from pathlib import Path

from teksi_hooks.hook import HookContext, HookHandler

from teksi_wastewater.interlis.twwinterlisservice import (
    InterlisCapability,
    TWWInterlisService,
)

logger = logging.getLogger(__name__)


def main() -> int:
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--xtf-input",
        required=True,
        help="Path to the XTF file to import.",
    )


    args = parser.parse_args()

    context = HookContext(
        parameters={
            "xtf_input": Path(args.xtf_input),
        },
        logger=logger,
        capabilities={
            InterlisCapability: InterlisCapability(
                service=TWWInterlisService(
                    to_quarantine_only=True,
                ),
            ),
        },
    )

    HookHandler(
        file=Path(__file__).parent / "hook.py",
    ).run(
        context,
    )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
