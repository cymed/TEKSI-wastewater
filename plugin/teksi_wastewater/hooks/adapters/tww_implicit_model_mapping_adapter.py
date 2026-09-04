from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum

from psycopg import sql

from teksi_hooks.capabilities.connection import (
    DatabaseConnectionFactory,
)
from teksi_hooks.capabilities.mapping import (
    ImplicitModelMappingCapability,
)
from teksi_hooks.models.mapping import (
    AttributeMapping,
    ClassMapping,
    ModelMapping,
    ValueMapping,
)


class TwwLanguage(
    StrEnum,
):
    """
    Languages supported by implicit TEKSI Wastewater model mappings.
    """

    DE = "de"
    FR = "fr"
    EN = "en"


@dataclass(slots=True)
class TwwImplicitModelMappingAdapter(
    ImplicitModelMappingCapability,
):
    """
    Database-backed provider for implicit canonical mappings.

    The adapter derives ModelMapping definitions from TWW dictionary metadata
    stored in ``tww_sys``.

    The resulting mappings are intended as fallback mappings when no explicit
    ModelMapping definition exists.

    Language-specific INTERLIS identifiers are resolved from dictionary
    columns such as ``ili_name_de``, ``ili_name_fr`` and ``ili_name_en``.
    """

    connection_factory: DatabaseConnectionFactory

    language: TwwLanguage = TwwLanguage.DE

    schema: str = "tww_sys"

    table_dictionary: str = "dictionary_od_table"

    attribute_dictionary: str = "dictionary_od_field"

    value_dictionary: str = "dictionary_od_values"

    _model_mapping: ModelMapping | None = field(
        init=False,
        default=None,
        repr=False,
    )

    def __post_init__(
        self,
    ) -> None:
        """
        Validate the configured language and load the implicit mapping.
        """

        try:
            self.language = TwwLanguage(
                self.language,
            )
        except ValueError as exception:
            raise ValueError(
                f"Unsupported language: {self.language!r}"
            ) from exception

        self._model_mapping = (
            self._load_model_mapping()
        )

    def model_mapping(
        self,
    ) -> ModelMapping:
        """
        Return the complete implicit model mapping.
        """

        if self._model_mapping is None:
            raise RuntimeError(
                "Implicit model mapping has not been loaded."
            )

        return self._model_mapping

    def class_mapping(
        self,
        ili_class_name: str,
    ) -> ClassMapping | None:
        """
        Return the implicit class mapping for one INTERLIS class.
        """

        return self.try_class_definition(
            ili_class_name,
        )

    def class_definition(
        self,
        class_id: str,
    ) -> ClassMapping:
        """
        Return the class mapping for a source-model class identifier.
        """

        class_mapping = self.try_class_definition(
            class_id,
        )

        if class_mapping is None:
            raise KeyError(
                f"Unknown class: {class_id!r}"
            )

        return class_mapping

    def try_class_definition(
        self,
        class_id: str,
    ) -> ClassMapping | None:
        """
        Return a class mapping if it exists.
        """

        return self.model_mapping().classes.get(
            class_id,
        )

    def attribute_definition(
        self,
        class_id: str,
        attribute_name: str,
    ) -> AttributeMapping:
        """
        Return the mapping for one source-model attribute.
        """

        attribute_mapping = (
            self.try_attribute_definition(
                class_id,
                attribute_name,
            )
        )

        if attribute_mapping is None:
            raise KeyError(
                f"Unknown attribute {attribute_name!r} "
                f"for class {class_id!r}"
            )

        return attribute_mapping

    def try_attribute_definition(
        self,
        class_id: str,
        attribute_name: str,
    ) -> AttributeMapping | None:
        """
        Return an attribute mapping if it exists.
        """

        class_mapping = self.try_class_definition(
            class_id,
        )

        if class_mapping is None:
            return None

        return class_mapping.attributes.get(
            attribute_name,
        )

    def value_mapping(
        self,
        class_id: str,
        attribute_name: str,
        value: str,
    ) -> ValueMapping:
        """
        Return the mapping for one source-model value.
        """

        value_mapping = self.try_value_mapping(
            class_id,
            attribute_name,
            value,
        )

        if value_mapping is None:
            raise KeyError(
                f"Unknown value {value!r} for "
                f"{class_id!r}.{attribute_name!r}"
            )

        return value_mapping

    def try_value_mapping(
        self,
        class_id: str,
        attribute_name: str,
        value: str,
    ) -> ValueMapping | None:
        """
        Return a value mapping if it exists.
        """

        attribute_mapping = (
            self.try_attribute_definition(
                class_id,
                attribute_name,
            )
        )

        if attribute_mapping is None:
            return None

        return attribute_mapping.values.get(
            value,
        )

    def _load_model_mapping(
        self,
    ) -> ModelMapping:
        """
        Load and assemble the complete implicit mapping.
        """

        attributes_by_class = (
            self._load_attribute_mappings()
        )

        values_by_attribute = (
            self._load_value_mappings()
        )

        classes: dict[
            str,
            ClassMapping,
        ] = {}

        ili_name_column = (
            self._ili_name_column()
        )

        query = sql.SQL(
            """
            SELECT
                tablename,
                {ili_name_column} AS ili_class_name
            FROM
                {schema}.{table_dictionary}
            ORDER BY
                tablename;
            """
        ).format(
            ili_name_column=sql.Identifier(
                ili_name_column,
            ),
            schema=sql.Identifier(
                self.schema,
            ),
            table_dictionary=sql.Identifier(
                self.table_dictionary,
            ),
        )

        for (
            canonical_class_id,
            ili_class_name,
        ) in self._fetchall(
            query,
        ):
            if not ili_class_name:
                continue

            attributes: dict[
                str,
                AttributeMapping,
            ] = {}

            for (
                ili_attribute_name,
                attribute_mapping,
            ) in attributes_by_class.get(
                ili_class_name,
                {},
            ).items():
                values = values_by_attribute.get(
                    (
                        ili_class_name,
                        ili_attribute_name,
                    ),
                    {},
                )

                attributes[
                    ili_attribute_name
                ] = AttributeMapping(
                    canonical_class_id=(
                        attribute_mapping
                        .canonical_class_id
                    ),
                    canonical_attr_id=(
                        attribute_mapping
                        .canonical_attr_id
                    ),
                    foreign_key=(
                        attribute_mapping
                        .foreign_key
                    ),
                    values=dict(
                        values,
                    ),
                )

            classes[
                ili_class_name
            ] = ClassMapping(
                canonical_class_id=(
                    canonical_class_id
                ),
                attributes=attributes,
            )

        return ModelMapping(
            classes=classes,
            is_ssot=False,
        )

    def _load_attribute_mappings(
        self,
    ) -> dict[
        str,
        dict[
            str,
            AttributeMapping,
        ],
    ]:
        """
        Load implicit mappings for canonical attributes.
        """

        ili_name_column = (
            self._ili_name_column()
        )

        query = sql.SQL(
            """
            SELECT
                t.tablename AS canonical_class_id,
                a.field_name AS canonical_attr_id,
                t.{ili_name_column} AS ili_class_name,
                a.{ili_name_column} AS ili_attribute_name
            FROM
                {schema}.{attribute_dictionary} AS a
            JOIN
                {schema}.{table_dictionary} AS t
                    ON t.id = a.class_id
            ORDER BY
                t.tablename,
                a.field_name;
            """
        ).format(
            ili_name_column=sql.Identifier(
                ili_name_column,
            ),
            schema=sql.Identifier(
                self.schema,
            ),
            attribute_dictionary=sql.Identifier(
                self.attribute_dictionary,
            ),
            table_dictionary=sql.Identifier(
                self.table_dictionary,
            ),
        )

        classes: dict[
            str,
            dict[
                str,
                AttributeMapping,
            ],
        ] = {}

        for (
            canonical_class_id,
            canonical_attr_id,
            ili_class_name,
            ili_attribute_name,
        ) in self._fetchall(
            query,
        ):
            if (
                not ili_class_name
                or not ili_attribute_name
            ):
                continue

            classes.setdefault(
                ili_class_name,
                {},
            )[
                ili_attribute_name
            ] = AttributeMapping(
                canonical_class_id=(
                    canonical_class_id
                ),
                canonical_attr_id=(
                    canonical_attr_id
                ),
            )

        return classes

    def _load_value_mappings(
        self,
    ) -> dict[
        tuple[
            str,
            str,
        ],
        dict[
            str,
            ValueMapping,
        ],
    ]:
        """
        Load implicit mappings for canonical value-list values.
        """

        ili_name_column = (
            self._ili_name_column()
        )

        query = sql.SQL(
            """
            SELECT
                t.{ili_name_column} AS ili_class_name,
                f.{ili_name_column} AS ili_attribute_name,
                v.{ili_name_column} AS ili_value_name,
                v.value_id AS canonical_value_id,
                v.value_name AS canonical_value_name
            FROM
                {schema}.{value_dictionary} AS v
            JOIN
                {schema}.{table_dictionary} AS t
                    ON t.id = v.class_id
            JOIN
                {schema}.{attribute_dictionary} AS f
                    ON f.class_id = v.class_id
                   AND f.attribute_id = v.attribute_id
            ORDER BY
                ili_class_name,
                ili_attribute_name,
                ili_value_name;
            """
        ).format(
            ili_name_column=sql.Identifier(
                ili_name_column,
            ),
            schema=sql.Identifier(
                self.schema,
            ),
            value_dictionary=sql.Identifier(
                self.value_dictionary,
            ),
            table_dictionary=sql.Identifier(
                self.table_dictionary,
            ),
            attribute_dictionary=sql.Identifier(
                self.attribute_dictionary,
            ),
        )

        mappings: dict[
            tuple[
                str,
                str,
            ],
            dict[
                str,
                ValueMapping,
            ],
        ] = {}

        for (
            ili_class_name,
            ili_attribute_name,
            ili_value_name,
            canonical_value_id,
            canonical_value_name,
        ) in self._fetchall(
            query,
        ):
            if (
                not ili_class_name
                or not ili_attribute_name
                or not ili_value_name
            ):
                continue

            mappings.setdefault(
                (
                    ili_class_name,
                    ili_attribute_name,
                ),
                {},
            )[
                ili_value_name
            ] = ValueMapping(
                canonical_value_id=(
                    canonical_value_id
                ),
                value=canonical_value_name,
            )

        return mappings

    def _fetchall(
        self,
        query,
    ) -> list[
        tuple,
    ]:
        """
        Execute a read-only query and return all rows.

        Implicit model metadata is loaded using an autocommit connection
        because the adapter performs only independent read operations.
        """

        with self.connection_factory.connection(
            autocommit=True,
        ) as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    query,
                )

                return cursor.fetchall()

    def _ili_name_column(
        self,
    ) -> str:
        """
        Return the dictionary column containing localized INTERLIS names.
        """

        return (
            f"ili_name_{self.language.value}"
        )