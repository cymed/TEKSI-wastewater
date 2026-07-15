from teksi_hooks.capabilities import SqlCapability
from ..models.validation import Change, RelationMapping
from ..capabilities.mapping import DictionaryMappingCapability, ModelMappingCapability
from ...interlis import config
from ...interlis.interlis_model_mapping.model_base import ModelBase
from ...interlis.interlis_model_mapping.model_tww_od import ModelTwwOd
from ...interlis.interlis_model_mapping.model_interlis_dss import ModelInterlisDss
from ...interlis.interlis_model_mapping.model_interlis_sia405_abwasser import ModelInterlisSia405Abwasser
from ...interlis.interlis_model_mapping.model_interlis_sia405_base_abwasser import ModelInterlisSia405BaseAbwasser
from ...interlis.interlis_model_mapping.model_interlis_vsa_kek import ModelInterlisVsaKek
from ...interlis.interlis_model_mapping.model_interlis_ag64 import ModelInterlisAG64
from ...interlis.interlis_model_mapping.model_interlis_ag96 import ModelInterlisAG96


class ChangeLoader:
    def __init__(
            self,
            ili_model: str,
            sql: SqlCapability,
            dictionary_mapping: DictionaryMappingCapability,
            model_mapping: ModelMappingCapability,
            import_schema: str = config.IMPORT_SCHEMA,
            export_schema: str = config.EXPORT_SCHEMA,
            live_schema: str = "tww_od",
            ):
        self.live_model = ModelTwwOd(schema=live_schema)
        self.ili_model = ili_model
        self.sql = sql
        self.groups = config.groups_for_models(self.ili_model)
        self.group = next(iter(self.groups))
        self.dictionary_mapping=dictionary_mapping
        self.model_mapping=model_mapping
        
        self.import_model = self._get_models(schema=import_schema)
        self.export_model = self._get_models(schema=export_schema)

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
                f"No model defined for groups {self.groups}"
            )

        return model_cls(schema=schema)

        
    def load(
        self,
    ) -> tuple[Change, ...]:
        changes: list[Change] = []
        for mapping in self._mappings():
            changes.extend(self._load_inserts(mapping))
            changes.extend(self._load_updates(mapping))
            changes.extend(self._load_deletes(mapping))

        return tuple(changes)

    def _load_inserts(
        self,
        sql: SqlCapability,
    ):
        pass
    
    def _load_updates(
        self,
        sql: SqlCapability,
    ):
        pass

    def _load_deletes(
        self,
        sql: SqlCapability,
    ):
        pass


    def _mappings(self):
        yield from self._relation_mappings()

        if {"ag64", "ag96"} & self.groups:
            yield from self._model_mappings()

    def _relation_mappings(
        self,
    ) -> tuple[RelationMapping, ...]:

        mappings: list[RelationMapping] = []

        for relation in self.import_model.classes().values():  
            ili_name = relation.__name__
            od_table = (
                self.dictionary_mapping
                .od_table_for_ili(ili_name)
            )

            mappings.append(
                RelationMapping(
                    relation_name=od_table,
                    live_relation=getattr(
                        self.live_model.classes(),
                        od_table,
                    ),
                    quarantine_relation=relation,
                    pk_attribute=self._pk_attribute(
                        relation,
                    ),
                )
            )


        return tuple(mappings)
    
    def _model_mappings(
        self,
    ) -> tuple[RelationMapping, ...]:

        mappings: list[RelationMapping] = []

        for relation in self.import_model.classes().values():  
            ili_name = relation.__name__
            od_table = (
                self.dictionary_mapping
                .od_table_for_ili(ili_name)
            )

            mappings.append(
                RelationMapping(
                    relation_name=od_table,
                    live_relation=getattr(
                        self.live_model.classes(),
                        od_table,
                    ),
                    quarantine_relation=relation,
                    pk_attribute=self._pk_attribute(
                        relation,
                    ),
                )
            )


        return tuple(mappings)
