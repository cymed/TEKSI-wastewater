from teksi_hooks.ili_definitions import Standardoid

from tww_hooks.capabilities.provider import ResolvedProviderCapability
from tww_hooks.models.privilege import Privilege


def test_provider_capability_returns_privileges(
    resolved_providers,
) -> None:
    provider = resolved_providers[
        Standardoid("ch000000geping01")
    ]

    capability = ResolvedProviderCapability(
        provider=provider,
    )

    assert capability.privileges_for(
        Standardoid("ch000000awgde001"),
    ) == frozenset(
        {
            Privilege.DBW_WI,
            Privilege.DBW_GEP,
        }
    )


def test_provider_capability_checks_privilege(
    resolved_providers,
) -> None:
    provider = resolved_providers[
        Standardoid("ch000000geping01")
    ]

    capability = ResolvedProviderCapability(
        provider=provider,
    )

    assert capability.has_privilege(
        Standardoid("ch000000awgde001"),
        Privilege.DBW_GEP,
    )


def test_provider_capability_returns_empty_for_unknown_dataowner(
    resolved_providers,
) -> None:
    provider = resolved_providers[
        Standardoid("ch000000geping01")
    ]

    capability = ResolvedProviderCapability(
        provider=provider,
    )

    assert capability.privileges_for(
        Standardoid("ch999999unknown"),
    ) == frozenset()