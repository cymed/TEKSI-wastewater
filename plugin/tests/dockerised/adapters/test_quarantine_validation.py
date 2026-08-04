from pathlib import Path

import pytest

from teksi_wastewater.hooks.adapters.tww_quarantine_runner import (
    TwwQuarantineRunner,
)
from teksi_wastewater.interlis import config


pytestmark = [
    pytest.mark.no_qgis,
    pytest.mark.integration,
]


DATA_DIR = (
    Path(__file__)
    .parents[2]
    / "qgis"
    / "data"
)

OUTPUT_DIR = (
    Path(__file__)
    .parent
    / "output"
)

OUTPUT_DIR.mkdir(
    parents=True,
    exist_ok=True,
)


@pytest.fixture(scope="module")
def imported_sia405_to_quarantine(
    clean_db_once,
    quarantine_runner,
    interlis_context
) -> None:

    quarantine_runner.import_xtf_to_quarantine(
        DATA_DIR / "minimal-dataset-organisation-arbon-only.xtf",
        context=interlis_context,
    )

    return quarantine_runner.import_xtf_to_quarantine(
        DATA_DIR / "minimal-dataset-SIA405-ABWASSER.xtf",
        context=interlis_context,
    )


def test_quarantine_runner_validates_quarantine_schema(
    imported_sia405_to_quarantine,
    quarantine_runner,
    interlis_context,
) -> None:
    import_model, _ = imported_sia405_to_quarantine

    findings = quarantine_runner.validate_quarantine(
        model_names=(
            import_model,
        ),
        log_path=OUTPUT_DIR / "validate_quarantine.log",
        srid=interlis_context.srid,
        schema=config.IMPORT_SCHEMA,
    )
    assert findings == ()


def test_quarantine_runner_validate_or_raise_accepts_valid_quarantine(
    imported_sia405_to_quarantine,
) -> None:
    runner = TwwQuarantineRunner()

    runner.validate_quarantine_or_raise(
        models=(
            config.MODEL_NAME_SIA405_ABWASSER,
        ),
        log_path=(
            OUTPUT_DIR
            / "validate_quarantine_or_raise_sia405.log"
        ),
        srid=2056,
    )