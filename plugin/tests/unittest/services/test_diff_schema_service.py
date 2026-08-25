from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from enum import StrEnum
from typing import Any

import pytest

from teksi_hooks.models.review import (
    ReviewFeature,
)

from teksi_wastewater.hooks.services.tww_diff_schema_service import (
    TwwDiffSchemaService,
)
from teksi_wastewater.utils.database_utils import (
    DatabaseUtils,
)


class FakeCursor:
    def __init__(
        self,
        *,
        table_columns: set[str] | None = None,
        metadata_id: int = 101,
    ) -> None:
        self.table_columns = table_columns or set()
        self.metadata_id = metadata_id
        self.executed: list[
            tuple[
                str,
                tuple[Any, ...] | None,
            ]
        ] = []
        self._last_query = ""

    def execute(
        self,
        query,
        parameters=None,
    ) -> None:
        query_text = str(
            query,
        )

        self._last_query = query_text

        self.executed.append(
            (
                query_text,
                parameters,
            )
        )

    def fetchone(
        self,
    ):
        return (
            self.metadata_id,
        )

    def fetchall(
        self,
    ):
        if "information_schema.columns" in self._last_query:
            return [
                (
                    column_name,
                )
                for column_name in sorted(
                    self.table_columns,
                )
            ]

        return []


class FakeConnection:
    def __init__(
        self,
        cursor: FakeCursor,
    ) -> None:
        self._cursor = cursor
        self.committed = False
        self.closed = False

    def cursor(
        self,
    ) -> FakeCursor:
        return self._cursor

    def commit(
        self,
    ) -> None:
        self.committed = True

    def close(
        self,
    ) -> None:
        self.closed = True


class FakeConnectionContext:
    def __init__(
        self,
        connection: FakeConnection,
    ) -> None:
        self.connection = connection

    def __enter__(
        self,
    ) -> FakeConnection:
        return self.connection

    def __exit__(
        self,
        exc_type,
        exc_val,
        exc_tb,
    ) -> None:
        self.connection.close()


class ExampleStatus(
    StrEnum,
):
    ACTIVE = "active"


@dataclass
class ExamplePayload:
    value: str


class GeometryWithAsWkt:
    def asWkt(
        self,
    ) -> str:
        return "POINT(1 2)"


class GeometryWithExportToWkt:
    def ExportToWkt(
        self,
    ) -> str:
        return "POINT(3 4)"


class GeometryWithWkt:
    wkt = "POINT(5 6)"


def test_diff_schema_service_base_column_values() -> None:
    service = TwwDiffSchemaService()

    feature = ReviewFeature(
        class_id="reach",
        object_id="ch000000re000001",
        attributes={
            "is_created": False,
            "is_altered": True,
            "is_deleted": False,
            "import_values": {
                "status": "new",
            },
            "canonical_values": {
                "status": "old",
            },
            "changed_attributes": (
                {
                    "attribute_name": "status",
                },
            ),
            "unpermitted_values": {},
            "permission_findings": (),
            "validation_findings": (),
        },
    )

    values = service._base_column_values(
        job_db_id=42,
        feature=feature,
    )

    assert values == {
        "job_id": 42,
        "obj_id": "ch000000re000001",
        "is_created": False,
        "is_altered": True,
        "is_deleted": False,
        "import_values": {
            "status": "new",
        },
        "canonical_values": {
            "status": "old",
        },
        "changed_attributes": (
            {
                "attribute_name": "status",
            },
        ),
        "unpermitted_values": {},
        "permission_findings": (),
        "validation_findings": (),
    }


def test_diff_schema_service_base_column_values_defaults() -> None:
    service = TwwDiffSchemaService()

    feature = ReviewFeature(
        class_id="reach",
        object_id="ch000000re000001",
        attributes={},
    )

    values = service._base_column_values(
        job_db_id=42,
        feature=feature,
    )

    assert values["is_created"] is False
    assert values["is_altered"] is False
    assert values["is_deleted"] is False
    assert values["import_values"] == {}
    assert values["canonical_values"] == {}
    assert values["changed_attributes"] == ()
    assert values["unpermitted_values"] == {}
    assert values["permission_findings"] == ()
    assert values["validation_findings"] == ()


def test_diff_schema_service_extra_column_values_filters_reserved_columns() -> None:
    service = TwwDiffSchemaService()

    feature = ReviewFeature(
        class_id="reach",
        object_id="ch000000re000001",
        attributes={
            "obj_id": "should_not_be_extra",
            "status": "active",
            "custom_flag": True,
            "created_at": "should_not_be_extra",
            "ignored_column": "not in table",
        },
    )

    values = service._extra_column_values(
        feature=feature,
        table_columns={
            "obj_id",
            "status",
            "custom_flag",
            "created_at",
        },
    )

    assert values == {
        "status": "active",
        "custom_flag": True,
    }


def test_diff_schema_service_value_expression_uses_jsonb_for_json_columns() -> None:
    service = TwwDiffSchemaService()

    expression, parameters = service._value_expression(
        column_name="import_values",
        value={
            "status": "active",
        },
    )

    assert expression == "%s::jsonb"
    assert parameters == [
        '{"status": "active"}',
    ]


def test_diff_schema_service_value_expression_uses_plain_parameter_for_normal_columns() -> None:
    service = TwwDiffSchemaService()

    expression, parameters = service._value_expression(
        column_name="status",
        value="active",
    )

    assert expression == "%s"
    assert parameters == [
        "active",
    ]


def test_diff_schema_service_geometry_expression_for_none() -> None:
    service = TwwDiffSchemaService()

    expression, parameters = service._geometry_expression(
        None,
    )

    assert expression == "%s"
    assert parameters == [
        None,
    ]


def test_diff_schema_service_geometry_expression_for_wkb() -> None:
    service = TwwDiffSchemaService(
        srid=2056,
    )

    expression, parameters = service._geometry_expression(
        b"fake-wkb",
    )

    assert expression == "ST_GeomFromWKB(%s, %s)"
    assert parameters == [
        b"fake-wkb",
        2056,
    ]


def test_diff_schema_service_geometry_expression_for_wkt() -> None:
    service = TwwDiffSchemaService(
        srid=2056,
    )

    expression, parameters = service._geometry_expression(
        "POINT(1 2)",
    )

    assert expression == "ST_GeomFromText(%s, %s)"
    assert parameters == [
        "POINT(1 2)",
        2056,
    ]


def test_diff_schema_service_geometry_to_wkt() -> None:
    service = TwwDiffSchemaService()

    assert service._geometry_to_wkt(
        None,
    ) is None

    assert service._geometry_to_wkt(
        GeometryWithAsWkt(),
    ) == "POINT(1 2)"

    assert service._geometry_to_wkt(
        GeometryWithExportToWkt(),
    ) == "POINT(3 4)"

    assert service._geometry_to_wkt(
        GeometryWithWkt(),
    ) == "POINT(5 6)"

    assert service._geometry_to_wkt(
        "POINT(7 8)",
    ) == "POINT(7 8)"

    assert service._geometry_to_wkt(
        object(),
    ) is None


def test_diff_schema_service_database_value_conversions() -> None:
    service = TwwDiffSchemaService()

    assert service._database_value(
        date(
            2026,
            1,
            2,
        )
    ) == "2026-01-02"

    assert service._database_value(
        datetime(
            2026,
            1,
            2,
            3,
            4,
            5,
        )
    ) == "2026-01-02T03:04:05"

    assert service._database_value(
        ExampleStatus.ACTIVE,
    ) == "active"

    assert service._database_value(
        ExamplePayload(
            value="abc",
        )
    ) == '{"value": "abc"}'

    assert service._database_value(
        "plain",
    ) == "plain"


def test_diff_schema_service_json_dumps_handles_common_values() -> None:
    service = TwwDiffSchemaService()

    payload = {
        "date": date(
            2026,
            1,
            2,
        ),
        "datetime": datetime(
            2026,
            1,
            2,
            3,
            4,
            5,
        ),
        "enum": ExampleStatus.ACTIVE,
        "dataclass": ExamplePayload(
            value="abc",
        ),
    }

    dumped = service._json_dumps(
        payload,
    )

    assert '"date": "2026-01-02"' in dumped
    assert '"datetime": "2026-01-02T03:04:05"' in dumped
    assert '"enum": "active"' in dumped
    assert '"dataclass": {"value": "abc"}' in dumped


def test_diff_schema_service_table_columns_reads_information_schema() -> None:
    cursor = FakeCursor(
        table_columns={
            "job_id",
            "obj_id",
            "status",
        },
    )

    service = TwwDiffSchemaService(
        schema="tww_diff",
    )

    columns = service._table_columns(
        cursor=cursor,
        table_name="reach",
    )

    assert columns == {
        "job_id",
        "obj_id",
        "status",
    }

    assert cursor.executed[0][1] == (
        "tww_diff",
        "reach",
    )


def test_diff_schema_service_assert_required_columns_accepts_complete_table() -> None:
    service = TwwDiffSchemaService()

    service._assert_required_columns(
        table_name="reach",
        table_columns={
            "job_id",
            "obj_id",
            "is_created",
            "is_altered",
            "is_deleted",
            "import_values",
            "canonical_values",
            "changed_attributes",
            "unpermitted_values",
            "permission_findings",
            "validation_findings",
        },
    )


def test_diff_schema_service_assert_required_columns_raises_for_missing_columns() -> None:
    service = TwwDiffSchemaService(
        schema="tww_diff",
    )

    with pytest.raises(
        RuntimeError,
        match="missing columns",
    ):
        service._assert_required_columns(
            table_name="reach",
            table_columns={
                "job_id",
                "obj_id",
            },
        )


def test_diff_schema_service_quote_identifier_escapes_quotes() -> None:
    service = TwwDiffSchemaService()

    assert service._quote_identifier(
        'weird"name',
    ) == '"weird""name"'


def test_diff_schema_service_table_qualifies_schema_and_table() -> None:
    service = TwwDiffSchemaService(
        schema="tww_diff",
    )

    assert service._table(
        "reach",
    ) == '"tww_diff"."reach"'


def test_diff_schema_service_insert_metadata_executes_insert_and_returns_id() -> None:
    cursor = FakeCursor(
        metadata_id=77,
    )

    service = TwwDiffSchemaService(
        schema="tww_diff",
    )

    job_db_id = service._insert_metadata(
        cursor=cursor,
        job_id="job-1",
        metadata={
            "source_model": "AG64",
            "source_file": "/tmp/input.xtf",
            "import_schema": "import_schema",
            "live_schema": "tww_od",
        },
        validation_success=True,
        job_status="pending",
    )

    assert job_db_id == 77

    query, parameters = cursor.executed[0]

    assert 'INSERT INTO "tww_diff"."metadata"' in query

    assert parameters[:7] == (
        "job-1",
        "pending",
        True,
        "AG64",
        "/tmp/input.xtf",
        "import_schema",
        "tww_od",
    )


def test_diff_schema_service_delete_existing_job_executes_delete() -> None:
    cursor = FakeCursor()

    service = TwwDiffSchemaService(
        schema="tww_diff",
    )

    service._delete_existing_job(
        cursor=cursor,
        job_id="job-1",
    )

    query, parameters = cursor.executed[0]

    assert 'DELETE FROM "tww_diff"."metadata"' in query
    assert parameters == (
        "job-1",
    )


def test_diff_schema_service_insert_feature_writes_known_columns_and_geometry() -> None:
    cursor = FakeCursor()

    service = TwwDiffSchemaService(
        schema="tww_diff",
        srid=2056,
    )

    feature = ReviewFeature(
        class_id="reach",
        object_id="ch000000re000001",
        attributes={
            "is_altered": True,
            "status": "active",
            "ignored": "not in table",
            "import_values": {
                "status": "active",
            },
        },
        geometries={
            "progression_geometry": b"fake-wkb",
            "ignored_geometry": b"ignored",
        },
    )

    service._insert_feature(
        cursor=cursor,
        job_db_id=42,
        table_name="reach",
        feature=feature,
        table_columns={
            "job_id",
            "obj_id",
            "is_created",
            "is_altered",
            "is_deleted",
            "import_values",
            "canonical_values",
            "changed_attributes",
            "unpermitted_values",
            "permission_findings",
            "validation_findings",
            "status",
            "progression_geometry",
        },
    )

    query, parameters = cursor.executed[0]

    assert 'INSERT INTO "tww_diff"."reach"' in query
    assert '"status"' in query
    assert '"progression_geometry"' in query
    assert "ST_GeomFromWKB" in query
    assert "ignored" not in query
    assert "ignored_geometry" not in query

    assert b"fake-wkb" in parameters
    assert 2056 in parameters


def test_diff_schema_service_write_persists_metadata_and_features(
    monkeypatch,
) -> None:
    table_columns = {
        "job_id",
        "obj_id",
        "is_created",
        "is_altered",
        "is_deleted",
        "import_values",
        "canonical_values",
        "changed_attributes",
        "unpermitted_values",
        "permission_findings",
        "validation_findings",
        "status",
        "progression_geometry",
    }

    cursor = FakeCursor(
        table_columns=table_columns,
        metadata_id=999,
    )
    connection = FakeConnection(
        cursor=cursor,
    )

    monkeypatch.setattr(
        DatabaseUtils,
        "PsycopgConnection",
        lambda: FakeConnectionContext(
            connection,
        ),
    )

    service = TwwDiffSchemaService(
        schema="tww_diff",
        srid=2056,
    )

    result = service.write(
        job_id="job-1",
        features_by_class={
            "reach": (
                ReviewFeature(
                    class_id="reach",
                    object_id="ch000000re000001",
                    attributes={
                        "is_altered": True,
                        "status": "active",
                        "import_values": {
                            "status": "active",
                        },
                    },
                    geometries={
                        "progression_geometry": b"fake-wkb",
                    },
                ),
            ),
        },
        metadata={
            "source_model": "AG64",
            "source_file": "/tmp/input.xtf",
            "import_schema": "import_schema",
            "live_schema": "tww_od",
        },
        validation_success=True,
        job_status="pending",
    )

    assert result.job_db_id == 999
    assert result.job_id == "job-1"
    assert result.row_count == 1

    assert connection.committed is True
    assert connection.closed is True

    executed_queries = [
        query
        for query, _ in cursor.executed
    ]

    assert any(
        'DELETE FROM "tww_diff"."metadata"'
        in query
        for query in executed_queries
    )

    assert any(
        'INSERT INTO "tww_diff"."metadata"'
        in query
        for query in executed_queries
    )

    assert any(
        'INSERT INTO "tww_diff"."reach"'
        in query
        for query in executed_queries
    )


def test_diff_schema_service_write_does_not_delete_existing_job_when_reset_is_false(
    monkeypatch,
) -> None:
    table_columns = {
        "job_id",
        "obj_id",
        "is_created",
        "is_altered",
        "is_deleted",
        "import_values",
        "canonical_values",
        "changed_attributes",
        "unpermitted_values",
        "permission_findings",
        "validation_findings",
    }

    cursor = FakeCursor(
        table_columns=table_columns,
        metadata_id=100,
    )
    connection = FakeConnection(
        cursor=cursor,
    )

    monkeypatch.setattr(
        DatabaseUtils,
        "PsycopgConnection",
        lambda: FakeConnectionContext(
            connection,
        ),
    )

    service = TwwDiffSchemaService()

    service.write(
        job_id="job-1",
        features_by_class={},
    )

    executed_queries = [
        query
        for query, _ in cursor.executed
    ]

    assert not any(
        "DELETE FROM"
        in query
        for query in executed_queries
    )
