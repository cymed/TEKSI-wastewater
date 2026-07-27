from dataclasses import dataclass, field
from collections.abc import Mapping
from typing import Any

from teksi_hooks.ili_definitions import Standardoid

from ..capabilities.conditions import (
    ConditionsCapability,
    ConditionEvaluationContext,
)
from ..capabilities.privilege import ResolvedProviderCapability
from ..capabilities.rights import RightsCapability,DerivedRightsCapability

from ..models.rulesets import (
    Rule,
    PrivilegeRule,
    OwnershipRule,
)
from ..models.validation import ChangeOperation


@dataclass(slots=True, frozen=True)
class RightsEvaluationContext:
    """
    Runtime context used for evaluating rights rules.

    The context contains all runtime values needed by rule evaluators:
    provider, data owner, operation type and old/new row values.
    """

    dataowner_oid: Standardoid
    provider_oid: Standardoid

    operation: ChangeOperation

    old_values: Mapping[str, Any] = field(
        default_factory=dict,
    )

    new_values: Mapping[str, Any] = field(
        default_factory=dict,
    )

    context_values: Mapping[str, Any] = field(
        default_factory=dict,
    )


class RightsEvaluator:
    """
    Evaluates resolved rights definitions against provider permissions
    and runtime change contexts.

    This class combines:
    - RightsCapability
    - ResolvedProviderCapability
    - ConditionsCapability

    It should contain authorization logic, while the capabilities remain
    lookup/evaluation helpers.
    """

    def __init__(
        self,
        rights: RightsCapability,
        provider: ResolvedProviderCapability,
        conditions: ConditionsCapability,
        derived_rights: DerivedRightsCapability,
    ):
        self.rights = rights
        self.provider = provider
        self.conditions = conditions
        self.derived_rights = derived_rights

    def can_update_attribute(
        self,
        dataowner_oid: Standardoid,
        class_id: str,
        attribute_name: str,
    ) -> bool:
        """
        Check whether the provider has the required attribute-level update
        privilege for a canonical class and attribute.
        Ownership and class-level CRUD rules are evaluated separately.
        """

        required_privileges = self.rights.update_privileges(
            class_id,
            attribute_name,
        )

        return any(
            self.provider.has_privilege(
                dataowner_oid,
                privilege,
            )
            for privilege in required_privileges
        )

    def can_create(
        self,
        class_id: str,
        context: RightsEvaluationContext,
    ) -> bool:
        """
        Check whether the provider may create an object of the class.
        """

        return self._can_apply_any_rule(
            self.rights.create_rules(class_id),
            context,
        )

    def can_update(
        self,
        class_id: str,
        context: RightsEvaluationContext,
    ) -> bool:
        """
        Check whether the provider may update an object of the class.
        """

        return self._can_apply_any_rule(
            self.rights.update_rules(class_id),
            context,
        )

    def can_delete(
        self,
        class_id: str,
        context: RightsEvaluationContext,
    ) -> bool:
        """
        Check whether the provider may delete an object of the class.
        """

        return self._can_apply_any_rule(
            self.rights.delete_rules(class_id),
            context,
        )

    def _can_apply_any_rule(
        self,
        rules: tuple[Rule, ...],
        context: RightsEvaluationContext,
    ) -> bool:
        """
        Return true if at least one rule grants access.
        """

        return any(
            self.can_apply_rule(
                rule,
                context,
            )
            for rule in rules
        )

    def can_apply_rule(
        self,
        rule: Rule,
        context: RightsEvaluationContext,
    ) -> bool:
        """
        Dispatch rule evaluation by concrete rule type.
        """

        if isinstance(rule, PrivilegeRule):
            return self.can_apply_privilege_rule(
                rule,
                context,
            )

        if isinstance(rule, OwnershipRule):
            return self.can_apply_ownership_rule(
                rule,
                context,
            )

        raise TypeError(
            f"Unsupported rule type: {type(rule)!r}"
        )

    def can_apply_privilege_rule(
        self,
        rule: PrivilegeRule,
        context: RightsEvaluationContext,
    ) -> bool:
        """
        Evaluate a privilege-based rule.

        If the rule has a condition, the condition must match before
        privileges are checked.
        """

        if rule.when is not None:
            if not self.conditions.evaluate(
                rule.when,
                self._condition_context(context),
            ):
                return False

        return any(
            self.provider.has_privilege(
                context.dataowner_oid,
                privilege,
            )
            for privilege in rule.privileges
        )

    def can_apply_ownership_rule(
        self,
        rule: OwnershipRule,
        context: RightsEvaluationContext,
    ) -> bool:
        """
        Evaluate an ownership rule.

        Ownership semantics:

        - INSERT: check ownership against submitted/new values.
        - UPDATE: check ownership against existing/old values.
        - DELETE: check ownership against existing/old values.

        This prevents a provider from passing ownership validation by
        changing the ownership attribute to themselves during an update.
        """

        if context.operation == ChangeOperation.INSERT:
            values = context.new_values
        else:
            values = context.old_values

        actual_owner = values.get(
            rule.attribute,
        )

        if actual_owner is None:
            return False

        return str(actual_owner) == str(context.provider_oid)

    def _condition_context(
        self,
        context: RightsEvaluationContext,
    ) -> ConditionEvaluationContext:
        """
        Convert a rights evaluation context into a condition evaluation
        context.
        """

        if context.operation == ChangeOperation.INSERT:
            local_values = context.new_values
        else:
            local_values = context.old_values

        return ConditionEvaluationContext(
            local_values=local_values,
            remote_values={},
            context_values={
                **context.context_values,
                "provider_oid": context.provider_oid,
                "dataowner_oid": context.dataowner_oid,
            },
        )