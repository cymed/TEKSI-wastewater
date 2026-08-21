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
CONFIG_DIR = (
    Path(__file__).parent
    / "config"
)


def test_diff_exporter_creates_review_job(
    clean_db_once,
):
    job_id = "test-diff-job"
    job_mode = "create"
    xtf_file = (
        DATA_DIR
        / "minimal-dataset.xtf"
    )

    orgs_file = (
        DATA_DIR
        / "minimal-dataset-organisation-arbon-only.xtf"
    )

    incremental_xtf = (
        DATA_DIR
        / "minimal-dataset-organisation-arbon-only_ag64.xtf"
    )
    incremental_import_schema = "xtf_agxx"

    run_cli(
        (
            "diff-exporter "
            f"--job-id {job_id} "
            f"--job_mode {job_mode} "
            f"--xtf-input {xtf_file} "
            "--provider-oid ch:1 "
            "--dataowner-oid ch:1 "
            f"--orgs-path {orgs_file}"
            f"--incremental-xtf {incremental_xtf}"
            f"--incremental-import-schema {incremental_import_schema}"
            "--rights_profile CI"
            f"--hook_config_dir {CONFIG_DIR}"
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