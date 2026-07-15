from dataclasses import dataclass
from typing import Any

from teksi_hooks.ili_definitions import Standardoid

from .privilege import Privilege


@dataclass(slots=True, frozen=True)
class ProviderAssignment:
    dataowner_oid: Standardoid
    privileges: frozenset[Privilege]


@dataclass(slots=True, frozen=True)
class Provider:
    name: str
    organisation_oid: Standardoid
    roles: frozenset[ProviderAssignment]
