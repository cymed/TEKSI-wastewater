# dockerised/adapters/test_diff_exporter_cli.py

from pathlib import Path

from ..helpers import run_cli

from teksi_wastewater.interlis import config
from teksi_wastewater.utils.database_utils import DatabaseUtils


DATA_DIR = (
    Path(__file__).parents[1]
    / "qgis"
    / "data"
)


def test_diff_exporter_creates_review_job(
    clean_db_once,
):
    job_id = "test-diff-job"

    xtf_file = (
        DATA_DIR
        / "minimal-dataset.xtf"
    )

    orgs_file = (
        DATA_DIR
        / "minimal-dataset-organisation-arbon-only.xtf"
    )

    run_cli(
        (
            "diff-exporter "
            f"--job-id {job_id} "
            f"--xtf-input {xtf_file} "
            "--provider-oid ch:1 "
            "--dataowner-oid ch:1 "
            f"--orgs-path {orgs_file}"
        )
    )

    rows = DatabaseUtils.execute_fetchall(
        f"""
        SELECT *
        FROM {config.EXPORT_SCHEMA}.review_job
        WHERE job_id = %s
        """,
        (job_id,),
    )

    assert len(rows) == 1

    job = rows[0]

    assert job["job_id"] == job_id
    assert job["status"] == "pending"

    rows = DatabaseUtils.execute_fetchall(
        """
        SELECT COUNT(*)
        FROM tww_diff.metadata
        WHERE job_id = %s
        """,
        (job_id,),
    )

    assert rows[0]["count"] == 1

    rows = DatabaseUtils.execute_fetchall(
        """
        SELECT COUNT(*)
        FROM tww_diff.wastewater_structure
        WHERE job_id = (
            SELECT id
            FROM tww_diff.metadata
            WHERE job_id = %s
        )
        """,
        (job_id,),
    )

    assert rows[0]["count"] > 0