
from dataclasses import dataclass

from teksi_hooks.capabilities import SqlCapability

from ..models.mapping import (
    AttributeMapping,
    ClassMapping,
    ValueMapping,
    ModelMapping,
)



@dataclass(slots=True, frozen=True)
class ModelMappingCapability:
    """
    Runtime lookup capability for a `ModelMapping`.

    A model mapping describes how a source model maps to the canonical
    internal TWW model. This capability provides convenient accessors for
    class, attribute and value mappings.

    The mapping itself is immutable and should already be parsed or resolved
    before this capability is created.
    """
    mapping: ModelMapping


    def class_definition(
        self,
        class_id: str,
    ) -> ClassMapping:
        """
        Return the class mapping for a source-model class identifier.

        Parameters
        ----------
        class_id:
            Source-model class identifier.

        Raises
        ------
        KeyError
            If the source class is unknown in this mapping.
        """

        try:
            return self.mapping.classes[class_id]
        except KeyError as exc:
            raise KeyError(
                f"Unknown class: {class_id}"
            ) from exc

    def try_class_definition(
        self,
        class_id: str,
    ) -> ClassMapping | None:
        """
        Return a class mapping if it exists, otherwise `None`.
        """

        return self.mapping.classes.get(class_id)

    def attribute_definition(
        self,
        class_id: str,
        attribute_name: str,
    ) -> AttributeMapping:
        """
        Return the attribute mapping for a source-model attribute.

        Parameters
        ----------
        class_id:
            Source-model class identifier.

        attribute_name:
            Source-model attribute identifier.

        Raises
        ------
        KeyError
            If the class or attribute is unknown in this mapping.
        """
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
    ) -> AttributeMapping | None:
        """
        Return an attribute mapping if it exists, otherwise `None`.
        """

        cls = self.mapping.classes.get(class_id)
        if cls is None:
            return None

        return cls.attributes.get(attribute_name)

    def value_mapping(
        self,
        class_id: str,
        attribute_name: str,
        value: str,
    ) -> ValueMapping:
        """
        Return the value mapping for a source-model value.

        Parameters
        ----------
        class_id:
            Source-model class identifier.

        attribute_name:
            Source-model attribute identifier.

        value:
            Source-model value.

        Raises
        ------
        KeyError
            If the class, attribute or value is unknown.
        """

        return self.attribute_definition(
            class_id,
            attribute_name,
        ).values[value]

    def try_value_mapping(
        self,
        class_id: str,
        attribute_name: str,
        value: str,
    ) -> ValueMapping | None:

        """
        Return a value mapping if it exists, otherwise `None`.
        """


        attribute = self.try_attribute_definition(
            class_id,
            attribute_name,
        )

        if attribute is None:
            return None

        return attribute.values.get(value)


@dataclass(slots=True)
class DictionaryMappingCapability:

    """
    Database-backed mapping capability for TWW dictionary metadata.

    This capability reads metadata from the TWW dictionary tables and exposes
    lookup methods for resolving INTERLIS class, attribute and value names to
    canonical internal TWW identifiers.

    The current implementation expects the dictionary tables to expose
    language-specific INTERLIS identifier columns such as:

    - `ili_name_de`
    - `ili_name_fr`
    - `ili_name_en`

    Loaded mappings are cached in memory during initialization.
    """

    def __init__(
            self,
            sql: SqlCapability,
            lang: str = "de",
        ):

        """
        Initialize the dictionary mapping capability.

        Parameters
        ----------
        sql:
            SQL capability used to read dictionary metadata.

        lang:
            Language suffix used for INTERLIS identifier columns.
            Supported values are `de`, `fr` and `en`.
        """

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

        self._table_mapping = self._load_table_mapping()
        self._attribute_mapping = self._load_attribute_mapping()
        self._value_mapping = self._load_value_mapping()

        self.model_mapping = self._load_model_mapping()
 
    def tww_table_for_ili(
        self,
        ili_name: str,
    ) -> str:
        """
        Return the canonical TWW table/class identifier for an INTERLIS class.

        Parameters
        ----------
        ili_name:
            INTERLIS class identifier in the configured language.

        Returns
        -------
        str
            Canonical TWW class/table identifier.
        """

        return self._table_mapping[ili_name]

    def tww_field_for_ili(
        self,
        ili_class: str,
        ili_attribute: str,
    ) -> tuple[str, str]:
        
        """
        Return the canonical TWW table and field for an INTERLIS attribute.

        Parameters
        ----------
        ili_class:
            INTERLIS class identifier.

        ili_attribute:
            INTERLIS attribute identifier.

        Returns
        -------
        tuple[str, str]
            A tuple containing `(table_name, field_name)`.
        """

        return self._attribute_mapping[
                (ili_class, ili_attribute)
            ]

    def tww_value_for_ili(
        self,
        ili_class: str,
        ili_attribute: str,
        ili_value: str,
    ) -> tuple[str, str, str]:
        """
        Return the canonical TWW value mapping for an INTERLIS value.

        Parameters
        ----------
        ili_class:
            INTERLIS class identifier.

        ili_attribute:
            INTERLIS attribute identifier.

        ili_value:
            INTERLIS value identifier.

        Returns
        -------
        tuple[str, str, str]
            Intended to return `(table_name, field_name, value_name)` or a
            similar canonical value tuple. Exact return shape may be adjusted
            once value mapping is implemented.
        """

        raise NotImplementedError(
            "Value mapping is not implemented yet."
        )


    def value_for_source(
        self,
        *,
        tww_class_id: str,
        tww_attr_id: str,
        source_value: str,
    ) -> ValueMapping | None:
        pass
    
    def _load_table_mapping(self):
        """
        Load INTERLIS class to canonical TWW table mappings.

        Returns
        -------
        dict[str, str]
            Mapping from INTERLIS class identifier to canonical TWW table name.
        """

        query = """
            SELECT
                tablename,
                ili_name_{lang}
            FROM {schema}.{metadata_tbl};
            """.format(lang=self.lang,schema=self.schema, metadata_tbl=self.metadata_tbl)
        
        rows = self.sql.fetchall(query)

        return {
            ili_name: tablename
            for ili_name, tablename in rows
        }

    
    def _load_attribute_mapping(self):
        """
        Load INTERLIS attribute to canonical TWW field mappings.

        Returns
        -------
        dict[tuple[str, str], tuple[str, str]]
            Mapping from `(ili_class, ili_attribute)` to
            `(table_name, field_name)`.
        """

        query = """
            SELECT
                a.tablename,
                a.field_name,
                t.ili_name_{lang} as ili_cls_name,
                a.ili_name_{lang} as ili_attr_name
            FROM {schema}.{metadata_attr} a
            INNER JOIN {schema}.{metadata_tbl} t on a.class_id=t.id;
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
        """
        Load INTERLIS value to canonical TWW value mappings.

        This is currently a placeholder. It should eventually return a mapping
        keyed by `(ili_class, ili_attribute, ili_value)`.
        """
        raise NotImplementedError(
            "Value mapping loading is not implemented yet."
        )