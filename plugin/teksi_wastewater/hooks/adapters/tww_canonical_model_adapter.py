from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from tww_hooks.models.canonical_model import (
    CanonicalAttributeMetadata,
    CanonicalClassMetadata,
    CanonicalModelMetadata,
    CanonicalValueMetadata,
)

from ..utils.database_utils import (
    DatabaseUtils,
)


from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from tww_hooks.models.canonical_model import (
    CanonicalAttributeMetadata,
    CanonicalClassMetadata,
    CanonicalModelMetadata,
    CanonicalValueMetadata,
    LocalizedMetadata,
    Localization,
)

from ..utils.database_utils import (
    DatabaseUtils,
)


@dataclass(slots=True)
class TwwCanonicalModelAdapter:
    """
    Plugin-side adapter that loads canonical TEKSI Wastewater model metadata
    from tww_sys dictionary tables.

    The adapter exposes database metadata through tww_hooks canonical metadata
    models. Database access and tww_sys table knowledge intentionally stay in
    the plugin layer.
    """

    schema: str = "tww_sys"

    def canonical_model(
        self,
    ) -> CanonicalModelMetadata:
        """
        Load complete canonical model metadata.
        """

        return CanonicalModelMetadata(
            classes=self.classes(),
            attributes=self.attributes(),
            values=self.values(),
        )

    def classes(
        self,
        language: Localization = Localization.de,
    ) -> dict[
        str,
        CanonicalClassMetadata,
    ]:
        """
        Load canonical class metadata keyed by class_id.

        Canonical class_id corresponds to dictionary_od_table.tablename.
        """
        localized_table_column = self._qualified_identifier(
            table_alias="f",
            column_name=self._localized_column_name(
                prefix="field_name",
                language=language,
            ),
        )
        query = DatabaseUtils.compose_sql(
            """
            SELECT
                id,
                tablename,
                {localized_table_column} as localized_name
            FROM {schema}.dictionary_od_table
            ORDER BY tablename
            """,
            schema=DatabaseUtils.wrap_identifier(
                self.schema,
            ),
            localized_table_column=localized_table_column,
        )

        rows = self._fetchall_dict(
            query,
        )

        return {
            row["tablename"]: CanonicalClassMetadata(
                source_id=row["id"],
                class_id=row["tablename"],
                localized=self._localized_metadata(
                    language=language,
                    value=row.get(
                        "localized_name",
                    ),
                ),
            )
            for row in rows
        }

    def attributes(
        self,
        class_id: str | None = None,
        language: Localization = Localization.de,
    ) -> dict[
        tuple[
            str,
            str,
        ],
        CanonicalAttributeMetadata,
    ]:
        """
        Load canonical attribute metadata keyed by (class_id, attribute_id).

        Canonical class_id is resolved from dictionary_od_table.tablename.
        Canonical attribute_id corresponds to dictionary_od_field.field_name.
        """

        where_clause = DatabaseUtils.compose_sql(
            "",
        )

        if class_id is not None:
            where_clause = DatabaseUtils.compose_sql(
                "WHERE t.tablename = {class_id}",
                class_id=DatabaseUtils.wrap_literal(
                    class_id,
                ),
            )
        localized_field_column = self._qualified_identifier(
            table_alias="f",
            column_name=self._localized_column_name(
                prefix="field_name",
                language=language,
            ),
        )
        query = DatabaseUtils.compose_sql(
            """
            SELECT
                f.id,
                f.class_id AS class_source_id,
                f.attribute_id AS attribute_source_id,
                t.tablename AS class_id,
                f.field_name AS attribute_id,
                {localized_field_column} AS localized_name
            FROM {schema}.dictionary_od_field f
            JOIN {schema}.dictionary_od_table t
                ON t.id = f.class_id
            {where_clause}
            ORDER BY
                t.tablename,
                f.field_name
            """,
            schema=DatabaseUtils.wrap_identifier(
                self.schema,
            ),
            
            localized_field_column=localized_field_column,
            where_clause=where_clause,
        )

        rows = self._fetchall_dict(
            query,
        )

        return {
            (
                row["class_id"],
                row["attribute_id"],
            ): CanonicalAttributeMetadata(
                source_id=row["id"],
                class_source_id=row["class_source_id"],
                attribute_source_id=row["attribute_source_id"],
                class_id=row["class_id"],
                attribute_id=row["attribute_id"],
                localized=self._localized_metadata(
                    language=language,
                    value=row.get(
                        "localized_name",
                    ),
                ),
            )
            for row in rows
        }

    def values(
        self,
        class_id: str | None = None,
        attribute_id: str | None = None,
        language: Localization = Localization.de,
    ) -> dict[
        tuple[
            str,
            str,
            str,
        ],
        CanonicalValueMetadata,
    ]:
        """
        Load canonical value metadata keyed by
        (class_id, attribute_id, value_id).

        Canonical class_id is resolved from dictionary_od_table.tablename.
        Canonical attribute_id is resolved from dictionary_od_field.field_name.
        Canonical value_id corresponds to dictionary_od_values.value_name.
        """

        where_parts = []

        if class_id is not None:
            where_parts.append(
                DatabaseUtils.compose_sql(
                    "t.tablename = {class_id}",
                    class_id=DatabaseUtils.wrap_literal(
                        class_id,
                    ),
                )
            )

        if attribute_id is not None:
            where_parts.append(
                DatabaseUtils.compose_sql(
                    "f.field_name = {attribute_id}",
                    attribute_id=DatabaseUtils.wrap_literal(
                        attribute_id,
                    ),
                )
            )
        localized_value_column = self._qualified_identifier(
            table_alias="v",
            column_name=self._localized_column_name(
                prefix="value_name",
                language=language,
            ),
        )
        where_clause = DatabaseUtils.compose_sql(
            "",
        )

        if where_parts:
            where_clause = DatabaseUtils.compose_sql(
                "WHERE {conditions}",
                conditions=DatabaseUtils.compose_sql(
                    " AND ",
                ).join(
                    where_parts,
                ),
            )

        query = DatabaseUtils.compose_sql(
            """
            SELECT
                v.id,
                v.class_id AS class_source_id,
                v.attribute_id AS attribute_source_id,
                v.value_id AS value_source_id,
                t.tablename AS class_id,
                f.field_name AS attribute_id,
                v.value_name AS value_id,
                {localized_value_column} AS localized_name
            FROM {schema}.dictionary_od_values v
            JOIN {schema}.dictionary_od_table t
                ON t.id = v.class_id
            JOIN {schema}.dictionary_od_field f
                ON f.class_id = v.class_id
               AND f.attribute_id = v.attribute_id
            {where_clause}
            ORDER BY
                t.tablename,
                f.field_name,
                v.value_name
            """,
            schema=DatabaseUtils.wrap_identifier(
                self.schema,
            ),
            where_clause=where_clause,
            localized_value_column=localized_value_column,
        )

        rows = self._fetchall_dict(
            query,
        )

        return {
            (
                row["class_id"],
                row["attribute_id"],
                row["value_id"],
            ): CanonicalValueMetadata(
                source_id=row["id"],
                class_source_id=row["class_source_id"],
                attribute_source_id=row["attribute_source_id"],
                value_source_id=row["value_source_id"],
                class_id=row["class_id"],
                attribute_id=row["attribute_id"],
                value_id=row["value_id"],
                localized=self._localized_metadata(
                    language=language,
                    value=row.get(
                        "localized_name",
                    ),
                ),
            )
            for row in rows
        }

    def _localized_names(
        self,
        *,
        de: str | None,
        fr: str | None,
    ) -> dict[
        Localization,
        str,
    ]:
        names: dict[
            Localization,
            str,
        ] = {}

        if de:
            names[
                Localization.de
            ] = de

        if fr:
            names[
                Localization.fr
            ] = fr

        return names

    def _localized_metadata(
        self,
        *,
        language: Localization,
        value: str | None,
    ) -> LocalizedMetadata:
        if not value:
            return LocalizedMetadata()

        return LocalizedMetadata(
            names={
                language: value,
            },
        )

    def _localized_column_name(
        self,
        prefix: str,
        language: Localization,
    ) -> str:
        return f"{prefix}_{language.value}"

    def _qualified_identifier(
        self,
        table_alias: str,
        column_name: str,
    ):
        return DatabaseUtils.compose_sql(
            "{table_alias}.{column_name}",
            table_alias=DatabaseUtils.wrap_identifier(
                table_alias,
            ),
            column_name=DatabaseUtils.wrap_identifier(
                column_name,
            ),
        )

    def _fetchall_dict(
        self,
        query,
    ) -> list[
        dict[
            str,
            Any,
        ]
    ]:
        if hasattr(
            DatabaseUtils,
            "fetchall_dict",
        ):
            return DatabaseUtils.fetchall_dict(
                query,
            )

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

@dataclass(slots=True, frozen=True)
class InMemoryCanonicalModelCapability:
    """
    In-memory canonical model metadata provider for tests and examples.
    """

    metadata: CanonicalModelMetadata

    def canonical_model(
        self,
    ) -> CanonicalModelMetadata:
        return self.metadata

    def classes(
        self,
    ) -> dict[
        str,
        CanonicalClassMetadata,
    ]:
        return self.metadata.classes

    def attributes(
        self,
        class_id: str | None = None,
    ) -> dict[
        tuple[
            str,
            str,
        ],
        CanonicalAttributeMetadata,
    ]:
        if class_id is None:
            return self.metadata.attributes

        return {
            key: value
            for key, value in self.metadata.attributes.items()
            if key[0] == class_id
        }

    def values(
        self,
        class_id: str | None = None,
        attribute_id: str | None = None,
    ) -> dict[
        tuple[
            str,
            str,
            str,
        ],
        CanonicalValueMetadata,
    ]:
        return {
            key: value
            for key, value in self.metadata.values.items()
            if (
                class_id is None
                or key[0] == class_id
            )
            and (
                attribute_id is None
                or key[1] == attribute_id
            )
        }