from dataclasses import dataclass

from collections.abc import Mapping
from teksi_hooks.capabilities import SqlCapability
from ..models.mapping import (
    MappingAttribute,
    MappingClass,
    MappingTarget,
    ModelMapping
)


@dataclass(slots=True, frozen=True)
class ModelMappingCapability:
    mapping: ModelMapping

    def class_definition(
        self,
        class_id: str,
    ) -> MappingClass:
        try:
            return self.mapping.classes[class_id]
        except KeyError as exc:
            raise KeyError(
                f"Unknown class: {class_id}"
            ) from exc

    def attribute_definition(
        self,
        class_id: str,
        attribute_name: str,
    ) -> MappingAttribute:
        cls = self.class_definition(class_id)

        try:
            return cls.attributes[attribute_name]
        except KeyError as exc:
            raise KeyError(
                f"Unknown attribute "
                f"{attribute_name!r} "
                f"for class {class_id!r}"
            ) from exc

    def try_attribute_definition(
        self,
        class_id: str,
        attribute_name: str,
    ) -> MappingAttribute | None:
        cls = self.mapping.classes.get(class_id)
        if cls is None:
            return None

        return cls.attributes.get(attribute_name)

    def targets(
        self,
        class_id: str,
        attribute_name: str,
    ) -> tuple[MappingTarget, ...]:
        return self.attribute_definition(
            class_id,
            attribute_name,
        ).targets

@dataclass(slots=True)
class DictionaryMappingCapability:

    def __init__(
            self,
            sql: SqlCapability,
            lang: str = "de",
        ):
        self.sql=sql
        self.lang=lang
        ALLOWED_LANGS = {"de", "fr", "en"}
        if self.lang not in ALLOWED_LANGS:
            raise ValueError(
                f"Unsupported language: {self.lang}"
            )
        self.schema="tww_sys"
        self.metadata_tbl="dictionary_od_table"
        self.metadata_attr="dictionary_od_field"
        self.metadata_vals="dictionary_od_values"

    def __post_init__(self):
        self._table_mapping = self._load_table_mapping()
        self._attribute_mapping = self._load_attribute_mapping()
        self._value_mapping = self._load_value_mapping()
 
    def od_table_for_ili(
        self,
        ili_name: str,
    ) -> str:
        return self._table_mapping[ili_name]

    def od_field_for_ili(
        self,
        ili_class: str,
        ili_attribute: str,
    ) -> tuple[str, str]:
        
        return self._attribute_mapping[
                (ili_class, ili_attribute)
            ]


    def od_value_for_ili(
        self,
        ili_class: str,
        ili_attribute: str,
        ili_value: str,
    ) -> tuple[str, str, str]:
        pass
        # return self._value_mapping[ili_class, ili_attribute, ili_value]
    
    def _load_table_mapping(self):
        query = """
            SELECT
                tablename,
                ili_name_{lang}
            FROM {schema}.{meta_tbl};
            """.format(lang=self.lang,schema=self.schema, meta_tbl=self.meta_tbl)
        
        rows = self.sql.fetchall(query)

        return {
            ili_name: tablename
            for ili_name, tablename in rows
        }

    
    def _load_attribute_mapping(self):
        query = """
            SELECT
                a.tablename,
                a.field_name,
                t.ili_name_{lang} as ili_cls_name,
                a.ili_name_{lang} as ili_attr_name
            FROM {schema}.{metadata_attr} a
            INNER JOIN {schema}.{meta_tbl} t on a.class_id=t.id;
            """.format(
                lang=self.lang,
                schema=self.schema,
                metadata_attr=self.metadata_attr,
                metadata_tbl=self.metadata_tbl,
            )
        
        mapping: dict[
            tuple[str, str],
            tuple[str, str],
        ] = {}

        for (
            table_name,
            field_name,
            ili_cls_name,
            ili_attr_name,
        ) in self.sql.fetchall(query):
            mapping[
                (
                    ili_cls_name,
                    ili_attr_name,
                )
            ] = (
                table_name,
                field_name,
            )

        return mapping

    
    def _load_value_mapping(self):
        pass