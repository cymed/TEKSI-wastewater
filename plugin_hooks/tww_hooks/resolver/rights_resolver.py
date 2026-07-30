from __future__ import annotations

from dataclasses import dataclass, field
from fnmatch import fnmatchcase
from collections.abc import Mapping
from ..models.rights import (
    AttributeDefinition,
    ClassDefinition,
    ResolvedAttributeDefinition,
    RightsDefinition,
    ResolvedClassDefinition,
    DerivedRights,
    ResolvedRights,
)

from ..models.rulesets import (
    CrudRules,
    InheritRule,
    Rule,
    ResolvedCrudRules,
)
from .validation_resolver import ValidationResolver


@dataclass(slots=True)
class RightsResolver:
    """
    Resolves parsed rights definitions into runtime definitions.

    Responsibilities:

    - apply default CRUD rules;
    - expand inherited CRUD rules;
    - apply wildcard attribute defaults;
    - produce immutable resolved models;
    - build class-level transition definitions.
    """

    validation_resolver: ValidationResolver = field(
        default_factory=ValidationResolver,
        )              

    def resolve(
        self,
        definition: RightsDefinition,
    ) -> ResolvedRights:
        return ResolvedRights(
            classes={
                class_id: self._resolve_class(
                    class_definition=class_definition,
                    definition=definition,
                )
                for (
                    class_id,
                    class_definition,
                ) in definition.classes.items()
            },
            derived_rights=self.resolve_derived_rights_config(
                definition,
            ),
            subclass_rights=self.resolve_subclass_rights(
                definition,
            ),
            allow_transitive_transitions=
                definition.allow_transitive_transitions,
        )

    def _resolve_class(
        self,
        class_definition: ClassDefinition,
        definition: RightsDefinition,
    ) -> ResolvedClassDefinition:
        attributes = self._resolve_attributes(
            class_definition=class_definition,
            definition=definition,
        )

        return ResolvedClassDefinition(
            id=class_definition.id,
            crud_rules=self._resolve_crud_rules(
                class_definition=class_definition,
                defaults=definition.defaults.crud_rules,
            ),
            attributes=attributes,
            transition_rules=(
                self.validation_resolver
                .resolve_class_transition_rules(
                    attributes,
                )
            ),
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
                    inherited_rules = rule_sets[
                        rule.source
                    ]
                except KeyError as exc:
                    raise KeyError(
                        f"Unknown inherited rule set: "
                        f"{rule.source!r}"
                    ) from exc

                expanded.extend(
                    inherited_rule
                    for inherited_rule in inherited_rules
                    if not isinstance(
                        inherited_rule,
                        InheritRule,
                    )
                )
            else:
                expanded.append(
                    rule,
                )

        return tuple(
            expanded,
        )

    def _resolve_attributes(
        self,
        class_definition: ClassDefinition,
        definition: RightsDefinition,
    ) -> Mapping[
        str,
        ResolvedAttributeDefinition,
    ]:
        resolved: dict[
            str,
            ResolvedAttributeDefinition,
        ] = {}

        for (
            attribute_name,
            attribute_definition,
        ) in class_definition.attributes.items():
            resolved[
                attribute_name
            ] = self._resolve_attribute(
                attribute_name=attribute_name,
                attribute_definition=attribute_definition,
                definition=definition,
            )

        return resolved

    def _resolve_attribute(
        self,
        attribute_name: str,
        attribute_definition: AttributeDefinition,
        definition: RightsDefinition,
    ) -> ResolvedAttributeDefinition:
        update_privileges = (
            attribute_definition.update_privileges
        )

        if not update_privileges:
            for default in (
                definition.defaults.attribute_defaults
            ):
                if fnmatchcase(
                    attribute_name,
                    default.pattern,
                ):
                    update_privileges = (
                        default.update_privileges
                    )
                    break

        return ResolvedAttributeDefinition(
            update_privileges=update_privileges,
            validations=tuple(
                attribute_definition.validations,
            ),
            transitions=tuple(
                attribute_definition.transitions,
            ),
        )

    def resolve_subclass_rights(
        self,
        definition: RightsDefinition,
    ) -> Mapping[
        str,
        tuple[str, ...],
    ]:
        """
        Resolve subclass-based rights inheritance.

        Returns a mapping of parent class identifiers to child classes whose
        rights should be considered during authorization evaluation.
        """

        subclasses: dict[
            str,
            list[str],
        ] = {}

        for child in definition.classes.values():
            if not child.superclass_id:
                continue

            if not child.rights_from_subclass:
                continue

            subclasses.setdefault(
                child.superclass_id,
                [],
            ).append(
                child.id,
            )

        return {
            parent_class: tuple(
                child_classes,
            )
            for (
                parent_class,
                child_classes,
            ) in subclasses.items()
        }

    def resolve_derived_rights_config(
        self,
        definition: RightsDefinition,
    ) -> Mapping[
        str,
        tuple[DerivedRights, ...],
    ]:
        resolved: dict[
            str,
            tuple[DerivedRights, ...],
        ] = {}

        for class_id, class_definition in definition.classes.items():
            derived_rights = self._derived_rights_for_class(
                class_definition=class_definition,
                definition=definition,
                visited=(),
            )

            if derived_rights:
                resolved[class_id] = derived_rights

        return resolved


    def _derived_rights_for_class(
        self,
        class_definition: ClassDefinition,
        definition: RightsDefinition,
        visited: tuple[str, ...],
    ) -> tuple[
        DerivedRights,
        ...
    ]:
        if class_definition.id in visited:
            return ()

        next_visited = visited + (
            class_definition.id,
        )

        inherited: list[
            DerivedRights
        ] = []

        if class_definition.superclass_id:
            superclass = definition.classes.get(
                class_definition.superclass_id,
            )

            if superclass is not None:
                inherited.extend(
                    self._derived_rights_for_class(
                        class_definition=superclass,
                        definition=definition,
                        visited=next_visited,
                    )
                )

        inherited.extend(
            class_definition.derive_rights_from,
        )

        return tuple(
            inherited,
        )