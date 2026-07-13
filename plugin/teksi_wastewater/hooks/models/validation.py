from dataclasses import dataclass
from typing import Any
  
from teksi_hooks.ili_definitions import Standardoid
from enum import StrEnum




@dataclass(frozen=True, slots=True)
class PrivilegeMetadata:
    label_de: str
    label_fr: str


class Privilege(StrEnum):
    DBW_WI = "DBW_WI"
    DBW_GEP = "DBW_GEP"
    FI_BU = "FI_BU"

    @property
    def metadata(self) -> PrivilegeMetadata:
        return _PRIVILEGE_METADATA[self]


_PRIVILEGE_METADATA = {
    Privilege.DBW_WI: PrivilegeMetadata(
        label_de="Datenbewirtschafter Werkinformation",
        label_fr="Gestionnaire cadastral",
    ),
    Privilege.DBW_GEP: PrivilegeMetadata(
        label_de="Datenbewirtschafter GEP-Themen",
        label_fr="Gestionnaire PGEE",
    ),
    Privilege.FI_BU: PrivilegeMetadata(
        label_de="Fachingenieur Betrieb und Unterhalt",
        label_fr="Ingénieur de maintenance",
    ),
}


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


class ChangeOperation(StrEnum):
    INSERT = "insert"
    UPDATE = "update"
    DELETE = "delete"

from dataclasses import dataclass
from enum import StrEnum


class ValidationSeverity(StrEnum):
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"


@dataclass(slots=True, frozen=True)
class ValidationFinding:
    severity: ValidationSeverity
    message: str