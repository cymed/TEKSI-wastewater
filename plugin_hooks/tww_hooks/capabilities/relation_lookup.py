from __future__ import annotations

from dataclasses import dataclass
from typing import Any
from collections.abc import Mapping, Sequence

from __future__ import annotations

from ..models.canonical_object import (
    CanonicalObject,
    CanonicalObjectIdentity,
)
from ..models.rights import (
    DerivedRights,
    CanonicalDerivedRights,
)



@dataclass(slots=True, frozen=True)
class RelatedObject:
    """
    Canonical related object reference.

    This structure is intentionally lightweight and contains only the
    information required by rights evaluation and future diff processing.
    """

    class_id: str

    identity: Mapping[str, Any]


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

    def related_objects(
        self,
        *,
        local_class_id: str,
        remote_class_id: str,
        local_attribute: str,
        remote_attribute: str,
        value: Any,
    ) -> Sequence:
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
        Sequence[RelatedObject]
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
        raise NotImplementedError

    def current_object(
        self,
        identity: CanonicalObjectIdentity,
    ) -> CanonicalObject | None:
        """
        Return the current canonical object or `None` if it no longer exists.
        """

        raise NotImplementedError
