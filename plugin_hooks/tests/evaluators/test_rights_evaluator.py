from teksi_hooks.ili_definitions import Standardoid

from tww_hooks.capabilities.conditions import ConditionsCapability
from tww_hooks.capabilities.privilege import ResolvedProviderCapability
from tww_hooks.capabilities.rights import RightsCapability
from tww_hooks.evaluators.rights import RightsEvaluationContext,RightsEvaluator

from tww_hooks.models.privilege import Privilege
from tww_hooks.models.rulesets import PrivilegeRule
from tww_hooks.models.validation import ChangeOperation
from tww_hooks.models.rulesets import OwnershipRule


def test_rights_evaluator_allows_attribute_update_with_required_privilege(
    resolved_rights,
    resolved_providers,
) -> None:
    evaluator = RightsEvaluator(
        rights=RightsCapability(
            classes=resolved_rights,
        ),
        provider=ResolvedProviderCapability(
            provider=resolved_providers[
                Standardoid("ch000000geping01")
            ],
        ),
        conditions=ConditionsCapability(),
    )

    assert evaluator.can_update_attribute(
        dataowner_oid=Standardoid("ch000000awgde001"),
        class_id="wastewater_structure",
        attribute_name="status",
    )


def test_rights_evaluator_rejects_attribute_update_without_required_privilege(
    resolved_rights,
    resolved_providers,
) -> None:
    evaluator = RightsEvaluator(
        rights=RightsCapability(
            classes=resolved_rights,
        ),
        provider=ResolvedProviderCapability(
            provider=resolved_providers[
                Standardoid("ch000000awverbnd")
            ],
        ),
        conditions=ConditionsCapability(),
    )

    assert not evaluator.can_update_attribute(
        dataowner_oid=Standardoid("ch000000awverbnd"),
        class_id="wastewater_structure",
        attribute_name="gross_costs",
    )

def test_rights_evaluator_applies_privilege_rule(
    resolved_rights,
    resolved_providers,
) -> None:
    evaluator = RightsEvaluator(
        rights=RightsCapability(
            classes=resolved_rights,
        ),
        provider=ResolvedProviderCapability(
            provider=resolved_providers[
                Standardoid("ch000000geping01")
            ],
        ),
        conditions=ConditionsCapability(),
    )

    rule = PrivilegeRule(
        privileges=frozenset(
            {
                Privilege.DBW_GEP,
            }
        ),
    )

    context = RightsEvaluationContext(
        dataowner_oid=Standardoid("ch000000awgde001"),
        provider_oid=Standardoid("ch000000geping01"),
        operation=ChangeOperation.UPDATE,
    )

    assert evaluator.can_apply_privilege_rule(
        rule,
        context,
    )

def test_rights_evaluator_applies_ownership_rule_for_update_using_old_values(
    resolved_rights,
    resolved_providers,
) -> None:
    evaluator = RightsEvaluator(
        rights=RightsCapability(
            classes=resolved_rights,
        ),
        provider=ResolvedProviderCapability(
            provider=resolved_providers[
                Standardoid("ch000000geping01")
            ],
        ),
        conditions=ConditionsCapability(),
    )

    rule = OwnershipRule(
        attribute="fk_provider",
    )

    context = RightsEvaluationContext(
        dataowner_oid=Standardoid("ch000000awgde001"),
        provider_oid=Standardoid("ch000000geping01"),
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
) -> None:
    evaluator = RightsEvaluator(
        rights=RightsCapability(
            classes=resolved_rights,
        ),
        provider=ResolvedProviderCapability(
            provider=resolved_providers[
                Standardoid("ch000000geping01")
            ],
        ),
        conditions=ConditionsCapability(),
    )

    context = RightsEvaluationContext(
        dataowner_oid=Standardoid("ch000000awgde001"),
        provider_oid=Standardoid("ch000000geping01"),
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
) -> None:
    evaluator = RightsEvaluator(
        rights=RightsCapability(
            classes=resolved_rights,
        ),
        provider=ResolvedProviderCapability(
            provider=resolved_providers[
                Standardoid("ch000000geping01")
            ],
        ),
        conditions=ConditionsCapability(),
    )

    context = RightsEvaluationContext(
        dataowner_oid=Standardoid("ch000000awgde001"),
        provider_oid=Standardoid("ch000000geping01"),
        operation=ChangeOperation.UPDATE,
        old_values={
            "fk_provider": "ch000000geping01",
        },
    )

    assert evaluator.can_update(
        "maintenance",
        context,
    )

def test_rights_evaluator_inherits_rights_from_wastewater_structure(
    evaluator,
) -> None:
    context = RightsEvaluationContext(
        dataowner_oid=Standardoid(
            "ch000000awgde001"
        ),
        provider_oid=Standardoid(
            "ch000000geping01"
        ),
        operation=ChangeOperation.UPDATE,
        old_values={
            "fk_wastewater_structure":
                "ch000000ws000001",
        },
    )

    assert evaluator.can_update(
        "wastewater_networkelement",
        context,
    )

def test_rights_evaluator_inherits_rights_from_reach(
    evaluator,
) -> None:
    context = RightsEvaluationContext(
        dataowner_oid=Standardoid(
            "ch000000awgde001"
        ),
        provider_oid=Standardoid(
            "ch000000geping01"
        ),
        operation=ChangeOperation.UPDATE,
        old_values={
            "obj_id":
                "ch000000rp000001",
        },
    )

    assert evaluator.can_update(
        "reach_point",
        context,
    )

def test_rights_evaluator_accepts_any_matching_derived_right(
    evaluator,
) -> None:
    context = RightsEvaluationContext(
        dataowner_oid=Standardoid(
            "ch000000awgde001"
        ),
        provider_oid=Standardoid(
            "ch000000geping01"
        ),
        operation=ChangeOperation.UPDATE,
        old_values={
            "obj_id":
                "ch000000rp000001",
        },
    )

    assert evaluator.can_update(
        "reach_point",
        context,
    )

def test_rights_evaluator_accepts_any_matching_derived_right(
    evaluator,
) -> None:
    context = RightsEvaluationContext(
        dataowner_oid=Standardoid(
            "ch000000awgde001"
        ),
        provider_oid=Standardoid(
            "ch000000geping01"
        ),
        operation=ChangeOperation.UPDATE,
        old_values={
            "obj_id":
                "ch000000rp000001",
        },
    )

    assert evaluator.can_update(
        "reach_point",
        context,
    )