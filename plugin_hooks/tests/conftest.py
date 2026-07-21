from pathlib import Path
from collections.abc import Mapping
import pytest


from tww_hooks.parser.provider_rights_parser import ProviderRightsParser
from tww_hooks.parser.rights_parser import RightsParser
from tww_hooks.models.provider import Provider, ResolvedProvider
from tww_hooks.resolver.rights_resolver import RightsResolver
from tww_hooks.resolver.provider_resolver import ProviderResolver

from teksi_hooks.ili_definitions import Standardoid
from ..models.rights import (
    AttributeDefinition,
    ClassDefinition,
    RightsDefinition,
    ResolvedClassDefinition,
)

DATA_DIR = Path(__file__).parent / "data"


@pytest.fixture
def definition() -> RightsDefinition:
    return RightsParser().parse_file(
        DATA_DIR / "rights_parser_minimal.yaml",
    )


@pytest.fixture
def providers() -> tuple[Provider, ...]:
    return ProviderRightsParser().parse_file(
        DATA_DIR / "provider_rights_minimal.yaml",
    )

@pytest.fixture
def resolved_providers(
    providers: tuple[Provider, ...],
) -> dict[Standardoid, ResolvedProvider]:
    return ProviderResolver().resolve_all(
        providers,
    )

@pytest.fixture
def resolved_rights(
    definition: RightsDefinition,
) ->  Mapping[str, ResolvedClassDefinition]:
    return RightsResolver().resolve(
        definition,
    )
