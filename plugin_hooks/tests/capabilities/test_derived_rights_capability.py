from tww_hooks.capabilities.rights import DerivedRightsCapability


def test_derived_rights_capability_returns_networkelement_definition(
    resolved_rights,
) -> None:
    capability = DerivedRightsCapability(
        rights=resolved_rights,
    )

    definitions = capability.derived_rights(
        "wastewater_networkelement",
    )

    assert len(
        definitions,
    ) == 1

    definition = definitions[0]

    assert definition.class_id == (
        "wastewater_structure"
    )

    assert definition.local_attribute == (
        "fk_wastewater_structure"
    )

    assert definition.remote_attribute == (
        "obj_id"
    )


def test_derived_rights_capability_returns_reach_point_definitions(
    resolved_rights,
) -> None:
    capability = DerivedRightsCapability(
        rights=resolved_rights,
    )

    definitions = capability.derived_rights(
        "reach_point",
    )

    assert len(
        definitions,
    ) == 2

    derived_targets = {
        (
            definition.class_id,
            definition.remote_attribute,
        )
        for definition in definitions
    }

    assert derived_targets == {
        (
            "reach",
            "fk_reach_point_from",
        ),
        (
            "reach",
            "fk_reach_point_to",
        ),
    }


def test_derived_rights_capability_returns_multiple_sources(
    resolved_rights,
) -> None:
    capability = DerivedRightsCapability(
        rights=resolved_rights,
    )

    definitions = capability.derived_rights(
        "reach_point",
    )

    assert len(
        definitions,
    ) > 1


def test_derived_rights_capability_try_returns_none_for_unknown_class(
    resolved_rights,
) -> None:
    capability = DerivedRightsCapability(
        rights=resolved_rights,
    )

    assert capability.try_derived_rights(
        "does_not_exist",
    ) is None


def test_derived_rights_capability_raises_for_unknown_class(
    resolved_rights,
) -> None:
    capability = DerivedRightsCapability(
        rights=resolved_rights,
    )

    try:
        capability.derived_rights(
            "does_not_exist",
        )
    except KeyError as exc:
        assert "Unknown class" in str(
            exc,
        )
    else:
        raise AssertionError(
            "Expected KeyError"
        )