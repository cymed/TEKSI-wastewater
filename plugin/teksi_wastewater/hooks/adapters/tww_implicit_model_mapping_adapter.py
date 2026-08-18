from __future__ import annotations

from dataclasses import dataclass, field

from teksi_hooks.models.mapping import (
    AttributeMapping,
    ClassMapping,
    ModelMapping,
    ValueMapping,
)

from ...utils.database_utils import (
    DatabaseUtils,
)


@dataclass(slots=True)
class TwwImplicitModelMappingAdapter:
    """
    Database-backed provider for implicit canonical mappings.

    The adapter derives ModelMapping definitions directly from TWW
    dictionary metadata stored in tww_sys.

    The resulting mappings are intended as a fallback source when no
    explicit ModelMapping definition exists.

    Language-specific INTERLIS identifiers are resolved from dictionary
    columns such as:

    - ili_name_de
    - ili_name_fr
    - ili_name_en
    """

    language: str = "de"
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
        allowed_languages = {
            "de",
            "fr",
            "en",
        }

        if self.language not in allowed_languages:
            raise ValueError(
                f"Unsupported language: {self.language!r}"
            )

        self._model_mapping = self._load_model_mapping()

    def model_mapping(
        self,
    ) -> ModelMapping:
        """
        Return the complete implicit model mapping.
        """
        return self._model_mapping

    def class_mapping(
        self,
        ili_class_name: str,
    ) -> ClassMapping | None:
        """
        Return the implicit class mapping for one INTERLIS class.
        """
        return self._model_mapping.classes.get(
            ili_class_name,
        )

    def _load_model_mapping(
        self,
    ) -> ModelMapping:
        classes = self._load_class_mappings()

        value_mappings = self._load_value_mappings()

        for (
            ili_class_name,
            ili_attribute_name,
        ), values in value_mappings.items():
            class_mapping = classes.get(
                ili_class_name,
            )

            if class_mapping is None:
                continue

            attribute_mapping = class_mapping.attributes.get(
                ili_attribute_name,
            )

            if attribute_mapping is None:
                continue

            class_mapping.attributes[
                ili_attribute_name
            ] = AttributeMapping(
                canonical_class_id=attribute_mapping.canonical_class_id,
                canonical_attr_id=attribute_mapping.canonical_attr_id,
                foreign_key=attribute_mapping.foreign_key,
                values=values,
            )

        return ModelMapping(
            classes=classes,
            is_ssot=False,
        )

    def _load_class_mappings(
        self,
    ) -> dict[
        str,
        ClassMapping,
    ]:
        classes: dict[
            str,
            ClassMapping,
        ] = {}

        attributes_by_class = self._load_attribute_mappings()

        query = f"""
            SELECT
                tablename,
                ili_name_{self.language}
            FROM
                {self.schema}.{self.table_dictionary}
        """

        for canonical_class_id, ili_class_name in (
            DatabaseUtils.fetchall(
                query,
            )
        ):
            if not ili_class_name:
                continue

            classes[
                ili_class_name
            ] = ClassMapping(
                canonical_class_id=canonical_class_id,
                attributes=attributes_by_class.get(
                    ili_class_name,
                    {},
                ),
            )

        return classes

    def _load_attribute_mappings(
        self,
    ) -> dict[
        str,
        dict[
            str,
            AttributeMapping,
        ],
    ]:
        query = f"""
            SELECT
                t.tablename,
                a.field_name,
                t.ili_name_{self.language},
                a.ili_name_{self.language}
            FROM
                {self.schema}.{self.attribute_dictionary} a
            JOIN
                {self.schema}.{self.table_dictionary} t
                    ON t.id = a.class_id
        """

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
        ) in DatabaseUtils.fetchall(
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
                canonical_class_id=canonical_class_id,
                canonical_attr_id=canonical_attr_id,
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
        query = f"""
            SELECT
                t.ili_name_{self.language},
                f.ili_name_{self.language},
                v.ili_name_{self.language},
                v.value_name
            FROM
                {self.schema}.{self.value_dictionary} v
            JOIN
                {self.schema}.{self.table_dictionary} t
                    ON t.id = v.class_id
            JOIN
                {self.schema}.{self.attribute_dictionary} f
                    ON f.class_id = v.class_id
                   AND f.attribute_id = v.attribute_id
        """

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
        ) in DatabaseUtils.fetchall(
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
                canonical_value_id=canonical_value_id,
                value=canonical_value_id,
            )

        return mappings