from unittest.mock import Mock

import pytest

from tww_hooks.models.mapping import (
    ClassMapping,
    ModelMapping,
)
from tww_hooks.capabilities.mapping import (
    ImplicitModelMappingCapability,
    ModelMappingCapability,
)

from teksi_wastewater.hooks.adapters.tww_relation_context_provider import (
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
    mapping = Mock(spec=ImplicitModelMappingCapability)

    mapping.class_mapping_for_ili.return_value = (
        "wastewater_node"
    )

    return mapping


@pytest.fixture
def empty_model_mapping():
    return ModelMappingCapability(
        ModelMapping(),
    )

@pytest.fixture
def effective_mapping():
    return EffectiveModelMappingCapability(
        explicit_mapping=empty_model_mapping,
        implicit_mapping=implicit_model_mapping,
    )


def test_relation_context_provider_uses_implicit_model_mapping_for_dss(
    monkeypatch,
    implicit_model_mapping,
    effective_mapping,
):
    monkeypatch.setattr(
        TwwRelationContextProvider,
        "_get_model",
        lambda self, schema: FakeModel(),
    )

    provider = TwwRelationContextProvider(
        ili_model="DSS_2020_1_LV95",
        model_mapping=effective_mapping,
    )

    contexts = provider.relation_contexts()

    assert len(contexts) == 1

    context = contexts[0]

    assert context.relation is FakeRelation

    assert context.class_mapping.tww_class_id == (
        "wastewater_node"
    )

    implicit_model_mapping.class_mapping_for_ili.assert_called_once_with(
        "FakeRelation",
    )


def test_relation_context_provider_prefers_explicit_agxx_mapping(
    monkeypatch,
    implicit_model_mapping,
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

    effective_model_mapping = EffectiveModelMappingCapability(
        explicit_mapping=model_mapping,
        implicit_mapping=implicit_model_mapping,
    )

    provider = TwwRelationContextProvider(
        ili_model="Abwasserkataster_AG_V2_LV95",
        model_mapping=effective_model_mapping,
    )

    contexts = provider.relation_contexts()

    assert len(contexts) == 1

    context = contexts[0]

    assert context.relation is FakeRelation

    assert context.class_mapping.tww_class_id == (
        "agxx_wastewater_node"
    )

    implicit_model_mapping.class_mapping_for_ili.assert_not_called()


def test_relation_context_provider_falls_back_to_dictionary_for_unmapped_agxx_class(
    monkeypatch,
    effective_mapping,
):
    monkeypatch.setattr(
        TwwRelationContextProvider,
        "_get_model",
        lambda self, schema: FakeModel(),
    )


    provider = TwwRelationContextProvider(
        ili_model="Abwasserkataster_AG_V2_LV95",
        model_mapping=effective_mapping,
    )

    contexts = provider.relation_contexts()

    assert len(contexts) == 1

    context = contexts[0]

    assert context.class_mapping.tww_class_id == (
        "wastewater_node"
    )

    implicit_model_mapping.class_mapping_for_ili.assert_called_once_with(
        "FakeRelation",
    )


def test_relation_context_provider_returns_immutable_tuple(
    monkeypatch,
    effective_mapping,
):
    monkeypatch.setattr(
        TwwRelationContextProvider,
        "_get_model",
        lambda self, schema: FakeModel(),
    )

    provider = TwwRelationContextProvider(
        ili_model="DSS_2020_1_LV95",
        model_mapping=effective_mapping,
    )

    contexts = provider.relation_contexts()

    assert isinstance(
        contexts,
        tuple,
    )


def test_relation_context_provider_raises_for_unknown_group(
    monkeypatch,
    effective_mapping,
):
    monkeypatch.setattr(
        "teksi_wastewater.hooks.adapters.tww_relation_context_provider.config.groups_for_models",
        lambda model: {"unknown"},
    )

    with pytest.raises(
        ValueError,
        match="No model defined for group",
    ):
        TwwRelationContextProvider(
            ili_model="UnknownModel",
            model_mapping=effective_mapping,
        )