from pathlib import Path

from tww_hooks.parser.rights_parser import RightsParser,AgxxRightsParser

from tww_hooks.models.privilege import Privilege
from tww_hooks.models.rulesets import (
    InheritRule,
    OwnershipRule,
    PrivilegeRule,
)
from tww_hooks.models.conditions import LocalCondition
from tww_hooks.models.validation import ValidationSeverity


DATA_DIR = Path(__file__).parent / "data"


def test_rights_parser_imports_minimal_yaml() -> None:
    rights = RightsParser().parse_file(
        DATA_DIR / "rights_parser_minimal.yaml",
    )

    assert rights.allow_transitive_transitions is True

    assert "wastewater_structure" in rights.classes
    assert "wastewater_networkelement" in rights.classes
    assert "wastewater_node" in rights.classes
    assert "maintenance" in rights.classes
    assert "pipe_profile" in rights.classes

    assert "last_modification" in rights.validation_rules
    assert len(rights.validation_rules["last_modification"]) == 1

    last_modification_rule = rights.validation_rules[
        "last_modification"
    ][0]

    assert last_modification_rule.id == "newer_than_existing"
    assert last_modification_rule.level == ValidationSeverity.INFO


def test_rights_parser_imports_defaults() -> None:
    rights = RightsParser().parse_file(
        DATA_DIR / "rights_parser_minimal.yaml",
    )

    create_rules = rights.defaults.crud_rules.create_rules

    assert len(create_rules) == 1
    assert isinstance(create_rules[0], OwnershipRule)
    assert create_rules[0].attribute == "fk_provider"


def test_rights_parser_imports_privilege_rules_with_conditions() -> None:
    rights = RightsParser().parse_file(
        DATA_DIR / "rights_parser_minimal.yaml",
    )

    wastewater_structure = rights.classes[
        "wastewater_structure"
    ]

    create_rules = wastewater_structure.crud_rules.create_rules

    assert len(create_rules) == 2
    assert isinstance(create_rules[0], PrivilegeRule)

    first_rule = create_rules[0]

    assert first_rule.privileges == frozenset(
        {
            Privilege.DBW_GEP,
        }
    )

    assert isinstance(first_rule.when, LocalCondition)
    assert first_rule.when.attribute == "status"
    assert first_rule.when.operator == "in"
    assert first_rule.when.value == [
        "other.planned",
        "other.calculation_alternative",
    ]


def test_rights_parser_imports_inherit_rules() -> None:
    rights = RightsParser().parse_file(
        DATA_DIR / "rights_parser_minimal.yaml",
    )

    wastewater_structure = rights.classes[
        "wastewater_structure"
    ]

    update_rules = wastewater_structure.crud_rules.update_rules
    delete_rules = wastewater_structure.crud_rules.delete_rules

    assert len(update_rules) == 1
    assert isinstance(update_rules[0], InheritRule)
    assert update_rules[0].source == "create_rules"

    assert len(delete_rules) == 1
    assert isinstance(delete_rules[0], InheritRule)
    assert delete_rules[0].source == "create_rules"


def test_rights_parser_imports_attributes_and_transitions() -> None:
    rights = RightsParser().parse_file(
        DATA_DIR / "rights_parser_minimal.yaml",
    )

    wastewater_structure = rights.classes[
        "wastewater_structure"
    ]

    status = wastewater_structure.attributes["status"]

    assert status.update_privileges == frozenset(
        {
            Privilege.DBW_GEP,
            Privilege.DBW_WI,
        }
    )

    assert len(status.transitions) == 1

    transition_validation = status.transitions[0]

    assert transition_validation.allow_transitive is True
    assert len(transition_validation.ruleset) == 2

    bilateral_rules = [
        rule
        for rule in transition_validation.ruleset
        if rule.bilateral
    ]

    assert len(bilateral_rules) == 1

    bilateral_rule = bilateral_rules[0]

    assert bilateral_rule.from_value == "other.calculation_alternative"
    assert bilateral_rule.to_value == "other.planned"
    assert bilateral_rule.privileges == frozenset(
        {
            Privilege.DBW_GEP,
        }
    )


def test_rights_parser_imports_crud_rules_shortcut() -> None:
    rights = RightsParser().parse_file(
        DATA_DIR / "rights_parser_minimal.yaml",
    )

    pipe_profile = rights.classes["pipe_profile"]

    assert len(pipe_profile.crud_rules.create_rules) == 1
    assert len(pipe_profile.crud_rules.read_rules) == 1
    assert len(pipe_profile.crud_rules.update_rules) == 1
    assert len(pipe_profile.crud_rules.delete_rules) == 1

    create_rule = pipe_profile.crud_rules.create_rules[0]

    assert isinstance(create_rule, PrivilegeRule)
    assert create_rule.privileges == frozenset(
        {
            Privilege.DBW_WI,
            Privilege.DBW_GEP,
        }
    )


def test_rights_parser_imports_extends_and_derived_rights() -> None:
    rights = RightsParser().parse_file(
        DATA_DIR / "rights_parser_minimal.yaml",
    )

    wastewater_node = rights.classes["wastewater_node"]

    assert wastewater_node.superclass_id == "wastewater_networkelement"

    wastewater_networkelement = rights.classes[
        "wastewater_networkelement"
    ]

    assert len(wastewater_networkelement.derive_rights_from) == 1

    derived_right = wastewater_networkelement.derive_rights_from[0]

    assert derived_right.class_id == "wastewater_structure"
    assert derived_right.relation == "fk_wastewater_structure"

    reach_point = rights.classes["reach_point"]

    assert len(reach_point.derive_rights_from) == 2

    derived_targets = {
        (
            derived.class_id,
            derived.relation,
        )
        for derived in reach_point.derive_rights_from
    }

    assert derived_targets == {
        (
            "reach",
            "fk_reach_point_from",
        ),
        (
            "reach",
            "fk_reach_point_to",
        ),
    }


def test_rights_parser_imports_ownership_update_rules() -> None:
    rights = RightsParser().parse_file(
        DATA_DIR / "rights_parser_minimal.yaml",
    )

    maintenance = rights.classes["maintenance"]

    assert maintenance.superclass_id == "maintenance_event"

    update_rules = maintenance.crud_rules.update_rules

    assert len(update_rules) == 1
    assert isinstance(update_rules[0], OwnershipRule)
    assert update_rules[0].attribute == "fk_provider"

    delete_rules = maintenance.crud_rules.delete_rules

    assert len(delete_rules) == 1
    assert isinstance(delete_rules[0], InheritRule)
    assert delete_rules[0].source == "update_rules"


def test_agxx_rights_parser_imports_defaults_and_classes() -> None:
    rights = AgxxRightsParser().parse_file(
        DATA_DIR / "agxx_privileges_minimal.yaml",
    )

    assert "agxx_wastewater_node" in rights.classes
    assert "agxx_overflow" in rights.classes

    assert len(rights.defaults.attribute_defaults) == 2

    defaults_by_pattern = {
        default.pattern: default
        for default in rights.defaults.attribute_defaults
    }

    assert defaults_by_pattern[
        "ag64_*"
    ].update_privileges == frozenset(
        {
            Privilege.DBW_WI,
        }
    )

    assert defaults_by_pattern[
        "ag96_*"
    ].update_privileges == frozenset(
        {
            Privilege.DBW_GEP,
        }
    )
