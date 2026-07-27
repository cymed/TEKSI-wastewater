from ..interlis import config
from ..interlis.interlis_model_mapping.model_tww_od import ModelTwwOd
from ..interlis.interlis_model_mapping.model_interlis_dss import ModelInterlisDss
from ..interlis.interlis_model_mapping.model_interlis_sia405_abwasser import ModelInterlisSia405Abwasser
from ..interlis.interlis_model_mapping.model_interlis_sia405_base_abwasser import ModelInterlisSia405BaseAbwasser
from ..interlis.interlis_model_mapping.model_interlis_vsa_kek import ModelInterlisVsaKek
from ..interlis.interlis_model_mapping.model_interlis_ag64 import ModelInterlisAG64
from ..interlis.interlis_model_mapping.model_interlis_ag96 import ModelInterlisAG96


# plugin/teksi_wastewater/hooks_adapters/tww_relation_context_provider.py

from tww_hooks.services.relation_context_provider import (
    RelationContextProvider,
)
from tww_hooks.models.mapping import (
    RelationContext,
    ClassMapping,
)
from tww_hooks.capabilities.mapping import (
    DictionaryMappingCapability,
    ModelMappingCapability,
)

class TwwRelationContextProvider(RelationContextProvider):
    """
    Plugin-side provider that builds RelationContext objects from the
    concrete TEKSI Wastewater INTERLIS model classes.

    This adapter is intentionally plugin-specific. The core `tww_hooks`
    package only depends on the RelationContextProvider protocol.
    """

    def __init__(
        self,
        ili_model: str,
        dictionary_mapping: DictionaryMappingCapability,
        model_mapping: ModelMappingCapability,
        import_schema: str = config.IMPORT_SCHEMA,
        export_schema: str = config.EXPORT_SCHEMA,
    ):
        self.ili_model = ili_model
        self.groups = config.groups_for_models(
            self.ili_model,
        )

        if len(self.groups) != 1:
            raise ValueError(
                f"Expected exactly one model group for {ili_model!r}, "
                f"got {sorted(self.groups)!r}"
            )

        self.group = next(iter(self.groups))

        self.dictionary_mapping = dictionary_mapping
        self.model_mapping = model_mapping

        self.import_model = self._get_model(
            schema=import_schema,
        )

        self.export_model = self._get_model(
            schema=export_schema,
        )

    def relation_contexts(
        self,
    ) -> tuple[RelationContext, ...]:
        contexts: list[RelationContext] = []

        for relation in self.import_model.classes().values():
            contexts.append(
                RelationContext(
                    relation=relation,
                    class_mapping=self._class_mapping_for_relation(
                        relation,
                    ),
                )
            )

        return tuple(contexts)

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
        }.get(self.group)

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

        if {"ag64", "ag96"} & self.groups:
            mapping = self.model_mapping.try_class_definition(
                ili_class_name,
            )

            if mapping is not None:
                return mapping

        tww_class_id = self.dictionary_mapping.class_definition_for_ili(
            ili_class_name,
        )

        return ClassMapping(
            tww_class_id=tww_class_id,
            attributes={},
        )