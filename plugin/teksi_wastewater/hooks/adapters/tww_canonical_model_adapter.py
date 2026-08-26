from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from teksi_hooks.models.canonical_object import (
    CanonicalAttributeMetadata,
    CanonicalClassMetadata,
    CanonicalModelMetadata,
    CanonicalValueMetadata,
    LocalizedMetadata,
)

from ...utils.database_utils import (
    DatabaseUtils,
)


class TwwLanguage(StrEnum):
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
    in tww_sys remains in the wastewater adapter.
    """

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

        query = DatabaseUtils.compose_sql(
            """
            SELECT
                t.id AS source_id,
                t.tablename AS class_id,
                t.name_de,
                t.name_fr,
                t.name_it,
                t.name_en
            FROM {schema}.dictionary_od_table t
            ORDER BY
                t.tablename
            """,
            schema=DatabaseUtils.wrap_identifier(
                self.schema,
            ),
        )

        rows = DatabaseUtils.fetchall_dict(
            query,
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

        where_clause = self._class_where_clause(
            class_id,
        )

        query = DatabaseUtils.compose_sql(
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
            where_clause=where_clause,
        )

        rows = DatabaseUtils.fetchall_dict(
            query,
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
            for row in rows if (
                class_id is None or
                row["class_id"] == class_id
                )
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

        where_clause = self._where_clause(
            where_parts,
        )

        query = DatabaseUtils.compose_sql(
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
        )

        rows = DatabaseUtils.fetchall_dict(
            query,
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
            for row in rows if (
                attribute_id is None or
                row["attribute_id"] == attribute_id
                ) and  (
                class_id is None or
                row["class_id"] == class_id
                )
        }

    def class_metadata(
        self,
        class_id: str,
    ) -> CanonicalClassMetadata | None:
        """
        Return metadata for one canonical class.
        """

        return self.classes().get(
            class_id,
        )

    def attribute_metadata(
        self,
        class_id: str,
        attribute_id: str,
    ) -> CanonicalAttributeMetadata | None:
        """
        Return metadata for one canonical attribute.
        """

        return self.attributes(
            class_id=class_id,
        ).get(
            (
                class_id,
                attribute_id,
            )
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

        return self.values(
            class_id=class_id,
            attribute_id=attribute_id,
        ).get(
            (
                class_id,
                attribute_id,
                value_id,
            )
        )

    def geometry_attribute_names(
        self,
        class_id: str,
    ) -> tuple[
        str,
        ...,
    ]:
        """
        Return canonical geometry attribute identifiers for one class.
        """

        return tuple(
            attribute.identifier
            for attribute in self.attributes(
                class_id=class_id,
            ).values()
            if self._is_geometry_datatype(
                attribute.field_datatype,
            )
        )

    def is_geometry_attribute(
        self,
        class_id: str,
        attribute_id: str,
    ) -> bool:
        """
        Return whether an attribute is a geometry attribute.
        """

        attribute = self.attribute_metadata(
            class_id=class_id,
            attribute_id=attribute_id,
        )

        if attribute is None:
            return False

        return self._is_geometry_datatype(
            attribute.field_datatype,
        )

    def _localized_metadata(
        self,
        *,
        row: dict,
        name_prefix: str,
    ) -> LocalizedMetadata:
        """
        Build generic localized metadata from TWW dictionary columns.
        """

        names = {
            language.value: value
            for language in self.languages
            if (
                value := row.get(
                    f"{name_prefix}_{language.value}",
                )
            )
        }

        return LocalizedMetadata(
            names=names,
        )

    def _is_geometry_datatype(
        self,
        field_datatype: str | None,
    ) -> bool:
        if field_datatype is None:
            return False

        return (
            field_datatype.strip().lower()
            == "geometry"
        )

    def _class_where_clause(
        self,
        class_id: str | None,
    ):
        if class_id is None:
            return DatabaseUtils.compose_sql(
                "",
            )

        return DatabaseUtils.compose_sql(
            "WHERE t.tablename = {class_id}",
            class_id=DatabaseUtils.wrap_literal(
                class_id,
            ),
        )

    def _where_clause(
        self,
        where_parts,
    ):
        if not where_parts:
            return DatabaseUtils.compose_sql(
                "",
            )

        return DatabaseUtils.compose_sql(
            "WHERE {conditions}",
            conditions=DatabaseUtils.compose_sql(
                " AND ",
            ).join(
                where_parts,
            ),
        )