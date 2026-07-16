from __future__ import annotations

from dataclasses import dataclass, field
from collections.abc import Mapping

from .privilege import Privilege
from .validation import AttributeValidation, TransitionValidation
from .rulesets import CrudRules, ResolvedCrudRules


@dataclass(slots=True)
class DefaultDefinitions:
    """
    Global default rights definitions.

    Defaults are applied by the resolver when a class does not define its own
    corresponding rule set. Class-level definitions override these defaults.
    """

    crud_rules: CrudRules = field(
        metadata={
            "doc": (
                "Default CRUD rules applied to classes that do not explicitly "
                "define their own rules."
            )
        },
    )


@dataclass(slots=True)
class ClassDefinition:
    """
    Parsed class-level rights definition.

    This model represents the rights configuration as loaded from the source
    definition before inheritance, defaults, derived rights, and rule shortcuts
    are resolved.

    `ClassDefinition` is part of the source model. Runtime validation should
    consume `ResolvedClassDefinition` instead.
    """

    id: str = field(
        metadata={
            "doc": (
                "Canonical class identifier. Usually corresponds to a TWW "
                "semantic class or table identifier."
            )
        },
    )

    superclass_id: str | None = field(
        default=None,
        metadata={
            "doc": (
                "Optional canonical class identifier of the superclass from "
                "which this class inherits rights and attributes."
            )
        },
    )

    rights_from_subclass: bool = field(
        default=False,
        metadata={
            "doc": (
                "Whether rights should be evaluated from subclass definitions. "
                "This is mainly used for abstract or inheritance-root classes "
                "whose concrete rights are defined on subclasses."
            )
        },
    )

    derive_rights_from: tuple[DerivedRights, ...] = field(
        default_factory=tuple,
        metadata={
            "doc": (
                "Optional relations from which rights can be derived. "
                "Derived rights are resolved against related objects and "
                "combined with local rights according to resolver semantics."
            )
        },
    )

    crud_rules: CrudRules = field(
        default_factory=CrudRules,
        metadata={
            "doc": (
                "Parsed CRUD rules for this class. These may include direct "
                "rules, ownership rules and inheritance references."
            )
        },
    )

    attributes: dict[str, AttributeDefinition] = field(
        default_factory=dict,
        metadata={
            "doc": (
                "Attribute definitions keyed by canonical attribute identifier."
            )
        },
    )


@dataclass(slots=True, frozen=True)
class ResolvedClassDefinition:
    """
    Resolved and immutable class-level rights definition.

    This model is produced by the rights resolver. It should contain the
    effective rule set after defaults, inheritance, CRUD shortcuts and rule
    inheritance have been applied.

    Runtime hooks and validators should use this model instead of
    `ClassDefinition`.
    """

    id: str = field(
        metadata={
            "doc": (
                "Canonical class identifier of the resolved class."
            )
        },
    )

    crud_rules: ResolvedCrudRules = field(
        metadata={
            "doc": (
                "Fully resolved immutable CRUD rules for this class."
            )
        },
    )

    attributes: Mapping[str, AttributeDefinition] = field(
        metadata={
            "doc": (
                "Resolved attribute definitions keyed by canonical attribute "
                "identifier."
            )
        },
    )

    # add when needed for debugging
    # resolution_info: ResolutionInfo | None = None


@dataclass(slots=True, frozen=True)
class DerivedRights:
    """
    Parsed derived-rights declaration.

    A derived-rights declaration describes that rights for one class may be
    derived from a related class through a relation. This model belongs to the
    parsed configuration and is resolved later by the rights resolver.
    """

    cls: ClassDefinition = field(
        metadata={
            "doc": (
                "Class definition from which rights may be derived."
            )
        },
    )

    relation: str = field(
        metadata={
            "doc": (
                "Relation name used to reach the related object whose rights "
                "may be reused."
            )
        },
    )


@dataclass(slots=True, frozen=True)
class ResolvedDerivedRights:
    """
    Resolved derived-rights declaration.

    This is the runtime counterpart of `DerivedRights`, where the referenced
    class has already been resolved.
    """

    cls: ResolvedClassDefinition = field(
        metadata={
            "doc": (
                "Resolved class definition from which rights may be derived."
            )
        },
    )

    relation: str = field(
        metadata={
            "doc": (
                "Relation name used to reach the related object whose resolved "
                "rights may be reused."
            )
        },
    )


@dataclass(slots=True)
class AttributeDefinition:
    """
    Rights and validation definition for one canonical attribute.

    Attribute definitions describe attribute-level update privileges, generic
    validations and state transition validations.
    """

    update_privileges: frozenset[Privilege] = field(
        default_factory=frozenset,
        metadata={
            "doc": (
                "Privileges allowed to update this attribute. If empty, the "
                "attribute has no explicit attribute-level update privilege."
            )
        },
    )

    validations: list[AttributeValidation] = field(
        default_factory=list,
        metadata={
            "doc": (
                "Attribute-level validation rules, for example freshness or "
                "data-quality checks."
            )
        },
    )

    transitions: list[TransitionValidation] = field(
        default_factory=list,
        metadata={
            "doc": (
                "Transition validations for state-like attributes. These "
                "define which value transitions are allowed and under which "
                "privileges."
            )
        },
    )


@dataclass(slots=True)
class ResolutionInfo:
    """
    Optional debug information produced during rights resolution.

    This model is not required for runtime validation. It can be attached to
    resolved models later if traceability, explanations or debugging output
    become necessary.
    """

    superclass_id: str | None = field(
        default=None,
        metadata={
            "doc": (
                "Identifier of the superclass used during resolution, if any."
            )
        },
    )

    derived_from: tuple[DerivedRights, ...] = field(
        default_factory=tuple,
        metadata={
            "doc": (
                "Derived-rights declarations that contributed to the resolved "
                "definition."
            )
        },
    )

    inherited_attributes: frozenset[str] = field(
        default_factory=frozenset,
        metadata={
            "doc": (
                "Attribute identifiers inherited from superclass definitions."
            )
        },
    )

    inherited_rules: frozenset[str] = field(
        default_factory=frozenset,
        metadata={
            "doc": (
                "Rule-set identifiers inherited or expanded during resolution."
            )
        },
    )