from collections.abc import Mapping
from dataclasses import dataclass, field

from ..models.privilege import Privilege
from ..models.rights import (
    AttributeDefinition,
    DerivedRights,
    ResolvedClassDefinition,
    ResolvedRights,
)
from ..models.rulesets import (
    ResolvedCrudRules,
    Rule,
)
from ..models.validation import (
    AttributeValidation,
    TransitionValidation,
)


@dataclass(slots=True, frozen=True)
class RightsCapability:
    """
    Runtime lookup capability for resolved rights definitions.

    This capability wraps resolved class definitions and exposes convenient
    query methods for class-level rules, attribute-level privileges,
    validations and transition validations.

    It should not evaluate whether an operation is allowed. Evaluation belongs
    to the rights evaluator or hook logic. This capability only answers
    metadata questions such as:

    - Which rules apply to class X?
    - Which privileges are required for attribute Y?
    - Which validations exist for attribute Z?
    """

    rights: ResolvedRights = field(
        metadata={
            "doc": (
                "Fully resolved runtime rights configuration."
            )
        },
    )
    
    def class_definition(
        self,
        class_id: str,
    ) -> ResolvedClassDefinition:
        """
        Return the resolved class definition for a canonical class id.

        Raises
        ------
        KeyError
            If the class is unknown.
        """

        try:
            return self.rights.classes[class_id]
        except KeyError as exc:
            raise KeyError(
                f"Unknown class: {class_id}"
            ) from exc

    def try_class_definition(
        self,
        class_id: str,
    ) -> ResolvedClassDefinition | None:
        """
        Return the resolved class definition if it exists, otherwise `None`.
        """

        return self.rights.classes.get(class_id)

    def attribute_definition(
        self,
        class_id: str,
        attribute_name: str,
    ) -> AttributeDefinition:
        """
        Return the attribute definition for a canonical class and attribute.

        Raises
        ------
        KeyError
            If the class or attribute is unknown.
        """

        cls = self.class_definition(
            class_id,
        )

        try:
            return cls.attributes[attribute_name]
        except KeyError as exc:
            raise KeyError(
                f"Unknown attribute {attribute_name!r} "
                f"for class {class_id!r}"
            ) from exc

    def try_attribute_definition(
        self,
        class_id: str,
        attribute_name: str,
    ) -> AttributeDefinition | None:
        """
        Return an attribute definition if it exists, otherwise `None`.

        This is useful when attributes may be unmapped, ignored or not
        relevant for rights validation.
        """

        cls = self.try_class_definition(
            class_id,
        )

        if cls is None:
            return None

        return cls.attributes.get(
            attribute_name,
        )

    def update_privileges(
        self,
        class_id: str,
        attribute_name: str,
    ) -> frozenset:
        """
        Return attribute-level update privileges.

        Raises
        ------
        KeyError
            If the class or attribute is unknown.
        """

        return self.attribute_definition(
            class_id,
            attribute_name,
        ).update_privileges

    def try_update_privileges(
        self,
        class_id: str,
        attribute_name: str,
    ) -> frozenset[Privilege] | None:
        """
        Return attribute-level update privileges if the attribute exists.

        Returns `None` if the class or attribute is unknown.
        """

        attribute = self.try_attribute_definition(
            class_id,
            attribute_name,
        )

        if attribute is None:
            return None

        return attribute.update_privileges

    def crud_rules(
        self,
        class_id: str,
    ) -> ResolvedCrudRules:
        """
        Return all resolved CRUD rules for a class.
        """

        return self.class_definition(
            class_id,
        ).crud_rules

    def validations(
        self,
        class_id: str,
        attribute_name: str,
    ) -> list:
        """
        Return attribute-level validations for a canonical attribute.
        """

        return self.attribute_definition(
            class_id,
            attribute_name,
        ).validations

    def try_validations(
        self,
        class_id: str,
        attribute_name: str,
    ) -> list[AttributeValidation] | None:
        """
        Return attribute-level validations if the attribute exists.

        Returns `None` if the class or attribute is unknown.
        """

        attribute = self.try_attribute_definition(
            class_id,
            attribute_name,
        )

        if attribute is None:
            return None

        return attribute.validations

    def transitions(
        self,
        class_id: str,
        attribute_name: str,
    ) -> list:
        """
        Return transition validations for a canonical attribute.
        """

        return self.attribute_definition(
            class_id,
            attribute_name,
        ).transitions

    def try_transitions(
        self,
        class_id: str,
        attribute_name: str,
    ) -> list[TransitionValidation] | None:
        """
        Return transition validations if the attribute exists.

        Returns `None` if the class or attribute is unknown.
        """

        attribute = self.try_attribute_definition(
            class_id,
            attribute_name,
        )

        if attribute is None:
            return None

        return attribute.transitions

    def create_rules(
        self,
        class_id: str,
    ) -> tuple[Rule, ...]:
        """
        Return resolved create rules for a class.
        """

        return self.class_definition(
            class_id,
        ).crud_rules.create_rules

    def read_rules(
        self,
        class_id: str,
    ) -> tuple[Rule, ...]:
        """
        Return resolved read rules for a class.
        """

        return self.class_definition(
            class_id,
        ).crud_rules.read_rules

    def update_rules(
        self,
        class_id: str,
    ) -> tuple[Rule, ...]:
        """
        Return resolved update rules for a class.
        """

        return self.class_definition(
            class_id,
        ).crud_rules.update_rules

    def delete_rules(
        self,
        class_id: str,
    ) -> tuple[Rule, ...]:
        """
        Return resolved delete rules for a class.
        """

        return self.class_definition(
            class_id,
        ).crud_rules.delete_rules

    def transition_rules(
        self,
        class_id: str,
        attribute_name: str,
    ) -> frozenset:
        """
        Return resolved transition rules for a canonical attribute.

        Raises
        ------
        KeyError
            If the class or attribute is unknown.
        """

        cls = self.class_definition(
            class_id,
        )

        try:
            return cls.transition_rules[
                attribute_name
            ]
        except KeyError as exc:
            raise KeyError(
                f"Unknown transition attribute "
                f"{attribute_name!r} "
                f"for class {class_id!r}"
            ) from exc

    def try_transition_rules(
    self,
    class_id: str,
    attribute_name: str,
    ):
        cls = self.try_class_definition(
            class_id,
        )

        if cls is None:
            return None

        return cls.transition_rules.get(
            attribute_name,
        )

    def allow_transitive_transitions(
        self,
    ) -> bool:
        return self.rights.allow_transitive_transitions

@dataclass(slots=True, frozen=True)
class DerivedRightsCapability:
    """
    Runtime lookup capability for rights-derivation definitions.

    This capability exposes relationships through which rights may be
    inherited from related canonical objects.
    """
    rights: ResolvedRights = field(
        metadata={
            "doc": (
                "Fully resolved runtime rights configuration."
            )
        },
    )

    def derived_rights(
        self,
        class_id: str,
    ) -> tuple[DerivedRights, ...]:
        """
        Return rights-derivation definitions for a class.

        Raises
        ------
        KeyError
            If the class is unknown.
        """

        try:
            return self.rights.derived_rights[class_id]
        except KeyError as exc:
            raise KeyError(
                f"Unknown class: {class_id}"
            ) from exc

    def try_derived_rights(
        self,
        class_id: str,
    ) -> tuple[DerivedRights, ...] | None:
        """
        Return rights-derivation definitions if the class exists.

        Returns `None` if the class is unknown.
        """

        return self.rights.derived_rights.get(
            class_id,
        )

@dataclass(slots=True, frozen=True)
class SubclassRightsCapability:
    """
    Runtime lookup capability for subclass-based rights inheritance.

    The capability exposes child classes whose rights may be considered
    when evaluating permissions on a parent class.
    """

    rights: ResolvedRights = field(
        metadata={
            "doc": (
                "Fully resolved runtime rights configuration."
            )
        },
    )

    def subclasses(
        self,
        class_id: str,
    ) -> tuple[str, ...]:
        """
        Return subclasses contributing rights to the supplied class.

        Raises
        ------
        KeyError
            If the class is unknown.
        """

        try:
            return self.rights.subclass_rights[class_id]
        except KeyError as exc:
            raise KeyError(
                f"Unknown class: {class_id}"
            ) from exc

    def try_subclasses(
        self,
        class_id: str,
    ) -> tuple[str, ...] | None:
        """
        Return subclasses if the class exists.

        Returns
        -------
        tuple[str, ...] | None
            Contributing subclasses or `None` if the class is unknown.
        """

        return self.rights.subclass_rights.get(
            class_id,
        )