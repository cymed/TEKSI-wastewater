from tww_hooks.capabilities.mapping import ModelMappingCapability


def test_model_mapping_capability_returns_function_backed_class(
    agxx_mapping,
) -> None:
    capability = ModelMappingCapability(
        mapping=agxx_mapping,
    )

    cls = capability.class_definition(
        "GepKnoten",
    )

    assert cls.function is not None
    assert cls.function.name == "fct_agxx_gepknoten_mapping_jsonb"


def test_model_mapping_capability_returns_attribute_backed_class(
    agxx_mapping,
) -> None:
    capability = ModelMappingCapability(
        mapping=agxx_mapping,
    )

    cls = capability.class_definition(
        "VersickerungsbereichAG",
    )

    assert cls.function is None
    assert "q_check" in cls.attributes


def test_model_mapping_capability_returns_attribute_definition(
    agxx_mapping,
) -> None:
    capability = ModelMappingCapability(
        mapping=agxx_mapping,
    )

    attribute = capability.attribute_definition(
        "VersickerungsbereichAG",
        "q_check",
    )

    assert attribute.tww_class_id == "agxx_infiltration_zone"
    assert attribute.tww_attr_id == "ag96_q_check"


def test_model_mapping_capability_try_class_definition_returns_none(
    agxx_mapping,
) -> None:
    capability = ModelMappingCapability(
        mapping=agxx_mapping,
    )

    assert capability.try_class_definition(
        "DoesNotExist",
    ) is None


def test_model_mapping_capability_try_attribute_definition_returns_none(
    agxx_mapping,
) -> None:
    capability = ModelMappingCapability(
        mapping=agxx_mapping,
    )

    assert capability.try_attribute_definition(
        "VersickerungsbereichAG",
        "does_not_exist",
    ) is None