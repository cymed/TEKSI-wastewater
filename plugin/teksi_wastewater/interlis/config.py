from collections.abc import Iterable
import os
from dataclasses import dataclass

BASE = os.path.dirname(__file__)

ILIVALIDATOR = os.path.join(BASE, "bin", "ilivalidator-1.15.0.jar")

TWW_DEFAULT_PGSERVICE = "pg_tww"
TWW_OD_SCHEMA = "tww_od"
TWW_VL_SCHEMA = "tww_vl"
TWW_SYS_SCHEMA = "tww_sys"
EXPORT_SCHEMA = "tww_app_pg2xtf"
IMPORT_SCHEMA = "tww_app_xtf2pg"
TWW_APP_SCHEMA = "tww_app"


@dataclass(frozen=True)
class InterlisLangModel:
    lang: str
    model: str
    topics: frozenset[str] = frozenset()


@dataclass(frozen=True)
class InterlisModel:
    models: frozenset[InterlisLangModel]


    @property
    def names(self) -> frozenset[str]:
        return frozenset(
            model.model
            for model in self.models
        )

    @property
    def topics(self) -> frozenset[str]:
        return frozenset(
            topic
            for model in self.models
            for topic in model.topics
        )
    
    def lang_name(self, lang:str):
        return next(
            model.model
            for model in self.models
            if model.lang == lang
        )



interlis_models = {
    "dss": InterlisModel(
            models=frozenset({
            InterlisLangModel(
                lang="de",
                model="DSS_2020_1_LV95",
                topics=frozenset({
                    "Siedlungsentwaesserung",
                }),
            ),
            InterlisLangModel(
                lang="fr",
                model="SDEE_2020_1_LV95",
                topics=frozenset({
                    "evacuation_des_eaux_des_agglomerations",
                }),
            ),
        }),
    ),
    "vsa_kek": InterlisModel(
            models=frozenset({
            InterlisLangModel(
                lang="de",
                model="VSA_KEK_2020_1_LV95",
                topics=frozenset({
                    "KEK",
                }),
            ),
            InterlisLangModel(
                lang="fr",
                model="VSA_IVI_2020_1_LV95 ",
                topics=frozenset({
                    "IVI",
                }),
            ),
        }),
    ),
    "sia405_abwasser": InterlisModel(
            models=frozenset({
            InterlisLangModel(
                lang="de",
                model="SIA405_ABWASSER_2020_1_LV95",
                topics=frozenset({
                    "SIA405_Abwasser",
                }),
            ),
            InterlisLangModel(
                lang="fr",
                model="SIA405_Eaux_usees_1_LV95",
                topics=frozenset({
                    "SIA405_Eaux_usees",
                }),
            ),
        }),
    ),
    "sia405_base_abwasser": InterlisModel(
            models=frozenset({
            InterlisLangModel(
                lang="de",
                model="SIA405_Base_Abwasser_1_LV95",
                topics=frozenset({
                    "Administration",
                }),
            ),
            InterlisLangModel(
                lang="fr",
                model="SIA405_Base_Eaux_usees_1_LV95",
                topics=frozenset({
                    "Administration",
                }),
            ),
        }),
    ),
    "sia405_cable": InterlisModel(
            models=frozenset({
            InterlisLangModel(
                lang="de",
                model="SIA405_FERNWIRKKABEL_2015_LV95",
                topics=frozenset({
                    "SIA405_Fernwirkkabel",
                }),
            ),
            InterlisLangModel(
                lang="fr",
                model="SIA405_CABLE_DE_CONTROLE_A_DISTANCE_2015",
                topics=frozenset({
                    "SIA405_Cable_de_controle_a_distance",
                }),
            ),
        }),
    ),
    "sia405_protection_tube": InterlisModel(
            models=frozenset({
            InterlisLangModel(
                lang="de",
                model="SIA405_Schutzrohr_2015_LV95",
                topics=frozenset({
                    "SIA405_Schutzrohr",
                }),
            ),
            InterlisLangModel(
                lang="fr",
                model="SIA405_TUBE_DE_PROTECTION_2015",
                topics=frozenset({
                    "SIA405_tube_de_protection",
                }),
            ),
        }),
    ),
    "ag96": InterlisModel(
            models=frozenset({
            InterlisLangModel(
                lang="de",
                model="Genereller_Entwaesserungsplan_AG",
                topics=frozenset({
                    "GEP_AGIS",
                }),
            ),
        }),
    ),
    "ag64":InterlisModel(
            models=frozenset({
            InterlisLangModel(
                lang="de",
                model="Abwasserkataster_AG_V2_LV95",
                topics=frozenset({
                    "Abwasserkataster_AG",
                }),
            ),
        }),
    ),
}

ALL_MODELS_BY_GROUP = {
    group: model.names
    for group, model in interlis_models.items()
}


ALL_SUPPORTED_MODELS = set().union(
    *ALL_MODELS_BY_GROUP.values()
    )

def groups_for_models(
    imported_models: str | Iterable[str],
) -> set:
    if isinstance(imported_models, str):
        imported_models = {imported_models}
    else:
        imported_models = set(imported_models)

    return {
        group
        for group, models in ALL_MODELS_BY_GROUP.items()
        if imported_models & models
    }


VSA_ORG_URL = "https://vsa.ch/models/organisation/vsa_organisationen_2020_1.xtf"
