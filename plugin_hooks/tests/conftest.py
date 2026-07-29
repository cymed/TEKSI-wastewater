from pathlib import Path
from collections.abc import Mapping
import pytest



from teksi_hooks.ili_definitions import Standardoid
from tww_hooks.models.rights import (
    AttributeDefinition,
    ClassDefinition,
    RightsDefinition,
    ResolvedClassDefinition,
)
from tww_hooks.parser.provider_rights_parser import ProviderRightsParser
from tww_hooks.parser.rights_parser import RightsParser, WildcardRightsParser
from tww_hooks.parser.model_mapping_parser import ModelMappingParser

from tww_hooks.models.provider import Provider, ResolvedProvider
from tww_hooks.models.mapping import ModelMapping

from tww_hooks.capabilities.conditions import ConditionsCapability
from tww_hooks.capabilities.rights import RightsCapability, DerivedRightsCapability, SubclassRightsCapability
from tww_hooks.capabilities.privilege import ResolvedProviderCapability
from tww_hooks.capabilities.validation import (
    ValidationRegistry,
)

from tww_hooks.resolver.rights_resolver import RightsResolver
from tww_hooks.resolver.provider_resolver import ProviderResolver


from tww_hooks.evaluators.rights import RightsEvaluator

DATA_DIR = Path(__file__).parent / "parser/data"

@pytest.fixture
def wildcard_rights_definition() -> RightsDefinition:
    return WildcardRightsParser().parse_file(
        DATA_DIR / "provider_privilege_agxx.yaml",
    )

@pytest.fixture
def rights_definition() -> RightsDefinition:
    return RightsParser().parse_file(
        DATA_DIR / "rights_parser_minimal.yaml",
    )

@pytest.fixture
def rights_definition_non_transitive() -> RightsDefinition:
    return RightsParser().parse_file(
        DATA_DIR / "rights_parser_minimal_non_transitive.yaml",
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
    rights_definition: RightsDefinition,
) -> Mapping[str, ResolvedClassDefinition]:
    return RightsResolver().resolve(
        rights_definition,
    )


@pytest.fixture
def agxx_mapping() -> ModelMapping:
    return ModelMappingParser().parse_file(
        DATA_DIR / "agxx_mapping_minimal.yaml",
    )

@pytest.fixture
def derived_rights(
    rights_definition,
):

    return RightsResolver().resolve_derived_rights_config(
        rights_definition,
    )

@pytest.fixture
def evaluator(
    resolved_rights,
    resolved_providers,
    relation_lookup,
):
    return RightsEvaluator(
        rights=RightsCapability(
            rights=resolved_rights,
        ),
        provider=ResolvedProviderCapability(
            provider=resolved_providers[
                Standardoid("ch000000geping01")
            ],
        ),
        conditions=ConditionsCapability(),
        relation_lookup=relation_lookup,
        derived_rights=DerivedRightsCapability(
            rights=resolved_rights,
        ),
        subclass_rights=SubclassRightsCapability(
            rights=resolved_rights,
        ),
    )


@pytest.fixture
def registry() -> ValidationRegistry:
    return ValidationRegistry()