from pathlib import Path
import pytest

from tww_hooks.parser.model_mapping_parser import ModelMappingParser


DATA_DIR = Path(__file__).parent / "data"

@pytest.fixture
def mapping():
    ModelMappingParser().parse_file(
        DATA_DIR / "agxx_mapping_minimal.yaml",
    )


def test_agxx_mapping_parser_imports_classes() -> None:
    assert "GepKnoten" in mapping.classes
    assert "GepHaltung" in mapping.classes
    assert "Ueberlauf_Foerderaggregat" in mapping.classes
    assert "VersickerungsbereichAG" in mapping.classes


def test_agxx_mapping_parser_imports_plain_attribute_mapping() -> None:

    attribute = mapping.classes[
        "GepKnoten"
    ].attributes["istschnittstelle"]

    assert attribute.tww_class_id == "agxx_wastewater_node"
    assert attribute.tww_attr_id == "ag96_is_gateway"
    assert attribute.foreign_key is None
    assert attribute.values == {}


def test_agxx_mapping_parser_imports_ag64_attribute_mapping() -> None:
    attribute = mapping.classes[
        "GepKnoten"
    ].attributes["funktionag"]

    assert attribute.tww_class_id == "agxx_wastewater_node"
    assert attribute.tww_attr_id == "ag64_function"
    assert attribute.foreign_key is None


def test_agxx_mapping_parser_imports_provider_mapping() -> None:

    attribute = mapping.classes[
        "GepKnoten"
    ].attributes["datenbewirtschafter_wi"]

    assert attribute.tww_class_id == "agxx_wastewater_networkelement"
    assert attribute.tww_attr_id == "ag64_fk_provider"


def test_agxx_mapping_parser_imports_foreign_key_mapping() -> None:

    attribute = mapping.classes[
        "GepKnoten"
    ].attributes["letzte_aenderung_wi"]

    assert attribute.tww_class_id == "agxx_last_modification"
    assert attribute.tww_attr_id == "ag64_last_modification"
    assert attribute.foreign_key is not None


def test_agxx_mapping_parser_imports_vl_extension_mapping() -> None:

    attribute = mapping.classes[
        "GepHaltung"
    ].attributes["nutzungsartag_ist"]

    assert attribute.tww_class_id == "channel"
    assert attribute.tww_attr_id == "usage_current"
    assert attribute.values == {}


def test_agxx_mapping_parser_imports_base_tww_target() -> None:
    attribute = mapping.classes[
        "VersickerungsbereichAG"
    ].attributes["versickerungsmoeglichkeitag"]

    assert attribute.tww_class_id == "infiltration_zone"
    assert attribute.tww_attr_id == "infiltration_capacity"
    assert attribute.vl_extension is True