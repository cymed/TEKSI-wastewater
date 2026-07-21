from pathlib import Path
import pytest

from teksi_hooks.ili_definitions import Standardoid
from tww_hooks.models.provider import ResolvedProvider
from tww_hooks.models.privilege import Privilege
from tww_hooks.capabilities.provider import ResolvedProviderCapability


def test_provider_rights_parser_imports_all_providers(providers) -> None:
    provider_names = {
        provider.name
        for provider in providers
    }

    assert provider_names == {
        "Muster Ingenieure AG",
        "Muster Ingenieure SA",
        "Muster Geometer GmbH",
        "Verband Abwasser Region Beispiel",
        "Gemeinde Musterfingen",
        "Gemeinde Musterlingen",
    }


def test_provider_rights_parser_imports_provider_oids(providers) -> None:
    provider = next(
        provider
        for provider in providers
        if provider.name == "Muster Ingenieure AG"
    )

    assert str(provider.organisation_oid) == "ch000000geping01"


def test_provider_rights_parser_imports_permissions(providers) -> None:
    provider = next(
        provider
        for provider in providers
        if str(provider.organisation_oid) == "ch000000geping01"
    )

    permissions_by_owner = {
        str(permission.dataowner_oid): permission
        for permission in provider.permissions
    }

    assert permissions_by_owner[
        "ch000000awverbnd"
    ].privileges == frozenset(
        {
            Privilege.DBW_GEP,
        }
    )

    assert permissions_by_owner[
        "ch000000awgde001"
    ].privileges == frozenset(
        {
            Privilege.DBW_WI,
            Privilege.DBW_GEP,
        }
    )

    assert permissions_by_owner[
        "ch000000awgde002"
    ].privileges == frozenset(
        {
            Privilege.FI_BU,
        }
    )


def test_provider_rights_parser_imports_empty_permissions_when_omitted(providers) -> None:
    provider = next(
        provider
        for provider in providers
        if provider.name == "Gemeinde Musterlingen"
    )

    assert str(provider.organisation_oid) == "ch000000awgde002"
    assert provider.permissions == frozenset()


def test_provider_rights_parser_imports_association_permissions(providers) -> None:
    provider = next(
        provider
        for provider in providers
        if provider.name == "Verband Abwasser Region Beispiel"
    )

    assert str(provider.organisation_oid) == "ch000000awverbnd"

    permission = next(
        iter(provider.permissions),
    )

    assert str(permission.dataowner_oid) == "ch000000awverbnd"
    assert permission.privileges == frozenset(
        {
            Privilege.FI_BU,
        }
    )


def test_provider_resolver_resolves_all_providers(
    resolved_providers: dict[Standardoid, ResolvedProvider],
) -> None:
    assert set(resolved_providers) == {
        Standardoid("ch000000geping01"),
        Standardoid("ch000000geping02"),
        Standardoid("ch000000dbwwi001"),
        Standardoid("ch000000awverbnd"),
        Standardoid("ch000000awgde001"),
        Standardoid("ch000000awgde002"),
    }


def test_provider_resolver_keeps_provider_metadata(
    resolved_providers: dict[Standardoid, ResolvedProvider],
) -> None:
    provider = resolved_providers[
        Standardoid("ch000000geping01")
    ]

    assert provider.name == "Muster Ingenieure AG"
    assert provider.organisation_oid == Standardoid(
        "ch000000geping01",
    )


def test_provider_resolver_resolves_permissions(
    resolved_providers: dict[Standardoid, ResolvedProvider],
) -> None:
    provider = resolved_providers[
        Standardoid("ch000000geping01")
    ]

    assert provider.permissions[
        Standardoid("ch000000awverbnd")
    ] == frozenset(
        {
            Privilege.DBW_GEP,
        }
    )

    assert provider.permissions[
        Standardoid("ch000000awgde001")
    ] == frozenset(
        {
            Privilege.DBW_WI,
            Privilege.DBW_GEP,
        }
    )

    assert provider.permissions[
        Standardoid("ch000000awgde002")
    ] == frozenset(
        {
            Privilege.FI_BU,
        }
    )


def test_provider_resolver_handles_provider_without_permissions(
    resolved_providers: dict[Standardoid, ResolvedProvider],
) -> None:
    provider = resolved_providers[
        Standardoid("ch000000awgde002")
    ]

    assert provider.name == "Gemeinde Musterlingen"
    assert provider.permissions == {}


def test_resolved_provider_capability_returns_privileges(
    resolved_providers: dict[Standardoid, ResolvedProvider],
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


def test_resolved_provider_capability_checks_existing_privilege(
    resolved_providers: dict[Standardoid, ResolvedProvider],
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


def test_resolved_provider_capability_rejects_missing_privilege(
    resolved_providers: dict[Standardoid, ResolvedProvider],
) -> None:
    provider = resolved_providers[
        Standardoid("ch000000geping01")
    ]

    capability = ResolvedProviderCapability(
        provider=provider,
    )

    assert not capability.has_privilege(
        Standardoid("ch000000awverbnd"),
        Privilege.DBW_WI,
    )


def test_provider_resolver_resolves_all_providers(
    resolved_providers,
) -> None:
    assert set(resolved_providers) == {
        Standardoid("ch000000geping01"),
        Standardoid("ch000000geping02"),
        Standardoid("ch000000dbwwi001"),
        Standardoid("ch000000awverbnd"),
        Standardoid("ch000000awgde001"),
        Standardoid("ch000000awgde002"),
    }


def test_provider_resolver_keeps_provider_metadata(
    resolved_providers,
) -> None:
    provider = resolved_providers[
        Standardoid("ch000000geping01")
    ]

    assert provider.name == "Muster Ingenieure AG"
    assert provider.organisation_oid == Standardoid(
        "ch000000geping01",
    )


def test_provider_resolver_resolves_permissions(
    resolved_providers,
) -> None:
    provider = resolved_providers[
        Standardoid("ch000000geping01")
    ]

    assert provider.permissions[
        Standardoid("ch000000awverbnd")
    ] == frozenset(
        {
            Privilege.DBW_GEP,
        }
    )

    assert provider.permissions[
        Standardoid("ch000000awgde001")
    ] == frozenset(
        {
            Privilege.DBW_WI,
            Privilege.DBW_GEP,
        }
    )

    assert provider.permissions[
        Standardoid("ch000000awgde002")
    ] == frozenset(
        {
            Privilege.FI_BU,
        }
    )

def test_provider_resolver_handles_provider_without_permissions(
    resolved_providers,
) -> None:
    provider = resolved_providers[
        Standardoid("ch000000awgde002")
    ]

    assert provider.name == "Gemeinde Musterlingen"
    assert provider.permissions == {}
