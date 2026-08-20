from __future__ import annotations

import json

import pytest

import teksi_wastewater.hooks.adapters.tww_quarantine_effect_projector as projector_module

from teksi_hooks.capabilities.mapping import (
    EffectiveModelMappingCapability,
    ModelMappingCapability,
)
from teksi_hooks.models.canonical_object import (
    CanonicalAttributeMetadata,
    CanonicalClassMetadata,
    CanonicalModelMetadata,
    CanonicalObjectIdentity,
)
from teksi_hooks.models.effects import (
    EnforceExistsEffect,
    EnforceNotExistsEffect,
    UpdateAttributeEffect,
)
from teksi_hooks.models.mapping import (
    AttributeMapping,
    ClassMapping,
    FunctionMapping,
    ModelMapping,
    RelationContext,
    ValueMapping,
)

from teksi_wastewater.hooks.adapters.tww_quarantine_effect_projector import (
    TwwQuarantineEffectProjector,
)
from teksi_wastewater.utils.database_utils import (
    DatabaseUtils,
)


class GepKnoten:
    pass


class GepHaltung:
    pass


class FunctionMappedClass:
    pass


class FakeRelationContextProvider:
    contexts: tuple[
        RelationContext,
        ...
    ] = ()

    init_args: list[
        dict,
    ] = []

    def __init__(
        self,
        *,
        ili_model,
        model_mapping,
        import_schema,
    ) -> None:
        self.__class__.init_args.append(
            {
                "ili_model": ili_model,
                "model_mapping": model_mapping,
                "import_schema": import_schema,
            }
        )

    def relation_contexts(
        self,
    ) -> tuple[
        RelationContext,
        ...
    ]:
        return self.__class__.contexts


def _canonical_metadata() -> CanonicalModelMetadata:
    return CanonicalModelMetadata(
        classes={
            "wastewater_structure": CanonicalClassMetadata(
                source_id=1,
                identifier="wastewater_structure",
            ),
            "wastewater_node": CanonicalClassMetadata(
                source_id=2,
                identifier="wastewater_node",
            ),
            "reach": CanonicalClassMetadata(
                source_id=3,
                identifier="reach",
            ),
        },
        attributes={
            (
                "wastewater_structure",
                "status",
            ): CanonicalAttributeMetadata(
                source_id=10,
                identifier="status",
            ),
            (
                "wastewater_structure",
                "function",
            ): CanonicalAttributeMetadata(
                source_id=11,
                identifier="function",
            ),
            (
                "wastewater_node",
                "function",
            ): CanonicalAttributeMetadata(
                source_id=20,
                identifier="function",
            ),
            (
                "reach",
                "status",
            ): CanonicalAttributeMetadata(
                source_id=30,
                identifier="status",
            ),
        },
        values={},
    )


def _mapping(
    *,
    classes,
    is_ssot: bool = True,
) -> EffectiveModelMappingCapability:
    return EffectiveModelMappingCapability(
        explicit_mapping=ModelMappingCapability(
            mapping=ModelMapping(
                classes=classes,
                is_ssot=is_ssot,
            ),
        ),
        implicit_mapping=None,
    )


def _patch_relation_context_provider(
    monkeypatch,
    contexts: tuple[
        RelationContext,
        ...
    ],
) -> None:
    FakeRelationContextProvider.contexts = contexts
    FakeRelationContextProvider.init_args = []

    monkeypatch.setattr(
        projector_module,
        "TwwRelationContextProvider",
        FakeRelationContextProvider,
    )


def test_projector_projects_simple_attribute_mapping(
    monkeypatch,
) -> None:
    class_mapping = ClassMapping(
        canonical_class_id="wastewater_structure",
        attributes={
            "statusag": AttributeMapping(
                canonical_class_id="wastewater_structure",
                canonical_attr_id="status",
            ),
        },
    )

    _patch_relation_context_provider(
        monkeypatch,
        contexts=(
            RelationContext(
                relation=GepKnoten,
                class_mapping=class_mapping,
            ),
        ),
    )

    monkeypatch.setattr(
        DatabaseUtils,
        "fetchall_dict",
        lambda query: [
            {
                "t_ili_tid": "ch000000ws000001",
                "statusag": "active",
            }
        ],
    )

    projector = TwwQuarantineEffectProjector(
        model_mapping=_mapping(
            classes={
                "GepKnoten": class_mapping,
            },
        ),
    )

    document = projector.effect_document_from_quarantine(
        schema="import_schema",
        source_model="AG64",
        canonical_metadata=_canonical_metadata(),
    )

    assert document.source.model == "AG64"
    assert document.source.class_id == "quarantine"
    assert document.source.object_id == "import_schema"

    assert len(
        document.effects,
    ) == 1

    effect = document.effects[0]

    assert isinstance(
        effect,
        UpdateAttributeEffect,
    )

    assert effect.identity == CanonicalObjectIdentity(
        class_id="wastewater_structure",
        attributes={
            "obj_id": "ch000000ws000001",
        },
    )

    assert effect.attribute_id == "status"
    assert effect.value == "active"

    assert FakeRelationContextProvider.init_args == [
        {
            "ili_model": "AG64",
            "model_mapping": projector.model_mapping,
            "import_schema": "import_schema",
        }
    ]


def test_projector_applies_value_mapping(
    monkeypatch,
) -> None:
    class_mapping = ClassMapping(
        canonical_class_id="wastewater_structure",
        attributes={
            "funktionag": AttributeMapping(
                canonical_class_id="wastewater_structure",
                canonical_attr_id="function",
                values={
                    "Schacht": ValueMapping(
                        canonical_value_id=1234,
                        value="manhole",
                    ),
                },
            ),
        },
    )

    _patch_relation_context_provider(
        monkeypatch,
        contexts=(
            RelationContext(
                relation=GepKnoten,
                class_mapping=class_mapping,
            ),
        ),
    )

    monkeypatch.setattr(
        DatabaseUtils,
        "fetchall_dict",
        lambda query: [
            {
                "t_ili_tid": "ch000000ws000002",
                "funktionag": "Schacht",
            }
        ],
    )

    projector = TwwQuarantineEffectProjector(
        model_mapping=_mapping(
            classes={
                "GepKnoten": class_mapping,
            },
        ),
    )

    document = projector.effect_document_from_quarantine(
        schema="import_schema",
        source_model="AG64",
        canonical_metadata=_canonical_metadata(),
    )

    effect = document.effects[0]

    assert isinstance(
        effect,
        UpdateAttributeEffect,
    )

    assert effect.attribute_id == "function"
    assert effect.value == 1234


def test_projector_skips_unmapped_canonical_class(
    monkeypatch,
) -> None:
    class_mapping = ClassMapping(
        canonical_class_id=None,
        attributes={},
    )

    _patch_relation_context_provider(
        monkeypatch,
        contexts=(
            RelationContext(
                relation=GepKnoten,
                class_mapping=class_mapping,
            ),
        ),
    )

    monkeypatch.setattr(
        DatabaseUtils,
        "fetchall_dict",
        lambda query: [
            {
                "t_ili_tid": "ch000000ws000003",
            }
        ],
    )

    projector = TwwQuarantineEffectProjector(
        model_mapping=_mapping(
            classes={
                "GepKnoten": class_mapping,
            },
        ),
    )

    document = projector.effect_document_from_quarantine(
        schema="import_schema",
        source_model="AG64",
        canonical_metadata=_canonical_metadata(),
    )

    assert document.effects == ()


def test_projector_rejects_unknown_canonical_class(
    monkeypatch,
) -> None:
    class_mapping = ClassMapping(
        canonical_class_id="unknown_class",
        attributes={},
    )

    _patch_relation_context_provider(
        monkeypatch,
        contexts=(
            RelationContext(
                relation=GepKnoten,
                class_mapping=class_mapping,
            ),
        ),
    )

    projector = TwwQuarantineEffectProjector(
        model_mapping=_mapping(
            classes={
                "GepKnoten": class_mapping,
            },
        ),
    )

    with pytest.raises(
        KeyError,
        match="Unknown canonical class",
    ):
        projector.effect_document_from_quarantine(
            schema="import_schema",
            source_model="AG64",
            canonical_metadata=_canonical_metadata(),
        )


def test_projector_rejects_unknown_canonical_attribute(
    monkeypatch,
) -> None:
    class_mapping = ClassMapping(
        canonical_class_id="wastewater_structure",
        attributes={
            "unknownag": AttributeMapping(
                canonical_class_id="wastewater_structure",
                canonical_attr_id="unknown_attribute",
            ),
        },
    )

    _patch_relation_context_provider(
        monkeypatch,
        contexts=(
            RelationContext(
                relation=GepKnoten,
                class_mapping=class_mapping,
            ),
        ),
    )

    monkeypatch.setattr(
        DatabaseUtils,
        "fetchall_dict",
        lambda query: [
            {
                "t_ili_tid": "ch000000ws000004",
                "unknownag": "value",
            }
        ],
    )

    projector = TwwQuarantineEffectProjector(
        model_mapping=_mapping(
            classes={
                "GepKnoten": class_mapping,
            },
        ),
    )

    with pytest.raises(
        KeyError,
        match="Unknown canonical attribute",
    ):
        projector.effect_document_from_quarantine(
            schema="import_schema",
            source_model="AG64",
            canonical_metadata=_canonical_metadata(),
        )


def test_projector_rejects_cross_class_simple_attribute_mapping(
    monkeypatch,
) -> None:
    class_mapping = ClassMapping(
        canonical_class_id="wastewater_structure",
        attributes={
            "funktionag": AttributeMapping(
                canonical_class_id="wastewater_node",
                canonical_attr_id="function",
            ),
        },
    )

    _patch_relation_context_provider(
        monkeypatch,
        contexts=(
            RelationContext(
                relation=GepKnoten,
                class_mapping=class_mapping,
            ),
        ),
    )

    monkeypatch.setattr(
        DatabaseUtils,
        "fetchall_dict",
        lambda query: [
            {
                "t_ili_tid": "ch000000ws000005",
                "funktionag": "value",
            }
        ],
    )

    projector = TwwQuarantineEffectProjector(
        model_mapping=_mapping(
            classes={
                "GepKnoten": class_mapping,
            },
        ),
    )

    with pytest.raises(
        NotImplementedError,
        match="different canonical class",
    ):
        projector.effect_document_from_quarantine(
            schema="import_schema",
            source_model="AG64",
            canonical_metadata=_canonical_metadata(),
        )


def test_projector_parses_function_mapping_payload(
    monkeypatch,
) -> None:
    class_mapping = ClassMapping(
        function=FunctionMapping(
            schema="tww_app",
            name="fct_agxx_mapping_jsonb",
            parameters={
                "row": "$row",
            },
        ),
    )

    _patch_relation_context_provider(
        monkeypatch,
        contexts=(
            RelationContext(
                relation=FunctionMappedClass,
                class_mapping=class_mapping,
            ),
        ),
    )

    monkeypatch.setattr(
        DatabaseUtils,
        "fetchall_dict",
        lambda query: [
            {
                "t_ili_tid": "source_1",
                "funktionag": "value",
            }
        ],
    )

    payload = {
        "version": 1,
        "effects": [
            {
                "kind": "update_attribute",
                "identity": {
                    "class_id": "wastewater_structure",
                    "attributes": {
                        "obj_id": "ch000000ws000006",
                    },
                },
                "attribute_id": "status",
                "value": "active",
            },
            {
                "kind": "enforce_exists",
                "identity": {
                    "class_id": "reach",
                    "attributes": {
                        "obj_id": "ch000000re000001",
                    },
                },
            },
            {
                "kind": "enforce_not_exists",
                "identity": {
                    "class_id": "reach",
                    "attributes": {
                        "obj_id": "ch000000re000002",
                    },
                },
            },
        ],
    }

    monkeypatch.setattr(
        DatabaseUtils,
        "fetchone",
        lambda query: (
            payload,
        ),
    )

    projector = TwwQuarantineEffectProjector(
        model_mapping=_mapping(
            classes={
                "FunctionMappedClass": class_mapping,
            },
        ),
    )

    document = projector.effect_document_from_quarantine(
        schema="import_schema",
        source_model="AG64",
        canonical_metadata=_canonical_metadata(),
    )

    assert len(
        document.effects,
    ) == 3

    assert isinstance(
        document.effects[0],
        UpdateAttributeEffect,
    )

    assert document.effects[0].attribute_id == "status"
    assert document.effects[0].value == "active"

    assert isinstance(
        document.effects[1],
        EnforceExistsEffect,
    )

    assert isinstance(
        document.effects[2],
        EnforceNotExistsEffect,
    )


def test_projector_parses_string_function_mapping_payload(
    monkeypatch,
) -> None:
    class_mapping = ClassMapping(
        function=FunctionMapping(
            schema="tww_app",
            name="fct_agxx_mapping_jsonb",
            parameters={
                "row": "$row",
            },
        ),
    )

    _patch_relation_context_provider(
        monkeypatch,
        contexts=(
            RelationContext(
                relation=FunctionMappedClass,
                class_mapping=class_mapping,
            ),
        ),
    )

    monkeypatch.setattr(
        DatabaseUtils,
        "fetchall_dict",
        lambda query: [
            {
                "t_ili_tid": "source_1",
            }
        ],
    )

    payload = {
        "version": 1,
        "effects": [
            {
                "kind": "update_attribute",
                "identity": {
                    "class_id": "wastewater_structure",
                    "attributes": {
                        "obj_id": "ch000000ws000007",
                    },
                },
                "tww_attribute_id": "status",
                "value": "planned",
            }
        ],
    }

    monkeypatch.setattr(
        DatabaseUtils,
        "fetchone",
        lambda query: (
            json.dumps(
                payload,
            ),
        ),
    )

    projector = TwwQuarantineEffectProjector(
        model_mapping=_mapping(
            classes={
                "FunctionMappedClass": class_mapping,
            },
        ),
    )

    document = projector.effect_document_from_quarantine(
        schema="import_schema",
        source_model="AG64",
        canonical_metadata=_canonical_metadata(),
    )

    effect = document.effects[0]

    assert isinstance(
        effect,
        UpdateAttributeEffect,
    )

    assert effect.attribute_id == "status"
    assert effect.value == "planned"


def test_projector_rejects_unsafe_function_parameter_name() -> None:
    projector = TwwQuarantineEffectProjector(
        model_mapping=_mapping(
            classes={},
        ),
    )

    function_mapping = FunctionMapping(
        schema="tww_app",
        name="fct_agxx_mapping_jsonb",
        parameters={
            "bad-name": "$row",
        },
    )

    with pytest.raises(
        ValueError,
        match="Unsafe SQL identifier",
    ):
        projector._call_function_mapping(
            function_mapping=function_mapping,
            row={
                "t_ili_tid": "source_1",
            },
        )


def test_projector_rejects_unsupported_function_effect_kind() -> None:
    projector = TwwQuarantineEffectProjector(
        model_mapping=_mapping(
            classes={},
        ),
    )

    with pytest.raises(
        ValueError,
        match="Unsupported effect kind",
    ):
        projector._effect_from_payload(
            {
                "kind": "unsupported",
                "identity": {
                    "class_id": "wastewater_structure",
                    "attributes": {
                        "obj_id": "ch000000ws000008",
                    },
                },
            }
        )
