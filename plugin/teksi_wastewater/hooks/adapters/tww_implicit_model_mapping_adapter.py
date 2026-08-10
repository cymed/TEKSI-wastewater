from tww_hooks.capabilities import ImplicitModelMappingCapability

from ...utils.database_utils import (
    DatabaseUtils,
)

@dataclass(slots=True)
class TwwImplicitModelMappingAdapter(ImplicitModelMappingCapability):

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
            lang: str = "de",
        ):

        """
        Initialize the dictionary mapping capability.

        Parameters
        ----------
        lang:
            Language suffix used for INTERLIS identifier columns.
            Supported values are `de`, `fr` and `en`.
        """

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


    @property
    def table_mapping(
        self,
    ) -> dict[str, str]:
        return self._table_mapping


    @property
    def attribute_mapping(
        self,
    ) -> dict[
        tuple[str, str],
        tuple[str, str],
    ]:
        return self._attribute_mapping


    @property
    def value_mapping(
        self,
    ) -> dict[
        tuple[str, str, str],
        tuple[str, str, str],
    ]:
        return self._value_mapping
 
    def class_mapping_for_ili(
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

    def attribute_mapping_for_ili(
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

    def value_mapping_for_ili(
        self,
        ili_class: str,
        ili_attribute: str,
        ili_value: str,
    ) -> tuple[
        str,
        str,
        str,
    ]:
        """
        Return the canonical TWW value mapping for an INTERLIS value.

        Parameters
        ----------
        ili_class:
            INTERLIS class identifier in the configured language.

        ili_attribute:
            INTERLIS attribute identifier in the configured language.

        ili_value:
            INTERLIS value identifier in the configured language.

        Returns
        -------
        tuple[str, str, str]
            Tuple containing:

            - canonical class identifier
            - canonical attribute identifier
            - canonical value identifier
        """

        return self._value_mapping[
            (
                ili_class,
                ili_attribute,
                ili_value,
            )
        ]

    def try_value_mapping_for_ili(
        self,
        ili_class: str,
        ili_attribute: str,
        ili_value: str,
    ) -> tuple[
        str,
        str,
        str,
    ] | None:
        """
        Return the canonical TWW value mapping if it exists.
        """

        return self._value_mapping.get(
            (
                ili_class,
                ili_attribute,
                ili_value,
            )
        )

    def _load_value_mapping(
        self,
    ) -> dict[
        tuple[
            str,
            str,
            str,
        ],
        tuple[
            str,
            str,
            str,
        ],
    ]:
        """
        Load INTERLIS value to canonical TWW value mappings.

        Returns
        -------
        dict[tuple[str, str, str], tuple[str, str, str]]
            Mapping from:

                (ili_class, ili_attribute, ili_value)

            to:

                (tww_class_id, tww_attr_id, tww_value_id)

        The INTERLIS names are only an intermediate bridge. The resulting
        ModelMapping should ultimately be keyed by the actual ili2pg runtime
        class and attribute names.
        """

        query = """
            SELECT
                t.tablename,
                f.field_name,
                v.value_name,
                t.ili_name_{lang} AS ili_cls_name,
                f.ili_name_{lang} AS ili_attr_name,
                v.ili_name_{lang} AS ili_value_name
            FROM {schema}.{metadata_vals} v
            INNER JOIN {schema}.{metadata_tbl} t
                ON t.id = v.class_id
            INNER JOIN {schema}.{metadata_attr} f
                ON f.class_id = v.class_id
               AND f.attribute_id = v.attribute_id;
            """.format(
            lang=self.lang,
            schema=self.schema,
            metadata_vals=self.metadata_vals,
            metadata_tbl=self.metadata_tbl,
            metadata_attr=self.metadata_attr,
        )

        mapping: dict[
            tuple[
                str,
                str,
                str,
            ],
            tuple[
                str,
                str,
                str,
            ],
        ] = {}

        for (
            table_name,
            field_name,
            value_name,
            ili_cls_name,
            ili_attr_name,
            ili_value_name,
        ) in DatabaseUtils.fetchall(
            query,
        ):
            if (
                ili_cls_name is None
                or ili_attr_name is None
                or ili_value_name is None
            ):
                continue

            mapping[
                (
                    ili_cls_name,
                    ili_attr_name,
                    ili_value_name,
                )
            ] = (
                table_name,
                field_name,
                value_name,
            )

        return mapping
        ¨
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
        
        rows = DatabaseUtils.fetchall(query)

        return {
            ili_name: tablename
            for tablename, ili_name in rows
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
                t.tablename,
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
        ) in DatabaseUtils.fetchall(query):
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
    