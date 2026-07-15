
from dataclasses import dataclass

from .privilege import Privilege
from .conditions import Condition

class Rule:
    pass


@dataclass(slots=True, frozen=True)
class PrivilegeRule(Rule):
    privileges: frozenset[Privilege]
    when: Condition | None = None


@dataclass(slots=True, frozen=True)
class OwnershipRule(Rule):
    privileges: frozenset[Privilege]
    attribute: str

@dataclass(slots=True, frozen=True)
class OwnershipRule(Rule):
    privileges: frozenset[Privilege]
    attribute: str


@dataclass(slots=True, frozen=True)
class StateTransitionRule(Rule):
    privileges: frozenset[Privilege]
    from_value: str | None = None
    to_value: str | None = None