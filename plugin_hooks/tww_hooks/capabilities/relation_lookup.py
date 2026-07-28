from __future__ import annotations

from typing import Any
from collections.abc import Sequence

from ..models.canonical_object import (
    CanonicalObject,
    CanonicalObjectIdentity,
)
from ..models.rights import (
    DerivedRights,
    CanonicalDerivedRights,
)


class RelationLookupCapability:
    """
    Capability providing canonical object relationship lookups.

    Implementations may use:

    - SQL
    - ORM models
    - in-memory data
    - test fixtures

    RightsEvaluator only depends on this abstraction and remains
    implementation-independent.
    """

    def canonical_objects(
        self,
        *,
        local_class_id: str,
        remote_class_id: str,
        local_attribute: str,
        remote_attribute: str,
        value: Any,
    ) -> Sequence[
        CanonicalObjectIdentity
    ]:
        """
        Return related objects matching the supplied join condition.

        Conceptually evaluates:

            local.<local_attribute>
                =
            remote.<remote_attribute>

        Parameters
        ----------
        local_class_id:
            Canonical class currently being evaluated.

        remote_class_id:
            Canonical class from which rights may be derived.

        local_attribute:
            Local attribute participating in the join.

        remote_attribute:
            Remote attribute participating in the join.

        value:
            Attribute value used for the lookup.

        Returns
        -------
        Sequence[CanonicalObjectIdentity]
            Matching related objects.
        """

        raise NotImplementedError

    def resolve_derived_rights(
        self,
        *,
        local_objects: tuple[
            CanonicalObjectIdentity,
            ...
        ],
        relation: DerivedRights,
    ) -> CanonicalDerivedRights:
        """
        Resolve rights inheritance through a configured relation.
        """

        remote_objects: list[
            CanonicalObjectIdentity
        ] = []

        for local_object in local_objects:
            try:
                value = local_object.attributes[
                    relation.local_attribute
                ]
            except KeyError:
                continue

            remote_objects.extend(
                self.canonical_objects(
                    local_class_id=(
                        local_object.class_id
                    ),
                    remote_class_id=(
                        relation.class_id
                    ),
                    local_attribute=(
                        relation.local_attribute
                    ),
                    remote_attribute=(
                        relation.remote_attribute
                    ),
                    value=value,
                )
            )

        return CanonicalDerivedRights(
            local_objects=tuple(
                local_objects,
            ),
            remote_objects=tuple(
                remote_objects,
            ),
        )

    def current_object(
        self,
        identity: CanonicalObjectIdentity,
    ) -> CanonicalObject | None:
        """
        Return the current canonical object or `None` if it no longer exists.

        CanonicalObjectIdentity
                ↓
        Current database object
        """

        raise NotImplementedError