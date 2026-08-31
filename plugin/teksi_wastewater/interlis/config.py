from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path


BASE = Path(
    __file__,
).parent

ILIVALIDATOR = (
    BASE
    / "bin"
    / "ilivalidator-1.15.0.jar"
)

TWW_DEFAULT_PGSERVICE = "pg_tww"

TWW_OD_SCHEMA = "tww_od"
TWW_VL_SCHEMA = "tww_vl"
TWW_SYS_SCHEMA = "tww_sys"
TWW_APP_SCHEMA = "tww_app"

EXPORT_SCHEMA = "tww_app_pg2xtf"
IMPORT_SCHEMA = "tww_app_xtf2pg"

DEFAULT_INTERLIS_LANGUAGE = "de"

VSA_ORG_URL = (
    "https://vsa.ch/models/organisation/"
    "vsa_organisationen_2020_1.xtf"
)


@dataclass(
    frozen=True,
    slots=True,
)
class InterlisLangModel:
    """
    One language-specific INTERLIS model definition.
    """

    lang: str
    model: str

    topics: frozenset[str] = frozenset()


@dataclass(
    frozen=True,
    slots=True,
)
class InterlisModel:
    """
    Language-specific variants of one semantic model group.
    """

    models: frozenset[
        InterlisLangModel
    ]

    @property
    def names(
        self,
    ) -> frozenset:
        """
        Return all language-specific model names.
        """

        return frozenset(
            model.model
            for model in self.models
        )

    @property
    def topics(
        self,
    ) -> frozenset:
        """
        Return all topics from all language variants.
        """

        return frozenset(
            topic
            for model in self.models
            for topic in model.topics
        )

    @property
    def languages(
        self,
    ) -> frozenset:
        """
        Return all configured language codes.
        """

        return frozenset(
            model.lang
            for model in self.models
        )

    def lang_name(
        self,
        lang: str,
        fallback_lang: str = DEFAULT_INTERLIS_LANGUAGE,
    ) -> str:
        """
        Return the model name for a language.

        If the requested language is unavailable, return the model configured
        for ``fallback_lang``.
        """

        requested_model = next(
            (
                model.model
                for model in self.models
                if model.lang == lang
            ),
            None,
        )

        if requested_model is not None:
            return requested_model

        fallback_model = next(
            (
                model.model
                for model in self.models
                if model.lang == fallback_lang
            ),
            None,
        )

        if fallback_model is not None:
            return fallback_model

        raise ValueError(
            "No INTERLIS model is configured for "
            f"language {lang!r} or fallback language "
            f"{fallback_lang!r}. Available languages: "
            f"{sorted(self.languages)}"
        )


interlis_models: dict[
    str,
    InterlisModel,
] = {
    "dss": InterlisModel(
        models=frozenset(
            {
                InterlisLangModel(
                    lang="de",
                    model="DSS_2020_1_LV95",
                    topics=frozenset(
                        {
                            "Siedlungsentwaesserung",
                        }
                    ),
                ),
                InterlisLangModel(
                    lang="fr",
                    model="SDEE_2020_1_LV95",
                    topics=frozenset(
                        {
                            (
                                "evacuation_des_eaux_"
                                "des_agglomerations"
                            ),
                        }
                    ),
                ),
            }
        ),
    ),
    "vsa_kek": InterlisModel(
        models=frozenset(
            {
                InterlisLangModel(
                    lang="de",
                    model="VSA_KEK_2020_1_LV95",
                    topics=frozenset(
                        {
                            "KEK",
                        }
                    ),
                ),
                InterlisLangModel(
                    lang="fr",
                    model="VSA_IVI_2020_1_LV95",
                    topics=frozenset(
                        {
                            "IVI",
                        }
                    ),
                ),
            }
        ),
    ),
    "sia405_abwasser": InterlisModel(
        models=frozenset(
            {
                InterlisLangModel(
                    lang="de",
                    model="SIA405_ABWASSER_2020_1_LV95",
                    topics=frozenset(
                        {
                            "SIA405_Abwasser",
                        }
                    ),
                ),
                InterlisLangModel(
                    lang="fr",
                    model="SIA405_EAUX_USEES_2020_1_LV95",
                    topics=frozenset(
                        {
                            "SIA405_Eaux_usees",
                        }
                    ),
                ),
            }
        ),
    ),
    "sia405_base_abwasser": InterlisModel(
        models=frozenset(
            {
                InterlisLangModel(
                    lang="de",
                    model="SIA405_Base_Abwasser_1_LV95",
                    topics=frozenset(
                        {
                            "Administration",
                        }
                    ),
                ),
                InterlisLangModel(
                    lang="fr",
                    model="SIA405_Base_Eaux_usees_1_LV95",
                    topics=frozenset(
                        {
                            "Administration",
                        }
                    ),
                ),
            }
        ),
    ),
    "sia405_cable": InterlisModel(
        models=frozenset(
            {
                InterlisLangModel(
                    lang="de",
                    model="SIA405_FERNWIRKKABEL_2015_LV95",
                    topics=frozenset(
                        {
                            "SIA405_Fernwirkkabel",
                        }
                    ),
                ),
                InterlisLangModel(
                    lang="fr",
                    model=(
                        "SIA405_CABLE_DE_CONTROLE_"
                        "A_DISTANCE_2015"
                    ),
                    topics=frozenset(
                        {
                            (
                                "SIA405_Cable_de_controle_"
                                "a_distance"
                            ),
                        }
                    ),
                ),
            }
        ),
    ),
    "sia405_protection_tube": InterlisModel(
        models=frozenset(
            {
                InterlisLangModel(
                    lang="de",
                    model="SIA405_Schutzrohr_2015_LV95",
                    topics=frozenset(
                        {
                            "SIA405_Schutzrohr",
                        }
                    ),
                ),
                InterlisLangModel(
                    lang="fr",
                    model="SIA405_TUBE_DE_PROTECTION_2015",
                    topics=frozenset(
                        {
                            "SIA405_tube_de_protection",
                        }
                    ),
                ),
            }
        ),
    ),
    "ag96": InterlisModel(
        models=frozenset(
            {
                InterlisLangModel(
                    lang="de",
                    model="Genereller_Entwaesserungsplan_AG",
                    topics=frozenset(
                        {
                            "GEP_AGIS",
                        }
                    ),
                ),
            }
        ),
    ),
    "ag64": InterlisModel(
        models=frozenset(
            {
                InterlisLangModel(
                    lang="de",
                    model="Abwasserkataster_AG_V2_LV95",
                    topics=frozenset(
                        {
                            "Abwasserkataster_AG",
                        }
                    ),
                ),
            }
        ),
    ),
}


INTERLIS_INHERITANCE_TREE: dict[
    str,
    tuple[str, ...],
] = {
    "dss": (
        "sia405_abwasser",
    ),
    "vsa_kek": (
        "sia405_abwasser",
    ),
    "sia405_abwasser": (
        "sia405_base_abwasser",
    ),
    "sia405_base_abwasser": (),
    "sia405_cable": (),
    "sia405_protection_tube": (),
    "ag96": (),
    "ag64": (),
}


ALL_MODELS_BY_GROUP: dict[
    str,
    frozenset[str],
] = {
    group: model.names
    for group, model in interlis_models.items()
}


ALL_SUPPORTED_MODELS: frozenset[str] = frozenset(
    model_name
    for model_names in ALL_MODELS_BY_GROUP.values()
    for model_name in model_names
)


def model_names_for_language(
    lang: str,
    fallback_lang: str = DEFAULT_INTERLIS_LANGUAGE,
    groups: Iterable[str] | None = None,
) -> dict[str, str]:
    """
    Return one language-specific model name per model group.

    If a group does not provide the requested language, its model in
    ``fallback_lang`` is returned.
    """

    selected_groups = (
        tuple(
            interlis_models,
        )
        if groups is None
        else tuple(
            groups,
        )
    )

    unknown_groups = (
        set(
            selected_groups,
        )
        - set(
            interlis_models,
        )
    )

    if unknown_groups:
        raise ValueError(
            "Unknown INTERLIS model groups: "
            f"{sorted(unknown_groups)}. "
            f"Available groups: "
            f"{sorted(interlis_models)}"
        )

    return {
        group: interlis_models[
            group
        ].lang_name(
            lang=lang,
            fallback_lang=fallback_lang,
        )
        for group in selected_groups
    }


def groups_for_models(
    imported_models: str | Iterable[str],
) -> set:
    """
    Return semantic model groups matching imported model names.
    """

    if isinstance(
        imported_models,
        str,
    ):
        imported_model_names = {
            imported_models,
        }
    else:
        imported_model_names = set(
            imported_models,
        )

    return {
        group
        for group, models
        in ALL_MODELS_BY_GROUP.items()
        if imported_model_names & models
    }


def resolve_interlis_model_groups(
    model_group: str,
) -> tuple[str, ...]:
    """
    Return inherited model groups in dependency-first order.

    The requested model group is included as the final item.
    """

    resolved: list[str] = []
    visited: set[str] = set()
    visiting: list[str] = []

    def visit(
        group: str,
    ) -> None:
        if group in visited:
            return

        if group in visiting:
            cycle_start = visiting.index(
                group,
            )

            cycle = (
                visiting[
                    cycle_start:
                ]
                + [
                    group,
                ]
            )

            raise ValueError(
                "Circular INTERLIS model inheritance: "
                + " -> ".join(
                    cycle,
                )
            )

        if group not in INTERLIS_INHERITANCE_TREE:
            raise KeyError(
                f"Unknown INTERLIS model group: "
                f"{group!r}."
            )

        visiting.append(
            group,
        )

        for inherited_group in (
            INTERLIS_INHERITANCE_TREE[
                group
            ]
        ):
            visit(
                inherited_group,
            )

        visiting.pop()

        visited.add(
            group,
        )

        resolved.append(
            group,
        )

    visit(
        model_group,
    )

    return tuple(
        resolved,
    )


def resolved_model_names(
    model_group: str,
    lang: str,
    fallback_lang: str = DEFAULT_INTERLIS_LANGUAGE,
) -> tuple[str, ...]:
    """
    Resolve one model group and its inheritance to concrete model names.

    Names are returned in dependency-first order.
    """

    resolved_groups = resolve_interlis_model_groups(
        model_group,
    )

    names_by_group = model_names_for_language(
        lang=lang,
        fallback_lang=fallback_lang,
        groups=resolved_groups,
    )

    return tuple(
        names_by_group[
            group
        ]
        for group in resolved_groups
    )