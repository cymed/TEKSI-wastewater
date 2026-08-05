from __future__ import annotations

from dataclasses import asdict, dataclass, is_dataclass
from datetime import date, datetime
import json
from typing import Any
from collections.abc import Iterable, Mapping

from tww_hooks.models.validation import (
    ClassifiedChange,
    ClassifiedChanges,
    Change,
)

from ...utils.database_utils import (
    DatabaseUtils,
)


@dataclass(slots=True)
class DiffSchemaWriteResult:
    """
    Result of writing classified changes into a PostgreSQL diff schema.
    """

    schema: str
    change_count: int
    attribute_count: int
    finding_count: int


@dataclass(slots=True)
class TwwDiffSchemaService:
    """
    Plugin-side service for persisting hook-side diff/review state into a
    PostgreSQL schema.

    This service intentionally only handles database access.

    It does not:

    - classify changes;
    - evaluate rights;
    - validate changes;
    - compare geometries;
    - create GeoPackages;
    - build QGIS layers.

    Those responsibilities belong to tww_hooks services or plugin-side
    interpreters/adapters.
    """

    schema: str

    def write(
        self,
        classified: ClassifiedChanges,
        metadata: Mapping[
            str,
            Any,
        ] | None = None,
        reset_schema: bool = True,
    ) -> DiffSchemaWriteResult:
        """
        Write classified changes into the configured diff schema.

        Parameters
        ----------
        classified:
            Hook-side classified changes.

        metadata:
            Optional workflow metadata. Typical examples are source file,
            source model, import schema, live schema, provider oid,
            dataowner oid or job id.

        reset_schema:
            If true, the existing diff schema is dropped and recreated.
        """

        with DatabaseUtils.PsycopgConnection() as connection:
            cursor = connection.cursor()

            if reset_schema:
                self._drop_schema(
                    cursor,
                )

            self._create_schema(
                cursor,
            )

            self._create_tables(
                cursor,
            )

            self._write_metadata(
                cursor=cursor,
                metadata={
                    **dict(
                        classified.metadata,
                    ),
                    **dict(
                        metadata or {},
                    ),
                },
            )

            change_count = 0
            attribute_count = 0
            finding_count = 0

            for classified_change in self._iter_classified_changes(
                classified,
            ):
                change_id = self._insert_change(
                    cursor=cursor,
                    classified_change=classified_change,
                )

                change_count += 1

                attribute_count += self._insert_change_attributes(
                    cursor=cursor,
                    change_id=change_id,
                    classified_change=classified_change,
                )

                finding_count += self._insert_findings(
                    cursor=cursor,
                    change_id=change_id,
                    classified_change=classified_change,
                )

            self._create_indexes(
                cursor,
            )

            connection.commit()

        return DiffSchemaWriteResult(
            schema=self.schema,
            change_count=change_count,
            attribute_count=attribute_count,
            finding_count=finding_count,
        )

    def _drop_schema(
        self,
        cursor,
    ) -> None:
        cursor.execute(
            f"DROP SCHEMA IF EXISTS {self._quote_identifier(self.schema)} CASCADE;"
        )

    def _create_schema(
        self,
        cursor,
    ) -> None:
        cursor.execute(
            f"CREATE SCHEMA IF NOT EXISTS {self._quote_identifier(self.schema)};"
        )

    def _create_tables(
        self,
        cursor,
    ) -> None:
        cursor.execute(
            f"""
            CREATE TABLE IF NOT EXISTS {self._table("metadata")} (
                key text PRIMARY KEY,
                value jsonb NOT NULL
            );
            """
        )

        cursor.execute(
            f"""
            CREATE TABLE IF NOT EXISTS {self._table("changes")} (
                change_id bigserial PRIMARY KEY,
                class_id text NOT NULL,
                object_id text NOT NULL,
                operation text NOT NULL,
                classification text NOT NULL,
                permitted boolean NOT NULL,
                severity text,
                reason text,
                old_values jsonb NOT NULL DEFAULT '{{}}'::jsonb,
                new_values jsonb NOT NULL DEFAULT '{{}}'::jsonb,
                changed_attributes jsonb NOT NULL DEFAULT '[]'::jsonb,
                classified_at timestamp with time zone,
                created_at timestamp with time zone NOT NULL DEFAULT now()
            );
            """
        )

        cursor.execute(
            f"""
            CREATE TABLE IF NOT EXISTS {self._table("change_attributes")} (
                change_attribute_id bigserial PRIMARY KEY,
                change_id bigint NOT NULL
                    REFERENCES {self._table("changes")} (change_id)
                    ON DELETE CASCADE,
                attribute_name text NOT NULL,
                old_value jsonb,
                new_value jsonb,
                changed boolean NOT NULL DEFAULT true,
                permitted boolean NOT NULL,
                classification text NOT NULL
            );
            """
        )

        cursor.execute(
            f"""
            CREATE TABLE IF NOT EXISTS {self._table("findings")} (
                finding_id bigserial PRIMARY KEY,
                change_id bigint NOT NULL
                    REFERENCES {self._table("changes")} (change_id)
                    ON DELETE CASCADE,
                code text,
                severity text,
                attribute_name text,
                message text,
                raw jsonb NOT NULL DEFAULT '{{}}'::jsonb
            );
            """
        )

    def _create_indexes(
        self,
        cursor,
    ) -> None:
        cursor.execute(
            f"""
            CREATE INDEX IF NOT EXISTS changes_class_object_idx
            ON {self._table("changes")} (class_id, object_id);
            """
        )

        cursor.execute(
            f"""
            CREATE INDEX IF NOT EXISTS changes_classification_idx
            ON {self._table("changes")} (classification);
            """
        )

        cursor.execute(
            f"""
            CREATE INDEX IF NOT EXISTS change_attributes_change_id_idx
            ON {self._table("change_attributes")} (change_id);
            """
        )

        cursor.execute(
            f"""
            CREATE INDEX IF NOT EXISTS findings_change_id_idx
            ON {self._table("findings")} (change_id);
            """
        )

    def _write_metadata(
        self,
        *,
        cursor,
        metadata: Mapping[
            str,
            Any,
        ],
    ) -> None:
        for key, value in metadata.items():
            cursor.execute(
                f"""
                INSERT INTO {self._table("metadata")} (
                    key,
                    value
                )
                VALUES (
                    %s,
                    %s::jsonb
                )
                ON CONFLICT (key)
                DO UPDATE SET
                    value = EXCLUDED.value;
                """,
                (
                    key,
                    self._json_dumps(
                        value,
                    ),
                ),
            )

    def _insert_change(
        self,
        *,
        cursor,
        classified_change: ClassifiedChange,
    ) -> int:
        change = classified_change.change
        metadata = classified_change.metadata

        cursor.execute(
            f"""
            INSERT INTO {self._table("changes")} (
                class_id,
                object_id,
                operation,
                classification,
                permitted,
                severity,
                reason,
                old_values,
                new_values,
                changed_attributes,
                classified_at
            )
            VALUES (
                %s,
                %s,
                %s,
                %s,
                %s,
                %s,
                %s,
                %s::jsonb,
                %s::jsonb,
                %s::jsonb,
                %s
            )
            RETURNING change_id;
            """,
            (
                change.table_name,
                change.object_id,
                self._enum_value(
                    change.operation,
                ),
                self._enum_value(
                    metadata.classification,
                ),
                metadata.permitted,
                self._enum_value(
                    metadata.severity,
                ),
                metadata.reason,
                self._json_dumps(
                    change.old_values,
                ),
                self._json_dumps(
                    change.new_values,
                ),
                self._json_dumps(
                    self._changed_attributes_payload(
                        change,
                    ),
                ),
                metadata.classified_at,
            ),
        )

        row = cursor.fetchone()

        return row[0]

    def _insert_change_attributes(
        self,
        *,
        cursor,
        change_id: int,
        classified_change: ClassifiedChange,
    ) -> int:
        change = classified_change.change
        metadata = classified_change.metadata

        count = 0

        for attribute_name in self._changed_attribute_names(
            change,
        ):
            cursor.execute(
                f"""
                INSERT INTO {self._table("change_attributes")} (
                    change_id,
                    attribute_name,
                    old_value,
                    new_value,
                    changed,
                    permitted,
                    classification
                )
                VALUES (
                    %s,
                    %s,
                    %s::jsonb,
                    %s::jsonb,
                    %s,
                    %s,
                    %s
                );
                """,
                (
                    change_id,
                    attribute_name,
                    self._json_dumps(
                        change.old_values.get(
                            attribute_name,
                        )
                    ),
                    self._json_dumps(
                        change.new_values.get(
                            attribute_name,
                        )
                    ),
                    True,
                    metadata.permitted,
                    self._enum_value(
                        metadata.classification,
                    ),
                ),
            )

            count += 1

        return count

    def _insert_findings(
        self,
        *,
        cursor,
        change_id: int,
        classified_change: ClassifiedChange,
    ) -> int:
        count = 0

        for finding in classified_change.metadata.findings:
            cursor.execute(
                f"""
                INSERT INTO {self._table("findings")} (
                    change_id,
                    code,
                    severity,
                    attribute_name,
                    message,
                    raw
                )
                VALUES (
                    %s,
                    %s,
                    %s,
                    %s,
                    %s,
                    %s::jsonb
                );
                """,
                (
                    change_id,
                    getattr(
                        finding,
                        "code",
                        None,
                    ),
                    self._enum_value(
                        getattr(
                            finding,
                            "severity",
                            None,
                        )
                    ),
                    getattr(
                        finding,
                        "attribute_name",
                        None,
                    ),
                    getattr(
                        finding,
                        "message",
                        None,
                    ),
                    self._json_dumps(
                        self._raw_payload(
                            finding,
                        )
                    ),
                ),
            )

            count += 1

        return count

    def _iter_classified_changes(
        self,
        classified: ClassifiedChanges,
    ) -> Iterable[
        ClassifiedChange,
    ]:
        yield from classified.created_objects
        yield from classified.altered_objects
        yield from classified.deleted_objects
        yield from classified.unpermitted_changes

    def _changed_attribute_names(
        self,
        change: Change,
    ) -> tuple[
        str,
        ...
    ]:
        names = []

        for attribute in change.changed_attributes:
            attribute_name = getattr(
                attribute,
                "attribute_name",
                None,
            )

            if attribute_name is not None:
                names.append(
                    attribute_name,
                )

        return tuple(
            names,
        )

    def _changed_attributes_payload(
        self,
        change: Change,
    ) -> list[
        dict[
            str,
            Any,
        ]
    ]:
        payload = []

        for attribute_name in self._changed_attribute_names(
            change,
        ):
            payload.append(
                {
                    "attribute_name": attribute_name,
                    "old_value": change.old_values.get(
                        attribute_name,
                    ),
                    "new_value": change.new_values.get(
                        attribute_name,
                    ),
                }
            )

        return payload

    def _raw_payload(
        self,
        value: Any,
    ) -> dict[
        str,
        Any,
    ]:
        if is_dataclass(
            value,
        ):
            return asdict(
                value,
            )

        if hasattr(
            value,
            "__dict__",
        ):
            return dict(
                value.__dict__,
            )

        return {
            "value": value,
        }

    def _json_dumps(
        self,
        value: Any,
    ) -> str:
        return json.dumps(
            value,
            default=self._json_default,
        )

    def _json_default(
        self,
        value: Any,
    ) -> Any:
        if isinstance(
            value,
            (
                datetime,
                date,
            ),
        ):
            return value.isoformat()

        if hasattr(
            value,
            "value",
        ):
            return value.value

        if is_dataclass(
            value,
        ):
            return asdict(
                value,
            )

        return str(
            value,
        )

    def _enum_value(
        self,
        value: Any,
    ) -> str | None:
        if value is None:
            return None

        if hasattr(
            value,
            "value",
        ):
            return value.value

        return str(
            value,
        )

    def _table(
        self,
        table_name: str,
    ) -> str:
        return (
            f"{self._quote_identifier(self.schema)}."
            f"{self._quote_identifier(table_name)}"
        )

    def _quote_identifier(
        self,
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