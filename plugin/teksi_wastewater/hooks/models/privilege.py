from dataclasses import dataclass

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
