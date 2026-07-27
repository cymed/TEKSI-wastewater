from pathlib import Path
import pytest
from tww_hooks.parser.model_mapping_parser import ModelMappingParser


DATA_DIR = Path(__file__).parent / "data"


@pytest.fixture
def mapping():
    return ModelMappingParser().parse_file(
        DATA_DIR / "agxx_mapping_minimal.yaml",
    )

def test_agxx_mapping_parser_imports_classes(mapping) -> None:
    assert "GepKnoten" in mapping.classes
    assert "GepHaltung" in mapping.classes
    assert "Ueberlauf_Foerderaggregat" in mapping.classes
    assert "VersickerungsbereichAG" in mapping.classes

def test_agxx_mapping_parser_imports_gepknoten_function(mapping) -> None:
    cls = mapping.classes["GepKnoten"]

    assert cls.function is not None
    assert cls.function.schema == "tww_app"
    assert cls.function.name == "fct_agxx_gepknoten_mapping_jsonb"
    assert cls.function.parameters == {
        "row": "$row",
    }

    assert cls.attributes == {}

def test_agxx_mapping_parser_imports_gephaltung_function(mapping) -> None:
    cls = mapping.classes["GepHaltung"]

    assert cls.function is not None
    assert cls.function.schema == "tww_app"
    assert cls.function.name == "fct_agxx_gephaltung_mapping_jsonb"
    assert cls.function.parameters == {
        "row": "$row",
    }

    assert cls.attributes == {}


def test_agxx_mapping_parser_imports_ueberlauf_function(mapping) -> None:
    cls = mapping.classes["Ueberlauf_Foerderaggregat"]

    assert cls.function is not None
    assert cls.function.schema == "tww_app"
    assert cls.function.name == (
        "fct_agxx_ueberlauf_foerderaggregat_mapping_jsonb"
    )
    assert cls.function.parameters == {
        "row": "$row",
    }

    assert cls.attributes == {}


def test_agxx_mapping_parser_imports_attribute_backed_class(mapping) -> None:
    cls = mapping.classes["VersickerungsbereichAG"]

    assert cls.function is None
    assert "q_check" in cls.attributes
    assert "versickerungsmoeglichkeitag" in cls.attributes


def test_agxx_mapping_parser_imports_agxx_extension_attribute_mapping(
    mapping,
) -> None:
    attribute = mapping.classes[
        "VersickerungsbereichAG"
    ].attributes["q_check"]

    assert attribute.tww_class_id == "agxx_infiltration_zone"
    assert attribute.tww_attr_id == "ag96_q_check"
    assert attribute.foreign_key is None
    assert attribute.values == {}


def test_agxx_mapping_parser_imports_base_tww_attribute_mapping(
    mapping,
) -> None:
    attribute = mapping.classes[
        "VersickerungsbereichAG"
    ].attributes["versickerungsmoeglichkeitag"]

    assert attribute.tww_class_id == "infiltration_zone"
    assert attribute.tww_attr_id == "infiltration_capacity"
    assert attribute.foreign_key is None
    assert attribute.values == {}