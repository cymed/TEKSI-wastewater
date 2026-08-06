import pytest

from teksi_wastewater.hooks.services.tww_diff_schema_service import (
    TwwDiffSchemaService,
)
from tww_hooks.models.review import (
    ReviewFeature,
)


pytestmark = pytest.mark.no_qgis


JOB_ID = "pytest_tww_diff_schema_service"


def test_tww_diff_schema_service_writes_metadata_and_class_row(
    clean_db_once,
) -> None:
    class_id = _first_available_diff_class()

    service = TwwDiffSchemaService()

    feature = ReviewFeature(
        class_id=class_id,
        object_id="pytest_obj_001",
        attributes={
            "is_created": True,
            "is_altered": False,
            "is_deleted": False,
            "import_values": {
                "obj_id": "pytest_obj_001",
                "status": "imported",
            },
            "canonical_values": {
                "obj_id": "pytest_obj_001",
                "status": "imported",
            },
            "changed_attributes": [
                {
                    "attribute_name": "status",
                    "old_value": None,
                    "new_value": "imported",
                },
            ],
            "unpermitted_values": {},
            "permission_findings": [],
            "validation_findings": [],
        },
        geometries={},
    )

    result = service.write(
        job_id=JOB_ID,
        features_by_class={
            class_id: [
                feature,
            ],
        },
        metadata={
            "source_model": "pytest_model",
            "source_file": "pytest.xtf",
            "import_schema": "tww_import",
            "live_schema": "tww_od",
        },
        validation_success=True,
        job_status="pending",
        reset_job=True,
    )

    assert result.job_id == JOB_ID
    assert result.row_count == 1

    metadata = _fetchone_dict(
        """
        SELECT
            id,
            job_id,
            job_status,
            validation_success,
            source_model,
            source_file,
            import_schema,
            live_schema
        FROM tww_diff.metadata
        WHERE job_id = %s
        """,
        (
            JOB_ID,
        ),
    )

    assert metadata is not None
    assert metadata["id"] == result.job_db_id
    assert metadata["job_id"] == JOB_ID
    assert metadata["job_status"] == "pending"
    assert metadata["validation_success"] is True
    assert metadata["source_model"] == "pytest_model"
    assert metadata["source_file"] == "pytest.xtf"
    assert metadata["import_schema"] == "tww_import"
    assert metadata["live_schema"] == "tww_od"

    row = _fetchone_dict(
        f"""
        SELECT
            job_id,
            obj_id,
            is_created,
            is_altered,
            is_deleted,
            is_rejected,
            import_values,
            canonical_values,
            changed_attributes,
            unpermitted_values,
            permission_findings,
            validation_findings
        FROM tww_diff.{_quote_identifier(class_id)}
        WHERE job_id = %s
          AND obj_id = %s
        """,
        (
            result.job_db_id,
            "pytest_obj_001",
        ),
    )

    assert row is not None
    assert row["job_id"] == result.job_db_id
    assert row["obj_id"] == "pytest_obj_001"
    assert row["is_created"] is True
    assert row["is_altered"] is False
    assert row["is_deleted"] is False
    assert row["is_rejected"] is False

    assert row["import_values"]["status"] == "imported"
    assert row["canonical_values"]["status"] == "imported"

    assert row["changed_attributes"] == [
        {
            "attribute_name": "status",
            "old_value": None,
            "new_value": "imported",
        },
    ]

    assert row["unpermitted_values"] == {}
    assert row["permission_findings"] == []
    assert row["validation_findings"] == []


def test_tww_diff_schema_service_sets_is_rejected_from_findings(
    clean_db_once,
) -> None:
    class_id = _first_available_diff_class()

    service = TwwDiffSchemaService()

    feature = ReviewFeature(
        class_id=class_id,
        object_id="pytest_obj_rejected",
        attributes={
            "is_created": False,
            "is_altered": True,
            "is_deleted": False,
            "import_values": {
                "status": "bad_status",
            },
            "canonical_values": {
                "status": "old_status",
            },
            "changed_attributes": [
                {
                    "attribute_name": "status",
                    "old_value": "old_status",
                    "new_value": "bad_status",
                },
            ],
            "unpermitted_values": {
                "status": "bad_status",
            },
            "permission_findings": [
                {
                    "code": "permission_denied",
                    "severity": "error",
                    "message": "Change is not permitted.",
                    "attribute_name": "status",
                },
            ],
            "validation_findings": [],
        },
        geometries={},
    )

    result = service.write(
        job_id=f"{JOB_ID}_rejected",
        features_by_class={
            class_id: [
                feature,
            ],
        },
        metadata={
            "source_model": "pytest_model",
        },
        validation_success=False,
        job_status="pending",
        reset_job=True,
    )

    row = _fetchone_dict(
        f"""
        SELECT
            is_rejected,
            unpermitted_values,
            permission_findings,
            validation_findings
        FROM tww_diff.{_quote_identifier(class_id)}
        WHERE job_id = %s
          AND obj_id = %s
        """,
        (
            result.job_db_id,
            "pytest_obj_rejected",
        ),
    )

    assert row is not None
    assert row["is_rejected"] is True
    assert row["unpermitted_values"] == {
        "status": "bad_status",
    }
    assert row["permission_findings"][0]["code"] == "permission_denied"
    assert row["validation_findings"] == []


def test_tww_diff_schema_service_reset_job_replaces_existing_rows(
    clean_db_once,
) -> None:
    class_id = _first_available_diff_class()

    service = TwwDiffSchemaService()

    first_feature = ReviewFeature(
        class_id=class_id,
        object_id="pytest_obj_before_reset",
        attributes={
            "is_created": True,
            "import_values": {
                "obj_id": "pytest_obj_before_reset",
            },
            "canonical_values": {
                "obj_id": "pytest_obj_before_reset",
            },
            "changed_attributes": [],
            "unpermitted_values": {},
            "permission_findings": [],
            "validation_findings": [],
        },
        geometries={},
    )

    service.write(
        job_id=f"{JOB_ID}_reset",
        features_by_class={
            class_id: [
                first_feature,
            ],
        },
        reset_job=True,
    )

    second_feature = ReviewFeature(
        class_id=class_id,
        object_id="pytest_obj_after_reset",
        attributes={
            "is_created": True,
            "import_values": {
                "obj_id": "pytest_obj_after_reset",
            },
            "canonical_values": {
                "obj_id": "pytest_obj_after_reset",
            },
            "changed_attributes": [],
            "unpermitted_values": {},
            "permission_findings": [],
            "validation_findings": [],
        },
        geometries={},
    )

    result = service.write(
        job_id=f"{JOB_ID}_reset",
        features_by_class={
            class_id: [
                second_feature,
            ],
        },
        reset_job=True,
    )

    rows = _fetchall_dict(
        f"""
        SELECT
            obj_id
        FROM tww_diff.{_quote_identifier(class_id)}
        WHERE job_id = %s
        ORDER BY obj_id
        """,
        (
            result.job_db_id,
        ),
    )

    assert rows == [
        {
            "obj_id": "pytest_obj_after_reset",
        },
    ]


def _first_available_diff_class() -> str:
    row = _fetchone_dict(
        """
        SELECT
            t.tablename
        FROM tww_sys.dictionary_od_table t
        JOIN information_schema.tables tbl
          ON tbl.table_schema = 'tww_diff'
         AND tbl.table_name = t.tablename
        ORDER BY
            t.tablename
        LIMIT 1
        """,
        (),
    )

    assert row is not None, (
        "No tww_diff class table found. "
        "Ensure the tww_diff changelog has been applied."
    )

    return row["tablename"]


def _fetchone_dict(
    query: str,
    params,
):
    rows = _fetchall_dict(
        query,
        params,
    )

    if not rows:
        return None

    return rows[0]


def _fetchall_dict(
    query: str,
    params,
) -> list[
    dict,
]:
    from teksi_wastewater.utils.database_utils import (
        DatabaseUtils,
    )

    with DatabaseUtils.PsycopgConnection() as connection:
        cursor = connection.cursor()

        cursor.execute(
            query,
            params,
        )

        rows = cursor.fetchall()

        column_names = [
            column[0]
            for column in cursor.description
        ]

    return [
        dict(
            zip(
                column_names,
                row,
            )
        )
        for row in rows
    ]


def _quote_identifier(
    value: str,
) -> str:
    return (
        '"'
        + value.replace(
            '"',
            '""',
        )
        + '"'
    )