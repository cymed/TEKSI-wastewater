from tww_hooks.models.privilege import Privilege
from tww_hooks.models.rulesets import (
    InheritRule,
    OwnershipRule,
    PrivilegeRule,
)
from tww_hooks.models.rulesets import ResolvedCrudRules


def test_rights_resolver_resolves_classes(
    resolved_rights,
) -> None:
    assert "wastewater_structure" in resolved_rights
    assert "wastewater_networkelement" in resolved_rights
    assert "wastewater_node" in resolved_rights
    assert "maintenance" in resolved_rights
    assert "pipe_profile" in resolved_rights


def test_rights_resolver_returns_resolved_crud_rules(
    resolved_rights,
) -> None:
    cls = resolved_rights["wastewater_structure"]

    assert isinstance(
        cls.crud_rules,
        ResolvedCrudRules,
    )

    assert isinstance(
        cls.crud_rules.create_rules,
        tuple,
    )
    assert isinstance(
        cls.crud_rules.update_rules,
        tuple,
    )
    assert isinstance(
        cls.crud_rules.delete_rules,
        tuple,
    )


def test_rights_resolver_expands_inherit_rules(
    resolved_rights,
) -> None:
    cls = resolved_rights["wastewater_structure"]

    assert len(cls.crud_rules.create_rules) == 2
    assert len(cls.crud_rules.update_rules) == 2
    assert len(cls.crud_rules.delete_rules) == 2

    assert all(
        not isinstance(rule, InheritRule)
        for rule in cls.crud_rules.update_rules
    )

    assert all(
        not isinstance(rule, InheritRule)
        for rule in cls.crud_rules.delete_rules
    )


def test_rights_resolver_preserves_privilege_rules(
    resolved_rights,
) -> None:
    cls = resolved_rights["wastewater_structure"]

    first_rule = cls.crud_rules.create_rules[0]

    assert isinstance(
        first_rule,
        PrivilegeRule,
    )

    assert first_rule.privileges == frozenset(
        {
            Privilege.DBW_GEP,
        }
    )


def test_rights_resolver_applies_default_create_rules(
    resolved_rights,
) -> None:
    cls = resolved_rights["maintenance_event"]

    assert len(cls.crud_rules.create_rules) == 1

    rule = cls.crud_rules.create_rules[0]

    assert isinstance(
        rule,
        OwnershipRule,
    )
    assert rule.attribute == "fk_provider"


def test_rights_resolver_expands_crud_rules_shortcut(
    resolved_rights,
) -> None:
    cls = resolved_rights["pipe_profile"]

    assert len(cls.crud_rules.create_rules) == 1
    assert len(cls.crud_rules.read_rules) == 1
    assert len(cls.crud_rules.update_rules) == 1
    assert len(cls.crud_rules.delete_rules) == 1

    create_rule = cls.crud_rules.create_rules[0]
    read_rule = cls.crud_rules.read_rules[0]
    update_rule = cls.crud_rules.update_rules[0]
    delete_rule = cls.crud_rules.delete_rules[0]

    assert isinstance(
        create_rule,
        PrivilegeRule,
    )

    assert create_rule.privileges == frozenset(
        {
            Privilege.DBW_WI,
            Privilege.DBW_GEP,
        }
    )

    assert read_rule == create_rule
    assert update_rule == create_rule
    assert delete_rule == create_rule


def test_rights_resolver_preserves_attribute_privileges(
    resolved_rights,
) -> None:
    cls = resolved_rights["wastewater_structure"]

    status = cls.attributes["status"]

    assert status.update_privileges == frozenset(
        {
            Privilege.DBW_GEP,
            Privilege.DBW_WI,
        }
    )


def test_rights_resolver_preserves_attribute_transitions(
    resolved_rights,
) -> None:
    cls = resolved_rights["wastewater_structure"]

    status = cls.attributes["status"]

    assert len(status.transitions) == 1

    transition_validation = status.transitions[0]

    assert transition_validation.allow_transitive is True
    assert len(transition_validation.ruleset) == 2


def test_rights_resolver_preserves_ownership_rules(
    resolved_rights,
) -> None:
    cls = resolved_rights["maintenance"]

    assert len(cls.crud_rules.update_rules) == 1
    assert len(cls.crud_rules.delete_rules) == 1

    update_rule = cls.crud_rules.update_rules[0]
    delete_rule = cls.crud_rules.delete_rules[0]

    assert isinstance(
        update_rule,
        OwnershipRule,
    )
    assert update_rule.attribute == "fk_provider"

    assert isinstance(
        delete_rule,
        OwnershipRule,
    )
    assert delete_rule.attribute == "fk_provider"