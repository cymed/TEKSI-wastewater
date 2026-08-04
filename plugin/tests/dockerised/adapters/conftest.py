import shutil
import subprocess
import time

import pytest


DB_HOST = "db"
DB_USER = "postgres"


@pytest.fixture(scope="session", autouse=True)
def wait_for_db():
    for _ in range(30):
        if shutil.which("docker"):
            cmd = (
                "docker compose exec db "
                "pg_isready -U postgres"
            )
        else:
            cmd = (
                f"pg_isready -h {DB_HOST} "
                f"-U {DB_USER}"
            )

        res = subprocess.run(
            cmd,
            shell=True,
        )

        if res.returncode == 0:
            return

        time.sleep(2)

    raise RuntimeError(
        "Database not ready"
    )