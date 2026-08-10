from __future__ import annotations

from dataclasses import replace

from sqlalchemy import inspect
from sqlalchemy.exc import NoInspectionAvailable

from ...interlis import config
from ...interlis.interlis_model_mapping.model_interlis_ag64 import (
    ModelInterlisAG64,
)
from ...interlis.interlis_model_mapping.model_interlis_ag96 import (
    ModelInterlisAG96,
)
from ...interlis.interlis_model_mapping.model_interlis_dss import (
    ModelInterlisDss,
)
from ...interlis.interlis_model_mapping.model_interlis_sia405_abwasser import (
    ModelInterlisSia405Abwasser,
)
from ...interlis.interlis_model_mapping.model_interlis_sia405_base_abwasser import (
    ModelInterlisSia405BaseAbwasser,
)
from ...interlis.interlis_model_mapping.model_interlis_vsa_kek import (
    ModelInterlisVsaKek,
)

from tww_hooks.capabilities.mapping import (
    EffectiveModelMappingCapability,
)
from tww_hooks.models.canonical_object import (
    CanonicalIdentityMapping,
)
from tww_hooks.models.mapping import (
    AttributeMapping,
    ClassMapping,
    ForeignKeyMapping,
    RelationContext,
)
from tww_hooks.services.relation_context_provider import (
    RelationContextProvider,
)


class TwwRelationContextProvider(
    RelationContextProvider,
):
    """
    Plugin-side provider that builds RelationContext objects from concrete
    TEKSI Wastewater INTERLIS import model classes.

    The provider:

    - loads the SQLAlchemy/automap import model for the selected INTERLIS
      model group;
    - resolves the effective ClassMapping for each import relation;
    - enriches missing foreign-key AttributeMappings from SQLAlchemy automap
      relationship metadata.

    Mapping precedence is handled outside this class by
    EffectiveModelMappingCapability:

        explicit mapping > implicit dictionary mapping

    This provider only adds automap-derived FK mappings where no explicit
    source-attribute mapping already exists.
    """

    def __init__(
        self,
        ili_model: str,
        model_mapping: EffectiveModelMappingCapability,
        import_schema: str = config.IMPORT_SCHEMA,
    ):
        self.ili_model = ili_model

        self.groups = config.groups_for_models(
            self.ili_model,
        )

        if len(
            self.groups,
        ) != 1:
            raise ValueError(
                f"Expected exactly one model group for {ili_model!r}, "
                f"got {sorted(self.groups)!r}"
            )

        self.group = next(
            iter(
                self.groups,
            )
        )

        self.model_mapping = model_mapping

        self.import_model = self._get_model(
            schema=import_schema,
        )

    def relation_contexts(
        self,
    ) -> tuple[
        RelationContext,
        ...
    ]:
        contexts: list[
            RelationContext
        ] = []

        for relation in self.import_model.classes().values():
            contexts.append(
                RelationContext(
                    relation=relation,
                    class_mapping=self._class_mapping_for_relation(
                        relation,
                    ),
                )
            )

        return tuple(
            contexts,
        )

    def _get_model(
        self,
        schema: str,
    ):
        model_cls = {
            "dss": ModelInterlisDss,
            "vsa_kek": ModelInterlisVsaKek,
            "sia405_abwasser": ModelInterlisSia405Abwasser,
            "sia405_base_abwasser": ModelInterlisSia405BaseAbwasser,
            "ag64": ModelInterlisAG64,
            "ag96": ModelInterlisAG96,
        }.get(
            self.group,
        )

        if model_cls is None:
            raise ValueError(
                f"No model defined for group {self.group!r}"
            )

        return model_cls(
            schema=schema,
        )

    def _class_mapping_for_relation(
        self,
        relation,
    ) -> ClassMapping:
        ili_class_name = relation.__name__

        class_mapping = self.model_mapping.class_definition(
            ili_class_name,
        )

        return self._with_automap_foreign_keys(
            relation=relation,
            class_mapping=class_mapping,
        )

    def _with_automap_foreign_keys(
        self,
        *,
        relation,
        class_mapping: ClassMapping,
    ) -> ClassMapping:
        """
        Return class_mapping enriched with automap-derived FK AttributeMappings.

        Explicit mappings are preserved. Automap-derived mappings are only
        added for source attributes that are not already present in
        class_mapping.attributes.
        """

        foreign_key_mappings = self._automap_foreign_key_mappings(
            relation=relation,
            class_mapping=class_mapping,
        )

        if not foreign_key_mappings:
            return class_mapping

        attributes = dict(
            class_mapping.attributes,
        )

        for source_attribute, attribute_mapping in (
            foreign_key_mappings.items()
        ):
            attributes.setdefault(
                source_attribute,
                attribute_mapping,
            )

        return replace(
            class_mapping,
            attributes=attributes,
        )

    def _automap_foreign_key_mappings(
        self,
        *,
        relation,
        class_mapping: ClassMapping,
    ) -> dict[
        str,
        AttributeMapping,
    ]:
        if class_mapping.tww_class_id is None:
            return {}

        try:
            mapper = inspect(
                relation,
            )
        except NoInspectionAvailable:
            return {}

        mappings: dict[
            str,
            AttributeMapping,
        ] = {}

        for relationship in mapper.relationships:
            referenced_relation = relationship.mapper.class_
            referenced_ili_class_name = referenced_relation.__name__

            referenced_class_mapping = (
                self.model_mapping.try_class_definition(
                    referenced_ili_class_name,
                )
            )

            if referenced_class_mapping is None:
                continue

            if referenced_class_mapping.tww_class_id is None:
                continue

            referenced_identity = self._identity_mapping(
                referenced_class_mapping,
            )

            for local_column in relationship.local_columns:
                if not local_column.foreign_keys:
                    continue

                source_attribute = self._column_attribute_name(
                    local_column,
                )

                mappings[source_attribute] = AttributeMapping(
                    tww_class_id=class_mapping.tww_class_id,
                    tww_attr_id=source_attribute,
                    foreign_key=ForeignKeyMapping(
                        referenced_class_id=(
                            referenced_class_mapping.tww_class_id
                        ),
                        referenced_attribute_id=(
                            referenced_identity.canonical_attribute
                        ),
                    ),
                )

        return mappings

    def _identity_mapping(
        self,
        class_mapping: ClassMapping,
    ) -> CanonicalIdentityMapping:
        """
        Return the effective identity mapping for a class mapping.

        If the mapping does not explicitly define one, use the default
        ili2pg identity convention:

            t_ili_tid -> obj_id
        """

        if class_mapping.identity is not None:
            return class_mapping.identity

        return CanonicalIdentityMapping(
            source_attribute="t_ili_tid",
            canonical_attribute="obj_id",
        )

    def _column_attribute_name(
        self,
        column,
    ) -> str:
        """
        Return the source attribute name for a SQLAlchemy column.
        """

        return getattr(
            column,
            "key",
            None,
        ) or column.name