from pathlib import Path
import pytest

from tww_hooks.parser.provider_rights_parser import ProviderRightsParser
from tww_hooks.models.privilege import Privilege


DATA_DIR = Path(__file__).parent / "data"

@pytest.fixture
def providers() -> Sequence[Provider]:
    return ProviderRightsParser().parse_file(
        DATA_DIR / "provider_mapping_minimal.yaml",
    )


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