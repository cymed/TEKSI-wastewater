from teksi_hooks.ili_definitions import Standardoid

from tww_hooks.capabilities.conditions import ConditionsCapability
from tww_hooks.capabilities.provider import ResolvedProviderCapability
from tww_hooks.capabilities.rights import RightsCapability
from tww_hooks.evaluators.rights import RightsEvaluator
from tww_hooks.models.privilege import Privilege


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