from __future__ import annotations

from dataclasses import dataclass

from ..models.rights import (
    AttributeDefinition,
    ClassDefinition,
    ResolvedAttributeDefinition,
)
from ..models.validation import (
    StateTransitionRule,
)


@dataclass(slots=True)
class ValidationResolver:
    """
    Resolves validation-related runtime structures.

    This resolver extracts and flattens transition definitions from
    attribute-level configuration into the class-level transition lookup
    exposed through `ResolvedClassDefinition`.

    The parsed model remains attribute-centric because that matches the YAML
    structure. The resolved model becomes validation-centric and allows
    efficient lookup of transitions by canonical attribute identifier.
    """

    def resolve_class(
        self,
        cls: ClassDefinition,
    ) -> tuple[
        dict[str, ResolvedAttributeDefinition],
        dict[str, frozenset[StateTransitionRule]],
    ]:
        attributes: dict[
            str,
            ResolvedAttributeDefinition,
        ] = {}

        transition_rules: dict[
            str,
            frozenset[StateTransitionRule],
        ] = {}

        for (
            attribute_id,
            attribute_definition,
        ) in cls.attributes.items():
            attributes[
                attribute_id
            ] = self.resolve_attribute(
                attribute_definition,
            )

            resolved_transitions = self.resolve_transition_rules(
                attribute_definition,
            )

            if resolved_transitions:
                transition_rules[
                    attribute_id
                ] = resolved_transitions

        return (
            attributes,
            transition_rules,
        )

    def resolve_attribute(
        self,
        attribute: AttributeDefinition,
    ) -> ResolvedAttributeDefinition:
        """
        Resolve an attribute definition.

        Validation and transition definitions are converted to immutable
        runtime structures.
        """

        return ResolvedAttributeDefinition(
            update_privileges=attribute.update_privileges,
            validations=tuple(
                attribute.validations,
            ),
            transitions=tuple(
                attribute.transitions,
            ),
        )

    def resolve_transition_rules(
        self,
        attribute: AttributeDefinition,
    ) -> frozenset:
        """
        Flatten transition validations into effective transition rules.
        """

        rules: set[
            StateTransitionRule
        ] = set()

        for transition_validation in attribute.transitions:
            rules.update(
                transition_validation.ruleset,
            )

        return frozenset(
            rules,
        )