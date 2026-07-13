
from __future__ import annotations

from dataclasses import dataclass, field

from .privilege import Privilege
from .validation import ValidationSeverity


@dataclass(slots=True)
class ClassDefinition:
    id: str
    superclass_id: str | None = None
    rights_from_subclass: bool = False

    create_rules: list[Rule] = field(
        default_factory=list,
    )

    delete_rules: list[Rule] = field(
        default_factory=list,
    )
    default_update_privileges: frozenset[Privilege] = field(
        default_factory=frozenset,
    )
    attributes: dict[str, AttributeDefinition] = field(
        default_factory=dict,
    )


@dataclass(slots=True, frozen=True)
class Rule:
    privileges: frozenset[Privilege]

    when: Condition | None = None


@dataclass(slots=True)
class AttributeDefinition:
    update_privileges: frozenset[Privilege] = field(
        default_factory=frozenset,
    )

    rules: list[AttributeRule] = field(
        default_factory=list,
    )

    transitions: list[TransitionRule] = field(
        default_factory=list,
    )


@dataclass(slots=True)
class ResolvedClassDefinition:
    id: str

    superclass: ResolvedClassDefinition | None = None

    create_rules: list[Rule] = field(
        default_factory=list,
    )

    delete_rules: list[Rule] = field(
        default_factory=list,
    )

    default_update_privileges: frozenset[Privilege] = field(
        default_factory=frozenset,
    )

    attributes: dict[str, AttributeDefinition] = field(
        default_factory=dict,
    )



@dataclass(slots=True, frozen=True)
class AttributeRule:
    id: str
    level: ValidationSeverity
