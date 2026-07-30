from pathlib import Path

import pytest

from teksi_wastewater.hooks_adapters.tww_interlis_service_adapter import (
    TwwInterlisServiceAdapter,
)
from teksi_wastewater.hooks_adapters.tww_quarantine_runner import (
    TwwQuarantineRunner,
)
from teksi_wastewater.hooks_adapters.tww_relation_lookup_adapter import (
    TwwRelationLookupAdapter,
)

from pathlib import Path

import pytest

from teksi_wastewater.interlis import config
from teksi_wastewater.utils.database_utils import DatabaseUtils

pytestmark = pytest.mark.no_qgis


@pytest.fixture
def quarantine_runner() -> TwwQuarantineRunner:
    return TwwQuarantineRunner(
        interlis_service=TwwInterlisServiceAdapter(),
    )


DATA_DIR = Path(
    "/usr/src/plugin/tests/qgis/data",
)

OUTPUT_DIR = Path(
    "/usr/src/plugin/tests/adapter/output",
)


def test_quarantine_runner_imports_xtf_to_import_schema(
    clean_db_once,
    quarantine_runner,
) -> None:
    quarantine_runner.import_xtf_to_quarantine(
        DATA_DIR / "minimal-dataset-organisation.xtf",
    )
    quarantine_runner.import_xtf_to_quarantine(
        DATA_DIR / "minimal-dataset-SIA405-ABWASSER.xtf",
    )

    result = DatabaseUtils.fetchone(
        "SELECT obj_id "
        f"FROM {config.IMPORT_SCHEMA}.reach "
        "WHERE obj_id='ch000000RE000001';"
    )

    assert result is not None
    assert result[0] == "ch000000RE000001"




def test_tww_relation_lookup_adapter_finds_reach_from_reach_point(
    clean_db_once,
    quarantine_runner,
) -> None:
    quarantine_runner.import_xtf_to_quarantine(
        DATA_DIR / "minimal-dataset-SIA405-ABWASSER.xtf",
    )

    lookup = TwwRelationLookupAdapter(
        schema=config.IMPORT_SCHEMA,
    )

    objects = lookup.canonical_objects(
        local_class_id="reach_point",
        related_class_id="reach",
        local_attribute="obj_id",
        related_attribute="fk_reach_point_from",
        value="ch000000RP000001",
    )

    assert objects

    assert (
        objects[0].class_id
        == "reach"
    )

def test_quarantine_runner_validates_import_schema(
    clean_db_once,
    quarantine_runner,
) -> None:
    quarantine_runner.import_xtf_to_quarantine(
        DATA_DIR / "minimal-dataset-SIA405-ABWASSER.xtf",
    )

    findings = quarantine_runner.validate_quarantine(
        models=(
            config.MODEL_NAME_SIA405_ABWASSER,
        ),
        log_path=OUTPUT_DIR / "validate_quarantine.log",
        srid=2056,
    )

    assert findings == ()
