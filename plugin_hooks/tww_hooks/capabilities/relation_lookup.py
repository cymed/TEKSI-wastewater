from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any
from collections.abc import Sequence

from ..models.canonical_object import (
    CanonicalObject,
    CanonicalObjectIdentity,
)

@dataclass(slots=True, frozen=True)
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

    objects: tuple[
        CanonicalObject,
        ...
    ] = field(
        default_factory=tuple,
        metadata={
            "doc": (
                "Canonical objects available for lookup. The default "
                "implementation searches this in-memory collection."
            )
        },
    )

    def canonical_objects(
        self,
        *,
        local_class_id: str,
        related_class_id: str,
        local_attribute: str,
        related_attribute: str,
        value: Any,
    ) -> Sequence[
        CanonicalObjectIdentity
    ]:
        """
        Return related objects matching the supplied join condition.

        Conceptually evaluates:

            local.<local_attribute>
                =
            related.<related_attribute>

        Parameters
        ----------
        local_class_id:
            Canonical class currently being evaluated.

        related_class_id:
            Canonical class from which rights may be derived.

        local_attribute:
            Local attribute participating in the join.

        related_attribute:
            related attribute participating in the join.

        value:
            Attribute value used for the lookup.

        Returns
        -------
        Sequence[CanonicalObjectIdentity]
            Matching related objects.
        """

        local_match_exists = False

        for obj in self._all_objects():
            if obj.identity.class_id != local_class_id:
                continue

            local_value = self._attribute_value(
                obj,
                local_attribute,
            )

            if local_value == value:
                local_match_exists = True
                break

        if not local_match_exists:
            return ()

        matches = []

        for obj in self._all_objects():
            if obj.identity.class_id != related_class_id:
                continue

            related_value = self._attribute_value(
                obj,
                related_attribute,
            )

            if related_value == value:
                matches.append(
                    obj.identity,
                )

        return tuple(
            matches,
        )

    def current_object(
        self,
        identity: CanonicalObjectIdentity,
    ) -> CanonicalObject | None:
        """
        Return the current canonical object or `None` if it no longer exists.
        """

        expected_key = self._identity_key(
            identity,
        )

        for obj in self.objects:
            if (
                self._identity_key(
                    obj.identity,
                )
                == expected_key
            ):
                return obj

        return None

    def _attribute_value(
        self,
        obj: CanonicalObject,
        attribute_name: str,
    ) -> Any:
        """
        Return an attribute value from object values or identity attributes.

        Values are checked first because normal object attributes should
        override identity metadata where both exist.
        """

        if attribute_name in obj.values:
            return obj.values[
                attribute_name
            ]

        return obj.identity.attributes.get(
            attribute_name,
        )

    def _identity_key(
        self,
        identity: CanonicalObjectIdentity,
    ) -> tuple:
        """
        Return a hashable identity key.
        """

        return (
            identity.class_id,
            tuple(
                sorted(
                    identity.attributes.items(),
                )
            ),
        )

    def _all_objects(
        self,
    ) -> tuple[
        CanonicalObject,
        ...
    ]:
        return (
            *self.local_objects,
            *self.related_objects,
        )


@dataclass(slots=True, frozen=True)
class InMemoryRelationLookupCapability(
    RelationLookupCapability,
):
    """
    In-memory relation lookup implementation.

    This implementation is intended for tests and small offline scenarios.
    Production code should use a SQL-backed or adapter-backed implementation.

    The object collections are split into local and related objects to make
    the join semantics explicit:

        local.<local_attribute>
            =
        related.<related_attribute>
    """

    local_objects: tuple[
        CanonicalObject,
        ...
    ] = field(
        default_factory=tuple,
        metadata={
            "doc": (
                "Canonical objects representing the local side of relation "
                "lookups."
            )
        },
    )

    related_objects: tuple[
        CanonicalObject,
        ...
    ] = field(
        default_factory=tuple,
        metadata={
            "doc": (
                "Canonical objects representing the related side of relation "
                "lookups."
            )
        },
    )

    def canonical_objects(
        self,
        local_class_id: str,
        related_class_id: str,
        local_attribute: str,
        related_attribute: str,
        value: Any,
    ) -> Sequence[
        CanonicalObjectIdentity
    ]:
        """
        Return related object identities matching the configured join.
        """

        local_match_exists = False

        for obj in self.local_objects:
            if obj.identity.class_id != local_class_id:
                continue

            local_value = self._attribute_value(
                obj,
                local_attribute,
            )

            if local_value == value:
                local_match_exists = True
                break

        if not local_match_exists:
            return ()

        matches: list[
            CanonicalObjectIdentity
        ] = []

        for obj in self.related_objects:
            if obj.identity.class_id != related_class_id:
                continue

            related_value = self._attribute_value(
                obj,
                related_attribute,
            )

            if related_value == value:
                matches.append(
                    obj.identity,
                )

        return tuple(
            matches,
        )

    def current_object(
        self,
        identity: CanonicalObjectIdentity,
    ) -> CanonicalObject | None:
        """
        Return the current canonical object or `None` if it no longer exists.
        """

        expected_key = self._identity_key(
            identity,
        )

        for obj in self.local_objects:
            if self._identity_key(
                obj.identity,
            ) == expected_key:
                return obj

        for obj in self.related_objects:
            if self._identity_key(
                obj.identity,
            ) == expected_key:
                return obj

        return None

    def _attribute_value(
        self,
        obj: CanonicalObject,
        attribute_name: str,
    ) -> Any:
        """
        Return an attribute value from object values or identity attributes.
        """

        if attribute_name in obj.values:
            return obj.values[
                attribute_name
            ]

        return obj.identity.attributes.get(
            attribute_name,
        )

    def _identity_key(
        self,
        identity: CanonicalObjectIdentity,
    ) -> tuple:
        """
        Return a hashable identity key.
        """

        return (
            identity.class_id,
            tuple(
                sorted(
                    identity.attributes.items(),
                )
            ),
        )