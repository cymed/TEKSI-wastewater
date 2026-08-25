# dockerised/adapters/test_diff_exporter_cli.py

from pathlib import Path

from ..helpers import run_cli

from teksi_wastewater.interlis import config
from teksi_wastewater.utils.database_utils import DatabaseUtils


DATA_DIR = (
    Path(__file__).parent
    / "data"
)
CONFIG_DIR = (
    Path(__file__).parent
    / "config"
)

DBW_WI="ch080qwzPR000017"
DBW_GEP="ch080qwzPR000020"
FI_BU="ch080qwzGE000001"
PROVIDERS = (
    FI_BU,
    DBW_GEP,
    DBW_WI,
)
DATAOWNER_OID="ch080qwzPR000018"

DB_ARGS = (
    "--pghost db " "--pgdatabase tww " "--pguser postgres " "--pgpass postgres " "--pgport 5432"
)

ORGS_XTF = (
    DATA_DIR
    / "test-dataset-organisations.xtf"
)

def run_import_cli(
    job_id: str,
    job_mode: str,
    xtf_file: Path,
    provider_oid:str,
    dataowner_oid:str,
    incremental_xtf: Path,
) -> None:
    run_cli(
        "diff-exporter",
        "--job-id",
        job_id,
        "--job-mode",
        job_mode,
        "--xtf-input",
        str(xtf_file),
        "--provider-oid",
        provider_oid,
        "--dataowner-oid",
        dataowner_oid,
        "--orgs-path",
        str(ORGS_XTF),
        "--incremental-xtf",
        str(incremental_xtf),
        "--incremental-import-schema",
        "xtf_agxx",
        "--rights-profile",
        "CI",
        "--hook-config-dir",
        str(
            CONFIG_DIR,
        ),
    )

def assert_job_created(
    job_id: str,
) -> None:
    rows = DatabaseUtils.execute_fetchall(
        """
        SELECT
            id,
            job_id,
            job_status,
            validation_success
        FROM tww_diff.metadata
        WHERE job_id = %s
        """,
        (
            job_id,
        ),
    )

    assert len(rows) == 1

    job = rows[0]

    assert job["job_id"] == job_id
    assert job["job_status"] == "pending"
    assert job["validation_success"] is True

    total_count, _ = _diff_counts(
        job_id,
    )

    assert total_count > 0

def import_run(allowed_provider: str, xtf_phase_identifier: str):
    ordered_providers = [
        provider
        for provider in PROVIDERS
        if provider != allowed_provider
    ]

    ordered_providers.append(
        allowed_provider
    )
    for provider in ordered_providers:
        job_id = f"c{xtf_phase_identifier}-job_{provider}"
        xtf_file = (
            DATA_DIR
            / f"test_{xtf_phase_identifier}_DSS_2020_1_LV95.xtf"
        )

        incremental_xtf = (
            DATA_DIR
            / f"test_{xtf_phase_identifier}_Genereller_Entwaesserungsplan_AG.xtf"
        )

        assert xtf_file.is_file(), (
            f"Missing test fixture: {xtf_file}"
        )

        assert incremental_xtf.is_file(), (
            f"Missing test fixture: {incremental_xtf}"
        )

        run_import_cli(
            job_id=job_id,
            job_mode="create",
            xtf_file=xtf_file,
            provider_oid=provider,
            dataowner_oid=DATAOWNER_OID,
            incremental_xtf=incremental_xtf
        )
        if provider != allowed_provider:
            assert_update_forbidden(job_id)
            reject_update(job_id)
        else:
            assert_update_allowed(job_id)
            persist_update(job_id)

def import_baseline():

    run_cli(
        "interlis_import "
        f"--xtf_file {DATA_DIR}/test-dataset-organisations.xtf "
        f"{DB_ARGS}"
    )

    run_cli(
        "interlis_import "
        f"--xtf_file {DATA_DIR}/test_baseline_import_DSS_2020_1_LV95.xtf "
        f"{DB_ARGS}"
    )

    run_cli(
        "interlis_import "
        f"--xtf_file {DATA_DIR}/test_baseline_Genereller_Entwaesserungsplan_AG.xtf "
        "--schema 'xtf_agxx' "
        f"{DB_ARGS}"
    )

def _diff_counts(
    job_id: str,
) -> tuple[int, int]:
    """
    Return total and rejected diff-row counts for a review job.
    """

    metadata_rows = DatabaseUtils.execute_fetchall(
        """
        SELECT id
        FROM tww_diff.metadata
        WHERE job_id = %s
        """,
        (
            job_id,
        ),
    )

    assert len(metadata_rows) == 1, (
        f"Expected exactly one metadata row for job {job_id!r}, "
        f"found {len(metadata_rows)}."
    )

    job_db_id = metadata_rows[0][
        "id"
    ]

    table_rows = DatabaseUtils.execute_fetchall(
        """
        SELECT table_name
        FROM information_schema.columns
        WHERE table_schema = 'tww_diff'
        GROUP BY table_name
        HAVING bool_or(
            column_name = 'job_id'
        )
        AND bool_or(
            column_name = 'is_rejected'
        )
        ORDER BY table_name
        """
    )

    total_count = 0
    rejected_count = 0

    for table_row in table_rows:
        table_name = table_row[
            "table_name"
        ]

        quoted_table_name = (
            '"'
            + table_name.replace(
                '"',
                '""',
            )
            + '"'
        )

        counts = DatabaseUtils.execute_fetchall(
            f"""
            SELECT
                count(*) AS total_count,
                count(*) FILTER (
                    WHERE is_rejected
                ) AS rejected_count
            FROM tww_diff.{quoted_table_name}
            WHERE job_id = %s
            """,
            (
                job_db_id,
            ),
        )[0]

        total_count += counts[
            "total_count"
        ]

        rejected_count += counts[
            "rejected_count"
        ]

    return (
        total_count,
        rejected_count,
    )

def assert_update_forbidden(
    job_id: str,
) -> None:
    """
    Assert that a job contains at least one rejected diff row.
    """

    total_count, rejected_count = _diff_counts(
        job_id,
    )

    assert total_count > 0, (
        f"Expected forbidden job {job_id!r} to contain changes, "
        "but no diff rows were created."
    )

    assert rejected_count > 0, (
        f"Expected job {job_id!r} to contain rejected changes, "
        f"but all {total_count} rows were permitted."
    )

def assert_update_allowed(
    job_id: str,
) -> None:
    """
    Assert that a job contains changes without rejected rows.
    """

    total_count, rejected_count = _diff_counts(
        job_id,
    )

    assert total_count > 0, (
        f"Expected permitted job {job_id!r} to contain changes, "
        "but no diff rows were created."
    )

    assert rejected_count == 0, (
        f"Expected job {job_id!r} to be fully permitted, "
        f"but {rejected_count} of {total_count} rows were rejected."
    )

def reject_update(
    job_id: str,
) -> None:
    """
    Reject a pending review job without changing live data.

    Assumes that fct_reject_diff_job will become the public entry point for
    rejecting a review job.
    """

    DatabaseUtils.execute_fetchall(
        """
        SELECT tww_app.fct_reject_diff_job(
            %s
        )
        """,
        (
            job_id,
        ),
    )

    rows = DatabaseUtils.execute_fetchall(
        f"""
        SELECT status
        FROM {config.EXPORT_SCHEMA}.review_job
        WHERE job_id = %s
        """,
        (
            job_id,
        ),
    )

    assert len(rows) == 1, (
        f"Expected one review job for {job_id!r}, "
        f"found {len(rows)}."
    )

    assert rows[0]["status"] == "rejected", (
        f"Expected job {job_id!r} to be rejected, "
        f"got status {rows[0]['status']!r}."
    )

def persist_update(
    job_id: str,
) -> None:
    """
    Apply a fully permitted review job to live data.

    Assumes that fct_apply_diff_job validates and applies the complete job in
    one transaction, then sets its status to applied.
    """

    total_count, rejected_count = _diff_counts(
        job_id,
    )

    assert total_count > 0, (
        f"Cannot apply empty job {job_id!r}."
    )
    assert rejected_count == 0, (
        f"Cannot apply job {job_id!r}: "
        f"{rejected_count} diff rows are rejected."
    )

    DatabaseUtils.execute_fetchall(
        """
        SELECT tww_app.fct_apply_diff_job(
            %s
        )
        """,
        (
            job_id,
        ),
    )

    rows = DatabaseUtils.execute_fetchall(
        f"""
        SELECT status
        FROM {config.EXPORT_SCHEMA}.review_job
        WHERE job_id = %s
        """,
        (
            job_id,
        ),
    )

    assert len(rows) == 1

    assert rows[0]["status"] == "applied"
 
def test_diff_import_workflow(
    clean_db_once,
) -> None:
    import_baseline()

    import_run(
        allowed_provider=DBW_WI,
        xtf_phase_identifier="phase1_dbw_wi",
    )

    import_run(
        allowed_provider=DBW_GEP,
        xtf_phase_identifier="phase2_dbw_gep",
    )

    import_run(
        allowed_provider=FI_BU,
        xtf_phase_identifier="phase3_fi_bu",
    )