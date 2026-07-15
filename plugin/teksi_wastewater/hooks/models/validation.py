from dataclasses import dataclass
from typing import Any
  
from teksi_hooks.ili_definitions import Standardoid
from enum import StrEnum
from .rulesets import StateTransitionRule
from .privilege import Privilege




@dataclass(slots=True, frozen=True)
class AttributePermission:
    table_name: str
    attribute_name: str
    privilege: Privilege

@dataclass(slots=True)
class Change:
    table_name: str
    object_id: str

    operation: ChangeOperation

    old_values: dict[str, Any]
    new_values: dict[str, Any]


    @property
    def changed_attributes(
        self,
    ) -> frozenset[AttributeChange]:
        return frozenset(
                AttributeChange(
                    attribute_name=attribute,
                    old_value=self.old_values.get(attribute),
                    new_value=self.new_values.get(attribute),
                )
                for attribute in ...
            )



class ChangeOperation(StrEnum):
    INSERT = "insert"
    UPDATE = "update"
    DELETE = "delete"


class ValidationSeverity(StrEnum):
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"


@dataclass(slots=True, frozen=True)
class ValidationFinding:
    severity: ValidationSeverity
    message: str


@dataclass(slots=True, frozen=True)
class AttributeValidation:
    id: str
    level: ValidationSeverity


@dataclass(slots=True, frozen=True)
class TransitionValidation:
    ruleset: frozenset[StateTransitionRule]
    allow_transitive: bool


@dataclass(slots=True, frozen=True)
class AttributeChange:
    attribute_name: str
    old_value: Any | None
    new_value: Any | None
