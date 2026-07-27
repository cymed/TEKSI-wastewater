
from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any

from .privilege import Privilege
from .rulesets import StateTransitionRule






dataclass(slots=True, frozen=True)
class AttributePermission:
    """
    Describes a privilege requirement for one concrete attribute.

    This is a lightweight runtime representation used when permission checks
    need to be expressed at attribute level.
    """

    table_name: str = field(
        metadata={
            "doc": (
                "Canonical table or class identifier containing the attribute."
            )
        },
    )

    attribute_name: str = field(
        metadata={
            "doc": (
                "Canonical attribute identifier for which the privilege applies."
            )
        },
    )

    privilege: Privilege = field(
        metadata={
            "doc": (
                "Privilege required to modify or access the attribute."
            )
        },
    )


@dataclass(slots=True, frozen=True)
class AttributeChange:
    """
    Represents the change of a single attribute within a row-level change.

    The row-level context, such as table name, object id and operation type,
    remains on `Change`. This object only describes the changed attribute
    itself.
    """

    attribute_name: str = field(
        metadata={
            "doc": (
                "Name of the changed attribute."
            )
        },
    )

    old_value: Any | None = field(
        metadata={
            "doc": (
                "Previous value of the attribute. For inserts this is usually "
                "`None`."
            )
        },
    )

    new_value: Any | None = field(
        metadata={
            "doc": (
                "Submitted or resulting value of the attribute. For deletes "
                "this is usually `None`."
            )
        },
    )


@dataclass(slots=True)
class Change:
    """
    Represents a row-level change.

    A change describes one inserted, updated or deleted object. Attribute-level
    changes can be derived from `old_values` and `new_values` via
    `changed_attributes`.
    """

    table_name: str = field(
        metadata={
            "doc": (
                "Canonical table or class identifier affected by the change."
            )
        },
    )

    object_id: str = field(
        metadata={
            "doc": (
                "Object identifier of the changed row."
            )
        },
    )

    operation: ChangeOperation = field(
        metadata={
            "doc": (
                "Type of row-level operation: insert, update or delete."
            )
        },
    )

    old_values: dict[str, Any] = field(
        metadata={
            "doc": (
                "Attribute values before the change. For inserts this is "
                "usually empty."
            )
        },
    )

    new_values: dict[str, Any] = field(
        metadata={
            "doc": (
                "Attribute values after the change. For deletes this is "
                "usually empty."
            )
        },
    )

    @property
    def changed_attributes(
        self,
    ) -> frozenset:
        """
        Return attribute-level changes derived from old and new row values.
        Attributes whose old and new values are equal are omitted.
        """

        attribute_names = (
            set(self.old_values)
            | set(self.new_values)
        )

        return frozenset(
            AttributeChange(
                attribute_name=attribute,
                old_value=self.old_values.get(attribute),
                new_value=self.new_values.get(attribute),
            )
            for attribute in attribute_names
            if self.old_values.get(attribute)
            != self.new_values.get(attribute)
        )

class ChangeOperation(StrEnum):
    """
    Supported row-level change operations.
    """

    INSERT = "insert"
    UPDATE = "update"
    DELETE = "delete"

class ValidationSeverity(StrEnum):
    """
    Severity levels used by validation findings.
    """

    INFO = "info"
    WARNING = "warning"
    ERROR = "error"

@dataclass(slots=True, frozen=True)
class ValidationFinding:
    """
    One validation finding emitted during validation.
    """

    severity: ValidationSeverity = field(
        metadata={
            "doc": (
                "Severity of the finding."
            )
        },
    )

    message: str = field(
        metadata={
            "doc": (
                "Human-readable validation message."
            )
        },
    )


@dataclass(slots=True, frozen=True)
class AttributeValidation:
    """
    Describes a validation rule attached to an attribute.

    This is intentionally lightweight. The `id` identifies the validation
    implementation, while `level` controls the emitted severity.
    """

    id: str = field(
        metadata={
            "doc": (
                "Identifier of the validation rule, for example "
                "`newer_than_existing`."
            )
        },
    )

    level: ValidationSeverity = field(
        metadata={
            "doc": (
                "Severity emitted when this validation produces a finding."
            )
        },
    )

@dataclass(slots=True, frozen=True)
class TransitionValidation:
    """
    Describes transition validation for a class based on  state-like attributes.

    The transition graph is expressed as a set of `StateTransitionRule`
    instances. `allow_transitive` controls whether indirect paths through
    the transition graph are accepted.
    """

    ruleset: frozenset[StateTransitionRule] = field(
        metadata={
            "doc": (
                "Allowed state transition rules for the attribute."
            )
        },
    )

    allow_transitive: bool = field(
        metadata={
            "doc": (
                "Whether transitive transitions are allowed. If true, a "
                "transition may be accepted when a path exists through the "
                "transition graph, even if no direct edge exists."
            )
        },
    )
