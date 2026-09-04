from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from enum import StrEnum
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
            row["class_id"]: CanonicalClassMetadata(
                source_id=row["source_id"],
                identifier=row["class_id"],
                localized=self._localized_metadata(
                    row=row,
                    name_prefix="name",
                ),
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

        conditions = []
        parameters = []

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
            ): CanonicalAttributeMetadata(
                source_id=row["source_id"],
                identifier=row["attribute_id"],
                field_datatype=row.get(
                    "field_datatype",
                ),
                localized=self._localized_metadata(
                    row=row,
                    name_prefix="field_name",
                ),
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

        conditions = []
        parameters = []

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
            ): CanonicalValueMetadata(
                source_id=row["source_id"],
                identifier=row["value_id"],
                localized=self._localized_metadata(
                    row=row,
                    name_prefix="value_name",
                ),
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

        return CanonicalClassMetadata