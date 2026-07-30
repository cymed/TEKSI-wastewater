from __future__ import annotations

from dataclasses import dataclass
from typing import Any
from collections.abc import Sequence

from tww_hooks.capabilities.relation_lookup import (
    RelationLookupCapability,
)
from tww_hooks.models.canonical_object import (
    CanonicalObject,
    CanonicalObjectIdentity,
)

from ..utils.database_utils import DatabaseUtils


@dataclass(slots=True)
class TwwRelationLookupAdapter(
    RelationLookupCapability,
):
    """
    Plugin-side relation lookup implementation backed by the database.

    This adapter bridges tww_hooks RelationLookupCapability to the
    TEKSI Wastewater database / ili2pg import schema.
    """

    schema: str

    def canonical_objects(
        self,
        local_class_id: str,
        related_class_id: str,
        local_attribute: str,
        related_attribute: str,
        value: Any,
    ) -> Sequencequery = DatabaseUtils.compose_sql(
            """
            SELECT {identity_attribute}
            FROM {schema}.{table_name}
            WHERE {related_attribute} = {value}
            """,
            identity_attribute=DatabaseUtils.wrap_identifier(
                "obj_id",
            ),
            schema=DatabaseUtils.wrap_identifier(
                self.schema,
            ),
            table_name=DatabaseUtils.wrap_identifier(
                related_class_id,
            ),
            related_attribute=DatabaseUtils.wrap_identifier(
                related_attribute,
            ),
            value=DatabaseUtils.wrap_literal(
                value,
            ),
        )

        rows = DatabaseUtils.fetchall(
            query,
        )

        return tuple(
            CanonicalObjectIdentity(
                class_id=related_class_id,
                attributes={
                    "obj_id": row[0],
                },
            )
            for row in rows
        )

    def current_object(
        self,
        identity: CanonicalObjectIdentity,
    ) -> CanonicalObject | None:
        rows = self._fetch_current_rows(
            identity,
        )

        if not rows:
            return None

        row = rows[0]

        values = {
            key: value
            for key, value in row.items()
            if key not in identity.attributes
        }

        return CanonicalObject(
            identity=identity,
            values=values,
            last_modification=row.get(
                "last_modification",
            ),
        )

    def _fetch_current_rows(
        self,
        identity: CanonicalObjectIdentity,
    ) -> list[dict[str, Any]]:
        where_parts = []

        for attribute, value in identity.attributes.items():
            where_parts.append(
                DatabaseUtils.compose_sql(
                    "{attribute} = {value}",
                    attribute=DatabaseUtils.wrap_identifier(
                        attribute,
                    ),
                    value=DatabaseUtils.wrap_literal(
                        value,
                    ),
                )
            )

        where_clause = DatabaseUtils.compose_sql(
            " AND ",
        ).join(
            where_parts,
        )

        query = DatabaseUtils.compose_sql(
            """
            SELECT *
            FROM {schema}.{table_name}
            WHERE {where_clause}
            LIMIT 1
            """,
            schema=DatabaseUtils.wrap_identifier(
                self.schema,
            ),
            table_name=DatabaseUtils.wrap_identifier(
                identity.class_id,
            ),
            where_clause=where_clause,
        )

        return self._fetchall_dict(
            query,
        )

    def _fetchall_dict(
        self,
        query,
    ) -> list[dict[str, Any]]:
        with DatabaseUtils.PsycopgConnection() as connection:
            cursor = connection.cursor()
            cursor.execute(
                query,
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