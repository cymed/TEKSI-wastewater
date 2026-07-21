from __future__ import annotations

from dataclasses import dataclass
from fnmatch import fnmatchcase
from collections.abc import Mapping

from ..models.rights import (
    AttributeDefinition,
    ClassDefinition,
    RightsDefinition,
    ResolvedClassDefinition,
)
from ..models.rulesets import (
    CrudRules,
    InheritRule,
    Rule,
    ResolvedCrudRules,
)


@dataclass(slots=True)
class RightsResolver:
    """
    Resolves parsed rights definitions into runtime class definitions.

    The resolver applies defaults, expands inherited rule references and
    converts mutable parsed rule containers into immutable resolved rule
    containers.
    """

    def resolve(
        self,
        definition: RightsDefinition,
    ) -> Mapping[str, ResolvedClassDefinition]:
        return {
            class_id: self._resolve_class(
                class_definition=class_definition,
                definition=definition,
            )
            for class_id, class_definition in definition.classes.items()
        }

    def _resolve_class(
        self,
        class_definition: ClassDefinition,
        definition: RightsDefinition,
    ) -> ResolvedClassDefinition:
        crud_rules = self._resolve_crud_rules(
            class_definition=class_definition,
            defaults=definition.defaults.crud_rules,
        )

        attributes = self._resolve_attributes(
            class_definition=class_definition,
            definition=definition,
        )

        return ResolvedClassDefinition(
            id=class_definition.id,
            crud_rules=crud_rules,
            attributes=attributes,
        )

    def _resolve_crud_rules(
        self,
        class_definition: ClassDefinition,
        defaults: CrudRules,
    ) -> ResolvedCrudRules:
        create_rules = self._rules_or_default(
            class_definition.crud_rules.create_rules,
            defaults.create_rules,
        )

        read_rules = self._rules_or_default(
            class_definition.crud_rules.read_rules,
            defaults.read_rules,
        )

        update_rules = self._rules_or_default(
            class_definition.crud_rules.update_rules,
            defaults.update_rules,
        )

        delete_rules = self._rules_or_default(
            class_definition.crud_rules.delete_rules,
            defaults.delete_rules,
        )

        rule_sets = {
            "create_rules": create_rules,
            "read_rules": read_rules,
            "update_rules": update_rules,
            "delete_rules": delete_rules,
        }

        return ResolvedCrudRules(
            create_rules=self._expand_inherit_rules(
                create_rules,
                rule_sets,
            ),
            read_rules=self._expand_inherit_rules(
                read_rules,
                rule_sets,
            ),
            update_rules=self._expand_inherit_rules(
                update_rules,
                rule_sets,
            ),
            delete_rules=self._expand_inherit_rules(
                delete_rules,
                rule_sets,
            ),
        )

    def _rules_or_default(
        self,
        rules: list[Rule],
        default_rules: list[Rule],
    ) -> tuple[Rule, ...]:
        if rules:
            return tuple(rules)

        return tuple(default_rules)

    def _expand_inherit_rules(
        self,
        rules: tuple[Rule, ...],
        rule_sets: Mapping[str, tuple[Rule, ...]],
    ) -> tuple[Rule, ...]:
        expanded: list[Rule] = []

        for rule in rules:
            if isinstance(rule, InheritRule):
                try:
                    inherited_rules = rule_sets[rule.source]
                except KeyError as exc:
                    raise KeyError(
                        f"Unknown inherited rule set: {rule.source!r}"
                    ) from exc

                expanded.extend(
                    inherited_rule
                    for inherited_rule in inherited_rules
                    if not isinstance(inherited_rule, InheritRule)
                )
            else:
                expanded.append(rule)

        return tuple(expanded)

    def _resolve_attributes(
        self,
        class_definition: ClassDefinition,
        definition: RightsDefinition,
    ) -> Mapping[str, AttributeDefinition]:
        attributes = dict(
            class_definition.attributes,
        )

        for default in definition.defaults.attribute_defaults:
            for attribute_name, attribute_definition in attributes.items():
                if fnmatchcase(
                    attribute_name,
                    default.pattern,
                ):
                    if not attribute_definition.update_privileges:
                        attribute_definition.update_privileges = (
                            default.update_privileges
                        )

        return attributes