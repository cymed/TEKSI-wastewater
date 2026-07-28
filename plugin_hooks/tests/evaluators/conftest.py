from typing import Sequence

import pytest
from tww_hooks.capabilities.relation_lookup import RelationLookupCapability

from tww_hooks.models.rights import CanonicalDerivedRights
from tww_hooks.models.canonical_object import CanonicalObjectIdentity,CanonicalObject

class FakeRelationLookupCapability(
    RelationLookupCapability,
):
    def __init__(
        self,
        *,
        derived_rights: CanonicalDerivedRights,
        objects: dict[
            tuple,
            CanonicalObject,
        ],
    ):
        self.derived_rights = derived_rights
        self.objects = objects

    @staticmethod
    def _key(
        identity: CanonicalObjectIdentity,
    ) -> tuple:
        return (
            identity.class_id,
            tuple(
                sorted(
                    identity.attributes.items(),
                ),
            ),
        )

    def current_object(
        self,
        identity: CanonicalObjectIdentity,
    ) -> CanonicalObject | None:
        return self.objects.get(
            self._key(
                identity,
            ),
        )

    def canonical_objects(
        self,
        *,
        local_class_id: str,
        remote_class_id: str,
        local_attribute: str,
        remote_attribute: str,
        value,
    ) -> Sequence[
        CanonicalObject
    ]:
        return self.derived_rights.remote_objects

    def resolve_derived_rights(
        self,
        *,
        local_objects,
        relation,
    ) -> CanonicalDerivedRights:
        return self.derived_rights

@pytest.fixture
def relation_lookup():
    return FakeRelationLookupCapability(
        derived_rights=CanonicalDerivedRights(),
        objects={},
    )