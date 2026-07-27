from tww_hooks.capabilities.rights import (
    RightsCapability,
    DerivedRightsCapability,
)
from tww_hooks.models.privilege import Privilege


def test_rights_capability_returns_class_definition(
    resolved_rights,
) -> None:
    capability = RightsCapability(
        classes=resolved_rights,
    )

    cls = capability.class_definition(
        "wastewater_structure",
    )

    assert cls.id == "wastewater_structure"


def test_rights_capability_returns_attribute_definition(
    resolved_rights,
) -> None:
    capability = RightsCapability(
        classes=resolved_rights,
    )

    attribute = capability.attribute_definition(
        "wastewater_structure",
        "status",
    )

    assert attribute.update_privileges == frozenset(
        {
            Privilege.DBW_GEP,
            Privilege.DBW_WI,
        }
    )


def test_rights_capability_returns_update_privileges(
    resolved_rights,
) -> None:
    capability = RightsCapability(
        classes=resolved_rights,
    )

    assert capability.update_privileges(
        "wastewater_structure",
        "status",
    ) == frozenset(
        {
            Privilege.DBW_GEP,
            Privilege.DBW_WI,
        }
    )


def test_rights_capability_returns_crud_rules(
    resolved_rights,
) -> None:
    capability = RightsCapability(
        classes=resolved_rights,
    )

    assert len(
        capability.create_rules(
            "wastewater_structure",
        )
    ) == 2

    assert len(
        capability.update_rules(
            "wastewater_structure",
        )
    ) == 2


def test_rights_capability_try_class_definition_returns_none(
    resolved_rights,
) -> None:
    capability = RightsCapability(
        classes=resolved_rights,
    )

    assert capability.try_class_definition(
        "does_not_exist",
    ) is None


def test_rights_capability_try_attribute_definition_returns_none(
    resolved_rights,
) -> None:
    capability = RightsCapability(
        classes=resolved_rights,
    )

    assert capability.try_attribute_definition(
        "wastewater_structure",
        "does_not_exist",
    ) is None

