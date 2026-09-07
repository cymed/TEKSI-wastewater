from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from enum import StrEnum
from typing import Any

from psycopg import sql

from teksi_hooks.capabilities.connection import (
    DatabaseConnectionFactory,
)
from teksi_hooks.models.canonical_object import (
    CanonicalAttributeMetadata,
    CanonicalClassMetadata,
    CanonicalModelMetadata,
    CanonicalValueMetadata,
    LocalizedMetadata,
)


class TwwLanguage(
    StrEnum,
):
    """
    Languages available in TEKSI Wastewater dictionary metadata.
    """

    DE = "de"
    FR = "fr"
    IT = "it"
    EN = "en"


@dataclass(slots=True)
class TwwCanonicalModelAdapter:
    """
    Load canonical TEKSI Wastewater model metadata.

    Stable canonical identifiers and generic localized metadata are exposed
    through teksi_hooks models. Knowledge of the language columns available
    in tww_sys remains in this wastewater-specific adapter.

    Database connections are created through the supplied connection factory.
    """

    connection_factory: DatabaseConnectionFactory

    schema: str = "tww_sys"

    languages: tuple[
        TwwLanguage,
        ...,
    ] = (
        TwwLanguage.DE,
        TwwLanguage.FR,
        TwwLanguage.IT,
        TwwLanguage.EN,
    )

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
    ) -> dict[
        str,
        CanonicalClassMetadata,
    ]:
        """
        Load canonical class metadata keyed by class identifier.
        """

        query = sql.SQL(
            """
            SELECT
                t.id AS source_id,
                t.tablename AS class_id,
                t.name_de,
                t.name_fr,
                t.name_it,
                t.name_en
            FROM {}.dictionary_od_table AS t
            ORDER BY
                t.tablename;
            """
        ).format(
            sql.Identifier(
                self.schema,
            )
        )

        rows = self._fetchall_dict(
            query=query,
        )

        return {
            row["class_id"]: self._class_metadata_from_row(
                row,
            )
            for row in rows
        }

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
        """
        Load canonical attribute metadata.

        Results are keyed by ``(class_id, attribute_id)``.
        """

        conditions: list[
            sql.Composable
        ] = []

        parameters: list[
            Any
        ] = []

        if class_id is not None:
            conditions.append(
                sql.SQL(
                    "t.tablename = %s"
                )
            )

            parameters.append(
                class_id,
            )

        query = sql.SQL(
            """
            SELECT
                f.attribute_id AS source_id,
                t.tablename AS class_id,
                f.field_name AS attribute_id,
                f.field_datatype AS field_datatype,
                f.field_name_de,
                f.field_name_fr,
                f.field_name_it,
                f.field_name_en
            FROM {}.dictionary_od_field AS f
            JOIN {}.dictionary_od_table AS t
                ON t.id = f.class_id
            {}
            ORDER BY
                t.tablename,
                f.field_name;
            """
        ).format(
            sql.Identifier(
                self.schema,
            ),
            sql.Identifier(
                self.schema,
            ),
            self._where_clause(
                conditions,
            ),
        )

        rows = self._fetchall_dict(
            query=query,
            parameters=parameters,
        )

        return {
            (
                row["class_id"],
                row["attribute_id"],
            ): self._attribute_metadata_from_row(
                row,
            )
            for row in rows
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
        """
        Load canonical value metadata.

        Results are keyed by
        ``(class_id, attribute_id, value_id)``.
        """

        conditions: list[
            sql.Composable
        ] = []

        parameters: list[
            Any
        ] = []

        if class_id is not None:
            conditions.append(
                sql.SQL(
                    "t.tablename = %s"
                )
            )

            parameters.append(
                class_id,
            )

        if attribute_id is not None:
            conditions.append(
                sql.SQL(
                    "f.field_name = %s"
                )
            )

            parameters.append(
                attribute_id,
            )

        query = sql.SQL(
            """
            SELECT
                v.value_id AS source_id,
                t.tablename AS class_id,
                f.field_name AS attribute_id,
                v.value_name AS value_id,
                v.value_name_de,
                v.value_name_fr,
                v.value_name_it,
                v.value_name_en
            FROM {}.dictionary_od_values AS v
            JOIN {}.dictionary_od_table AS t
                ON t.id = v.class_id
            JOIN {}.dictionary_od_field AS f
                ON f.class_id = v.class_id
               AND f.attribute_id = v.attribute_id
            {}
            ORDER BY
                t.tablename,
                f.field_name,
                v.value_name;
            """
        ).format(
            sql.Identifier(
                self.schema,
            ),
            sql.Identifier(
                self.schema,
            ),
            sql.Identifier(
                self.schema,
            ),
            self._where_clause(
                conditions,
            ),
        )

        rows = self._fetchall_dict(
            query=query,
            parameters=parameters,
        )

        return {
            (
                row["class_id"],
                row["attribute_id"],
                row["value_id"],
            ): self._value_metadata_from_row(
                row,
            )
            for row in rows
        }

    def class_metadata(
        self,
        class_id: str,
    ) -> CanonicalClassMetadata | None:
        """
        Return metadata for one canonical class.
        """

        query = sql.SQL(
            """
            SELECT
                t.id AS source_id,
                t.tablename AS class_id,
                t.name_de,
                t.name_fr,
                t.name_it,
                t.name_en
            FROM {}.dictionary_od_table AS t
            WHERE t.tablename = %s;
            """
        ).format(
            sql.Identifier(
                self.schema,
            )
        )

        row = self._fetchone_dict(
            query=query,
            parameters=(
                class_id,
            ),
        )

        if row is None:
            return None

        return self._class_metadata_from_row(
            row,
        )

    def attribute_metadata(
        self,
        class_id: str,
        attribute_id: str,
    ) -> CanonicalAttributeMetadata | None:
        """
        Return metadata for one canonical attribute.
        """

        query = sql.SQL(
            """
            SELECT
                f.attribute_id AS source_id,
                t.tablename AS class_id,
                f.field_name AS attribute_id,
                f.field_datatype AS field_datatype,
                f.field_name_de,
                f.field_name_fr,
                f.field_name_it,
                f.field_name_en
            FROM {}.dictionary_od_field AS f
            JOIN {}.dictionary_od_table AS t
                ON t.id = f.class_id
            WHERE
                t.tablename = %s
                AND f.field_name = %s;
            """
        ).format(
            sql.Identifier(
                self.schema,
            ),
            sql.Identifier(
                self.schema,
            ),
        )

        row = self._fetchone_dict(
            query=query,
            parameters=(
                class_id,
                attribute_id,
            ),
        )

        if row is None:
            return None

        return self._attribute_metadata_from_row(
            row,
        )

    def value_metadata(
        self,
        class_id: str,
        attribute_id: str,
        value_id: str,
    ) -> CanonicalValueMetadata | None:
        """
        Return metadata for one canonical value.
        """

        query = sql.SQL(
            """
            SELECT
                v.value_id AS source_id,
                t.tablename AS class_id,
                f.field_name AS attribute_id,
                v.value_name AS value_id,
                v.value_name_de,
                v.value_name_fr,
                v.value_name_it,
                v.value_name_en
            FROM {}.dictionary_od_values AS v
            JOIN {}.dictionary_od_table AS t
                ON t.id = v.class_id
            JOIN {}.dictionary_od_field AS f
                ON f.class_id = v.class_id
               AND f.attribute_id = v.attribute_id
            WHERE
                t.tablename = %s
                AND f.field_name = %s
                AND v.value_name = %s;
            """
        ).format(
            sql.Identifier(
                self.schema,
            ),
            sql.Identifier(
                self.schema,
            ),
            sql.Identifier(
                self.schema,
            ),
        )

        row = self._fetchone_dict(
            query=query,
            parameters=(
                class_id,
                attribute_id,
                value_id,
            ),
        )

        if row is None:
            return None

        return self._value_metadata_from_row(
            row,
        )

    def is_geometry_attribute(
        self,
        class_id: str,
        attribute_id: str,
    ) -> bool:
        """
        Return whether one canonical attribute contains geometry data.
        """

        metadata = self.attribute_metadata(
            class_id,
            attribute_id,
        )

        if metadata is None:
            return False

        return self._is_geometry_datatype(
            metadata.field_datatype,
        )

    def geometry_attribute_names(
        self,
        class_id: str,
    ) -> tuple[
        str,
        ...,
    ]:
        """
        Return geometry attribute identifiers for one canonical class.
        """

        attributes = self.attributes(
            class_id=class_id,
        )

        return tuple(
            attribute_id
            for (
                attribute_class_id,
                attribute_id,
            ), metadata in attributes.items()
            if (
                attribute_class_id == class_id
                and self._is_geometry_datatype(
                    metadata.field_datatype,
                )
            )
        )

    def _class_metadata_from_row(
        self,
        row: Mapping[
            str,
            Any,
        ],
    ) -> CanonicalClassMetadata:
        """
        Build canonical class metadata from a dictionary row.
        """

        return CanonicalClassMetadata(
            source_id=row[
                "source_id"
            ],
            identifier=row[
                "class_id"
            ],
            localized=self._localized_metadata(
                row=row,
                name_prefix="name",
            ),
        )

    def _attribute_metadata_from_row(
        self,
        row: Mapping[
            str,
            Any,
        ],
    ) -> CanonicalAttributeMetadata:
        """
        Build canonical attribute metadata from a dictionary row.
        """

        return CanonicalAttributeMetadata(
            source_id=row[
                "source_id"
            ],
            identifier=row[
                "attribute_id"
            ],
            field_datatype=row.get(
                "field_datatype",
            ),
            localized=self._localized_metadata(
                row=row,
                name_prefix="field_name",
            ),
        )

    def _value_metadata_from_row(
        self,
        row: Mapping[
            str,
            Any,
        ],
    ) -> CanonicalValueMetadata:
        """
        Build canonical value metadata from a dictionary row.
        """

        return CanonicalValueMetadata(
            source_id=row[
                "source_id"
            ],
            identifier=row[
                "value_id"
            ],
            localized=self._localized_metadata(
                row=row,
                name_prefix="value_name",
            ),
        )

    def _localized_metadata(
        self,
        *,
        row: Mapping[
            str,
            Any,
        ],
        name_prefix: str,
    ) -> LocalizedMetadata:
        """
        Return localized metadata for the configured languages.

        Null and empty localized values are omitted.
        """

        names: dict[
            str,
            str,
        ] = {}

        for language in self.languages:
            column_name = (
                f"{name_prefix}_{language.value}"
            )

            value = row.get(
                column_name,
            )

            if value is None:
                continue

            if not isinstance(
                value,
                str,
            ):
                value = str(
                    value,
                )

            if not value:
                continue

            names[
                language.value
            ] = value

        return LocalizedMetadata(
            names=names,
        )

    def _is_geometry_datatype(
        self,
        field_datatype: str | None,
    ) -> bool:
        """
        Return whether a dictionary datatype represents geometry.
        """

        if field_datatype is None:
            return False

        return (
            field_datatype.strip().lower()
            == "geometry"
        )

    def _where_clause(
        self,
        conditions: Sequence[
            sql.Composable,
        ],
    ) -> sql.Composable:
        """
        Build a WHERE clause from composable SQL conditions.
        """

        if not conditions:
            return sql.SQL(
                ""
            )

        return sql.SQL(
            "WHERE "
        ) + sql.SQL(
            " AND "
        ).join(
            conditions,
        )

    def _fetchall_dict(
        self,
        *,
        query: sql.Composable,
        parameters: Sequence[
            Any,
        ] = (),
    ) -> list[
        dict[
            str,
            Any,
        ]
    ]:
        """
        Execute a query and return all rows as dictionaries.
        """

        with self.connection_factory.connection(
            autocommit=True,
        ) as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    query,
                    tuple(
                        parameters,
                    ),
                )

                rows = cursor.fetchall()

                if cursor.description is None:
                    return []

                column_names = tuple(
                    self._column_name(
                        column,
                    )
                    for column
                    in cursor.description
                )

        return [
            dict(
                zip(
                    column_names,
                    row,
                    strict=True,
                )
            )
            for row in rows
        ]

    def _fetchone_dict(
        self,
        *,
        query: sql.Composable,
        parameters: Sequence[
            Any,
        ] = (),
    ) -> dict[
        str,
        Any,
    ] | None:
        """
        Execute a query and return its first row as a dictionary.
        """

        with self.connection_factory.connection(
            autocommit=True,
        ) as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    query,
                    tuple(
                        parameters,
                    ),
                )

                row = cursor.fetchone()

                if row is None:
                    return None

                if cursor.description is None:
                    raise RuntimeError(
                        "Canonical metadata query returned a row "
                        "without column metadata."
                    )

                column_names = tuple(
                    self._column_name(
                        column,
                    )
                    for column
                    in cursor.description
                )

        return dict(
            zip(
                column_names,
                row,
                strict=True,
            )
        )

    def _column_name(
        self,
        column: Any,
    ) -> str:
        """
        Return a column name from psycopg or test cursor metadata.
        """

        name = getattr(
            column,
            "name",
            None,
        )

        if name is not None:
            return str(
                name,
            )

        return str(
            column[0],
        )