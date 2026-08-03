from dataclasses import replace

from teksi_hooks.ili_definitions import Standardoid

from tww_hooks.capabilities.conditions import ConditionsCapability
from tww_hooks.capabilities.privilege import ResolvedProviderCapability
from tww_hooks.capabilities.rights import (
    DerivedRightsCapability,
    RightsCapability,
    SubclassRightsCapability,
)
from tww_hooks.evaluators.rights import (
    RightsEvaluationContext,
    RightsEvaluator,
)
from tww_hooks.models.privilege import Privilege
from tww_hooks.models.rulesets import (
    OwnershipRule,
    PrivilegeRule,
)
from tww_hooks.models.validation import ChangeOperation


def _make_evaluator(
    resolved_rights,
    resolved_providers,
    relation_lookup,
    provider_oid="ch000000geping01",
):
    return RightsEvaluator(
        rights=RightsCapability(
            rights=resolved_rights,
        ),
        provider=ResolvedProviderCapability(
            provider=resolved_providers[
                Standardoid(provider_oid)
            ],
        ),
        conditions=ConditionsCapability(),
        relation_lookup=relation_lookup,
        derived_rights=DerivedRightsCapability(
            rights=resolved_rights,
        ),
        subclass_rights=SubclassRightsCapability(
            rights=resolved_rights,
        ),
    )


def test_rights_evaluator_allows_attribute_update_with_required_privilege(
    resolved_rights,
    resolved_providers,
    relation_lookup,
) -> None:
    evaluator = _make_evaluator(
        resolved_rights,
        resolved_providers,
        relation_lookup,
    )

    assert evaluator.can_update_attribute(
        dataowner_oid=Standardoid(
            "ch000000awgde001",
        ),
        class_id="wastewater_structure",
        attribute_name="status",
    )


def test_rights_evaluator_rejects_attribute_update_without_required_privilege(
    resolved_rights,
    resolved_providers,
    relation_lookup,
) -> None:
    evaluator = _make_evaluator(
        resolved_rights,
        resolved_providers,
        relation_lookup,
        provider_oid="ch000000awverbnd",
    )

    assert not evaluator.can_update_attribute(
        dataowner_oid=Standardoid(
            "ch000000awgde001",
        ),
        class_id="wastewater_structure",
        attribute_name="gross_costs",
    )


def test_rights_evaluator_applies_privilege_rule(
    resolved_rights,
    resolved_providers,
    relation_lookup,
) -> None:
    evaluator = _make_evaluator(
        resolved_rights,
        resolved_providers,
        relation_lookup,
    )

    rule = PrivilegeRule(
        privileges=frozenset(
            {
                Privilege.DBW_GEP,
            }
        ),
    )

    context = RightsEvaluationContext(
        dataowner_oid=Standardoid(
            "ch000000awgde001",
        ),
        provider_oid=Standardoid(
            "ch000000geping01",
        ),
        operation=ChangeOperation.UPDATE,
    )

    assert evaluator.can_apply_privilege_rule(
        rule,
        context,
    )


def test_rights_evaluator_applies_ownership_rule_for_update_using_old_values(
    resolved_rights,
    resolved_providers,
    relation_lookup,
) -> None:
    evaluator = _make_evaluator(
        resolved_rights,
        resolved_providers,
        relation_lookup,
    )

    rule = OwnershipRule(
        attribute="fk_provider",
    )

    context = RightsEvaluationContext(
        dataowner_oid=Standardoid(
            "ch000000awgde001",
        ),
        provider_oid=Standardoid(
            "ch000000geping01",
        ),
        operation=ChangeOperation.UPDATE,
        old_values={
            "fk_provider": "ch000000geping01",
        },
        new_values={
            "fk_provider": "ch000000other01",
        },
    )

    assert evaluator.can_apply_ownership_rule(
        rule,
        context,
    )


def test_rights_evaluator_can_update_class_with_privilege_rule(
    resolved_rights,
    resolved_providers,
    relation_lookup,
) -> None:
    evaluator = _make_evaluator(
        resolved_rights,
        resolved_providers,
        relation_lookup,
    )

    context = RightsEvaluationContext(
        dataowner_oid=Standardoid(
            "ch000000awgde001",
        ),
        provider_oid=Standardoid(
            "ch000000geping01",
        ),
        operation=ChangeOperation.UPDATE,
        old_values={
            "status": "other.planned",
        },
    )

    assert evaluator.can_update(
        "wastewater_structure",
        context,
    )


def test_rights_evaluator_can_update_class_with_ownership_rule(
    resolved_rights,
    resolved_providers,
    relation_lookup,
) -> None:
    evaluator = _make_evaluator(
        resolved_rights,
        resolved_providers,
        relation_lookup,
    )

    context = RightsEvaluationContext(
        dataowner_oid=Standardoid(
            "ch000000awgde001",
        ),
        provider_oid=Standardoid(
            "ch000000geping01",
        ),
        operation=ChangeOperation.UPDATE,
        old_values={
            "fk_provider": "ch000000geping01",
        },
    )

    assert evaluator.can_update(
        "maintenance",
        context,
    )


def test_rights_evaluator_resolves_derived_rights(
    resolved_rights,
    resolved_providers,
    relation_lookup,
) -> None:
    evaluator = _make_evaluator(
        resolved_rights,
        resolved_providers,
        relation_lookup,
    )

    context = RightsEvaluationContext(
        dataowner_oid=Standardoid(
            "ch000000awgde001",
        ),
        provider_oid=Standardoid(
            "ch000000geping01",
        ),
        operation=ChangeOperation.UPDATE,
        old_values={
            "fk_wastewater_structure": "ch000000ws000001",
        },
    )

    derived = evaluator._resolve_derived_rights(
        "wastewater_networkelement",
        context,
    )

    assert len(
        derived.remote_objects,
    ) == 1

    assert (
        derived.remote_objects[0].class_id
        == "wastewater_structure"
    )


def test_rights_evaluator_inherits_rights_from_wastewater_structure(
    resolved_rights,
    resolved_providers,
    relation_lookup,
) -> None:
    evaluator = _make_evaluator(
        resolved_rights,
        resolved_providers,
        relation_lookup,
    )

    context = RightsEvaluationContext(
        dataowner_oid=Standardoid(
            "ch000000awgde001",
        ),
        provider_oid=Standardoid(
            "ch000000geping01",
        ),
        operation=ChangeOperation.UPDATE,
        old_values={
            "fk_wastewater_structure": "ch000000ws000001",
        },
    )

    assert evaluator.can_update(
        "wastewater_networkelement",
        context,
    )


def test_rights_evaluator_resolves_derived_rights_from_reach(
    resolved_rights,
    resolved_providers,
    relation_lookup,
) -> None:
    evaluator = _make_evaluator(
        resolved_rights,
        resolved_providers,
        relation_lookup,
    )

    context = RightsEvaluationContext(
        dataowner_oid=Standardoid(
            "ch000000awgde001",
        ),
        provider_oid=Standardoid(
            "ch000000geping01",
        ),
        operation=ChangeOperation.UPDATE,
        old_values={
            "obj_id": "ch000000rp000001",
        },
    )

    derived = evaluator._resolve_derived_rights(
        "reach_point",
        context,
    )

    assert len(
        derived.remote_objects,
    ) >= 1

    assert {
        obj.class_id
        for obj in derived.remote_objects
    } == {
        "reach",
    }

def test_resolved_rights_inherit_derived_rights_to_reach(
    resolved_rights,
) -> None:
    assert "reach" in resolved_rights.derived_rights

    assert any(
        relation.class_id == "wastewater_structure"
        for relation in resolved_rights.derived_rights["reach"]
    )

def test_rights_evaluator_inherits_rights_from_reach(
    resolved_rights,
    resolved_providers,
    relation_lookup,
) -> None:
    evaluator = _make_evaluator(
        resolved_rights,
        resolved_providers,
        relation_lookup,
    )



    context = RightsEvaluationContext(
        dataowner_oid=Standardoid(
            "ch000000awgde001",
        ),
        provider_oid=Standardoid(
            "ch000000geping01",
        ),
        operation=ChangeOperation.UPDATE,
        old_values={
            "obj_id": "ch000000rp000001",
        },
    )
    derived_from_reach_point = evaluator._resolve_derived_rights(
        "reach_point",
        context,
    )

    assert derived_from_reach_point.remote_objects

    assert {
        obj.class_id
        for obj in derived_from_reach_point.remote_objects
    } == {
        "reach",
    }

    reach_identity = derived_from_reach_point.remote_objects[0]

    reach = evaluator.relation_lookup.current_object(
        reach_identity,
    )

    assert reach is not None

    assert (
        reach.values["fk_wastewater_structure"]
        == "ch000000ws000001"
    )

    reach_context = RightsEvaluationContext(
        dataowner_oid=context.dataowner_oid,
        provider_oid=context.provider_oid,
        operation=context.operation,
        old_values={
            **reach.identity.attributes,
            **reach.values,
        },
        new_values={},
        context_values=context.context_values,
    )

    derived_from_reach = evaluator._resolve_derived_rights(
        "reach",
        reach_context,
    )

    assert derived_from_reach.remote_objects

    assert {
        obj.class_id
        for obj in derived_from_reach.remote_objects
    } == {
        "wastewater_structure",
    }
        
    assert evaluator.can_update(
        "reach_point",
        context,
    )

def test_rights_evaluator_inherits_update_rights_from_subclass(
    resolved_rights,
    resolved_providers,
    relation_lookup,
) -> None:
    resolved_with_subclass_rights = replace(
        resolved_rights,
        subclass_rights={
            "maintenance_event": (
                "maintenance",
            ),
        },
    )

    evaluator = _make_evaluator(
        resolved_with_subclass_rights,
        resolved_providers,
        relation_lookup,
    )

    context = RightsEvaluationContext(
        dataowner_oid=Standardoid(
            "ch000000awgde001",
        ),
        provider_oid=Standardoid(
            "ch000000geping01",
        ),
        operation=ChangeOperation.UPDATE,
        old_values={
            "fk_provider": "ch000000geping01",
        },
    )

    assert evaluator.can_update(
        "maintenance_event",
        context,
    )


def test_rights_evaluator_returns_false_without_subclass_mapping(
    resolved_rights,
    resolved_providers,
    relation_lookup,
) -> None:
    evaluator = _make_evaluator(
        resolved_rights,
        resolved_providers,
        relation_lookup,
    )

    context = RightsEvaluationContext(
        dataowner_oid=Standardoid(
            "ch000000awgde001",
        ),
        provider_oid=Standardoid(
            "ch000000geping01",
        ),
        operation=ChangeOperation.UPDATE,
        old_values={
            "fk_provider": "ch000000geping01",
        },
    )

    assert not evaluator._can_update_via_subclass_rights(
        "maintenance_event",
        context,
    )