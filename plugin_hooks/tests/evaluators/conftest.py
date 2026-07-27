import pytest
from tww_hooks.capabilities.relation_lookup import RelationLookupCapability

from tww_hooks.models.rights import CanonicalDerivedRights
from tww_hooks.models.canonical_object import CanonicalObjectIdentity,CanonicalObject

class FakeRelationLookupCapability(
    RelationLookupCapability,
):
    def __init__(
        self,
        derived_rights: CanonicalDerivedRights | None = None,
        objects: dict[
            CanonicalObjectIdentity,
            CanonicalObject,
        ] | None = None,
    ):
        self.derived_rights = (
            derived_rights
            if derived_rights is not None
            else CanonicalDerivedRights()
        )

        self.objects = (
            objects
            if objects is not None
            else {}
        )

    def resolve_derived_rights(
        self,
        *,
        local_objects,
        relation,
    ) -> CanonicalDerivedRights:
        return self.derived_rights

    def current_object(
        self,
        identity: CanonicalObjectIdentity,
    ) -> CanonicalObject | None:
        return self.objects.get(
            identity,
        )

@pytest.fixture
def relation_lookup():
    return FakeRelationLookupCapability(
        derived_rights=CanonicalDerivedRights(),
        objects={},
    )