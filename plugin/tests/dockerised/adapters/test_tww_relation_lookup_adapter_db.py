from pathlib import Path

import pytest

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
from tww_hooks.models.canonical_object import (
    CanonicalObjectIdentity,
)


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


@pytest.fixture(scope="module")
def imported_sia405_to_quarantine(
    clean_db_once,
) -> None:
    runner = TwwQuarantineRunner()

    runner.import_xtf_to_quarantine(
        DATA_DIR / "minimal-dataset-organisation-arbon-only.xtf",
    )

    runner.import_xtf_to_quarantine(
        DATA_DIR / "minimal-dataset-SIA405-ABWASSER.xtf",
    )


def test_tww_relation_lookup_adapter_finds_reach_from_reach_point(
    imported_sia405_to_quarantine,
) -> None:
    row = DatabaseUtils.fetchone(
        "SELECT obj_id, fk_reach_point_from "
        f"FROM {config.IMPORT_SCHEMA}.reach "
        "WHERE fk_reach_point_from IS NOT NULL "
        "LIMIT 1;"
    )

    assert row is not None

    reach_obj_id = row[0]
    reach_point_obj_id = row[1]

    lookup = TwwRelationLookupAdapter(
        schema=config.IMPORT_SCHEMA,
    )

    objects = lookup.canonical_objects(
        local_class_id="reach_point",
        related_class_id="reach",
        local_attribute="obj_id",
        related_attribute="fk_reach_point_from",
        value=reach_point_obj_id,
    )

    assert len(
        objects,
    ) >= 1

    assert any(
        obj.class_id == "reach"
        and obj.attributes == {
            "obj_id": reach_obj_id,
        }
        for obj in objects
    )


def test_tww_relation_lookup_adapter_loads_current_object(
    imported_sia405_to_quarantine,
) -> None:
    row = DatabaseUtils.fetchone(
        "SELECT obj_id "
        f"FROM {config.IMPORT_SCHEMA}.reach "
        "LIMIT 1;"
    )

    assert row is not None

    reach_obj_id = row[0]

    lookup = TwwRelationLookupAdapter(
        schema=config.IMPORT_SCHEMA,
    )

    current = lookup.current_object(
        CanonicalObjectIdentity(
            class_id="reach",
            attributes={
                "obj_id": reach_obj_id,
            },
        )
    )

    assert current is not None

    assert (
        current.identity.class_id
        == "reach"
    )

    assert current.identity.attributes == {
        "obj_id": reach_obj_id,
    }

    assert (
        "obj_id"
        not in current.values
    )


def test_tww_relation_lookup_adapter_finds_wastewater_structure_from_networkelement(
    imported_sia405_to_quarantine,
) -> None:
    row = DatabaseUtils.fetchone(
        "SELECT obj_id, fk_wastewater_structure "
        f"FROM {config.IMPORT_SCHEMA}.wastewater_networkelement "
        "WHERE fk_wastewater_structure IS NOT NULL "
        "LIMIT 1;"
    )

    assert row is not None

    networkelement_obj_id = row[0]
    wastewater_structure_obj_id = row[1]

    lookup = TwwRelationLookupAdapter(
        schema=config.IMPORT_SCHEMA,
    )

    objects = lookup.canonical_objects(
        local_class_id="wastewater_networkelement",
        related_class_id="wastewater_structure",
        local_attribute="fk_wastewater_structure",
        related_attribute="obj_id",
        value=wastewater_structure_obj_id,
    )

    assert len(
        objects,
    ) >= 1

    assert any(
        obj.class_id == "wastewater_structure"
        and obj.attributes == {
            "obj_id": wastewater_structure_obj_id,
        }
        for obj in objects
    )

    assert networkelement_obj_id is not None