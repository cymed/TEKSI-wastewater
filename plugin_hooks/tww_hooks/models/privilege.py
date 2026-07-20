from dataclasses import dataclass
from enum import StrEnum


@dataclass(frozen=True, slots=True)
class PrivilegeMetadata:
    """
    Human-readable metadata for a provider privilege.

    The metadata is used for display, documentation and user-facing messages.
    The privilege enum itself remains the stable machine-readable identifier.
    """

    label_de: str
    label_fr: str


class Privilege(StrEnum):
    """
    Provider privilege used by the rights validation model.

    Privileges describe which functional domain a provider may edit for a
    given data owner. They are evaluated together with the provider's
    permissions and the configured class or attribute rights.
    """

    DBW_WI = "DBW_WI"
    DBW_GEP = "DBW_GEP"
    FI_BU = "FI_BU"

    @property
    def metadata(self) -> PrivilegeMetadata:
        """
        Return localized display metadata for this privilege.
        """
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