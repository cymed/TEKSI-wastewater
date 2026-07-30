from unittest.mock import Mock

import pytest

from tww_hooks.models.mapping import (
    ClassMapping,
    ModelMapping,
)
from tww_hooks.capabilities.mapping import (
    DictionaryMappingCapability,
    ModelMappingCapability,
)

from teksi_wastewater.hooks_adapters.tww_relation_context_provider import (
    TwwRelationContextProvider,
)


class FakeRelation:
    pass


class FakeModel:
    def classes(self):
        return {
            "FakeRelation": FakeRelation,
        }


@pytest.fixture
def dictionary_mapping():
    mapping = Mock(spec=DictionaryMappingCapability)

    mapping.class_mapping_for_ili.return_value = (
        "wastewater_node"
    )

    return mapping


@pytest.fixture
def empty_model_mapping():
    return ModelMappingCapability(
        ModelMapping(),
    )


def test_relation_context_provider_uses_dictionary_mapping_for_dss(
    monkeypatch,
    dictionary_mapping,
    empty_model_mapping,
):
    monkeypatch.setattr(
        TwwRelationContextProvider,
        "_get_model",
        lambda self, schema: FakeModel(),
    )

    provider = TwwRelationContextProvider(
        ili_model="DSS_2020_1_LV95",
        dictionary_mapping=dictionary_mapping,
        model_mapping=empty_model_mapping,
    )

    contexts = provider.relation_contexts()

    assert len(contexts) == 1

    context = contexts[0]

    assert context.relation is FakeRelation

    assert context.class_mapping.tww_class_id == (
        "wastewater_node"
    )

    dictionary_mapping.class_mapping_for_ili.assert_called_once_with(
        "FakeRelation",
    )


def test_relation_context_provider_prefers_explicit_agxx_mapping(
    monkeypatch,
    dictionary_mapping,
):
    monkeypatch.setattr(
        TwwRelationContextProvider,
        "_get_model",
        lambda self, schema: FakeModel(),
    )

    model_mapping = ModelMappingCapability(
        ModelMapping(
            classes={
                "FakeRelation": ClassMapping(
                    tww_class_id="agxx_wastewater_node",
                ),
            },
        ),
    )

    provider = TwwRelationContextProvider(
        ili_model="Abwasserkataster_AG_V2_LV95",
        dictionary_mapping=dictionary_mapping,
        model_mapping=model_mapping,
    )

    contexts = provider.relation_contexts()

    assert len(contexts) == 1

    context = contexts[0]

    assert context.relation is FakeRelation

    assert context.class_mapping.tww_class_id == (
        "agxx_wastewater_node"
    )

    dictionary_mapping.class_mapping_for_ili.assert_not_called()


def test_relation_context_provider_falls_back_to_dictionary_for_unmapped_agxx_class(
    monkeypatch,
    dictionary_mapping,
):
    monkeypatch.setattr(
        TwwRelationContextProvider,
        "_get_model",
        lambda self, schema: FakeModel(),
    )

    model_mapping = ModelMappingCapability(
        ModelMapping(),
    )

    provider = TwwRelationContextProvider(
        ili_model="Abwasserkataster_AG_V2_LV95",
        dictionary_mapping=dictionary_mapping,
        model_mapping=model_mapping,
    )

    contexts = provider.relation_contexts()

    assert len(contexts) == 1

    context = contexts[0]

    assert context.class_mapping.tww_class_id == (
        "wastewater_node"
    )

    dictionary_mapping.class_mapping_for_ili.assert_called_once_with(
        "FakeRelation",
    )


def test_relation_context_provider_returns_immutable_tuple(
    monkeypatch,
    dictionary_mapping,
    empty_model_mapping,
):
    monkeypatch.setattr(
        TwwRelationContextProvider,
        "_get_model",
        lambda self, schema: FakeModel(),
    )

    provider = TwwRelationContextProvider(
        ili_model="DSS_2020_1_LV95",
        dictionary_mapping=dictionary_mapping,
        model_mapping=empty_model_mapping,
    )

    contexts = provider.relation_contexts()

    assert isinstance(
        contexts,
        tuple,
    )


def test_relation_context_provider_raises_for_unknown_group(
    monkeypatch,
    dictionary_mapping,
    empty_model_mapping,
):
    monkeypatch.setattr(
        "teksi_wastewater.hooks_adapters.tww_relation_context_provider.config.groups_for_models",
        lambda model: {"unknown"},
    )

    with pytest.raises(
        ValueError,
        match="No model defined for group",
    ):
        TwwRelationContextProvider(
            ili_model="UnknownModel",
            dictionary_mapping=dictionary_mapping,
            model_mapping=empty_model_mapping,
        )