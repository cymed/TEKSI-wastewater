from pathlib import Path

import pytest

from teksi_wastewater.hooks_adapters.tww_interlis_service_adapter import (
    TwwInterlisContext,
)
from teksi_wastewater.hooks_adapters.tww_quarantine_runner import (
    TwwQuarantineRunner,
)
from teksi_wastewater.hooks_adapters.tww_relation_lookup_adapter import (
    TwwRelationLookupAdapter,
)
from teksi_wastewater.interlis import config
from teksi_wastewater.utils.database_utils import (
    DatabaseUtils,
)


pytestmark = pytest.mark.no_qgis


DATA_DIR = Path(
    "/usr/src/plugin/tests/qgis/data",
)

OUTPUT_DIR = Path(
    "/usr/src/plugin/tests/dockerised/adapters/output",
)

OUTPUT_DIR.mkdir(
    parents=True,
    exist_ok=True,
)


@pytest.fixture
def quarantine_runner() -> TwwQuarantineRunner:
    return TwwQuarantineRunner()


@pytest.fixture
def interlis_context() -> TwwInterlisContext:
    return TwwInterlisContext(
        schema=config.IMPORT_SCHEMA,
        srid=2056,
        logs_next_to_file=True,
        filter_nulls=True,
    )


@pytest.fixture
def imported_sia405_to_quarantine(
    clean_db_once,
    quarantine_runner,
    interlis_context,
) -> tuple[
    str,
    tuple[str, ...],
]:
    quarantine_runner.import_xtf_to_quarantine(
        xtf_file=DATA_DIR / "minimal-dataset-organisation.xtf",
        context=interlis_context,
    )

    return quarantine_runner.import_xtf_to_quarantine(
        xtf_file=DATA_DIR / "minimal-dataset-SIA405-ABWASSER.xtf",
        context=interlis_context,
    )


def test_quarantine_runner_imports_xtf_to_import_schema(
    imported_sia405_to_quarantine,
) -> None:
    result = DatabaseUtils.fetchone(
        "SELECT obj_id "
        f"FROM {config.IMPORT_SCHEMA}.reach "
        "WHERE obj_id='ch000000RE000001';"
    )

    assert result is not None
    assert result[0] == "ch000000RE000001"


def test_tww_relation_lookup_adapter_finds_reach_from_reach_point(
    imported_sia405_to_quarantine,
) -> None:
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

    assert any(
        obj.class_id == "reach"
        for obj in objects
    )


def test_quarantine_runner_validates_import_schema(
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