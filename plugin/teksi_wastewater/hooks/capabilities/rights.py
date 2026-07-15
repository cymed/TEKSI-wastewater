from collections.abc import Mapping

from ..models.rights import AttributeDefinition, AttributeValidation, CrudRules, Privilege, ResolvedClassDefinition, TransitionValidation
from ..models.rulesets import Rule

class RightsCapability:
    classes: Mapping[str, ResolvedClassDefinition]

    def class_definition(
        self,
        class_id: str,
    ) -> ResolvedClassDefinition: 
        try:
            return self.classes[class_id]
        except KeyError as exc:
            raise KeyError(
                f"Unknown class: {class_id}"
            ) from exc


    def attribute_definition(
        self,
        class_id: str,
        attribute_name: str,
    ) -> AttributeDefinition:
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
        cls = self.classes.get(class_id)

        if cls is None:
            return None

        return cls.attributes.get(attribute_name)

    def update_privileges(
        self,
        class_id: str,
        attribute_name: str,
    ) -> frozenset[Privilege]:
        return self.attribute_definition(
            class_id,
            attribute_name,
        ).update_privileges

    def crud_rules(
        self,
        class_id: str,
    ) -> CrudRules:
        return self.class_definition(
            class_id,
        ).crud_rules


    def validations(
        self,
        class_id: str,
        attribute_name: str,
    ) -> list[AttributeValidation]:
        return self.attribute_definition(
            class_id,
            attribute_name,
        ).validations

    def transitions(
        self,
        class_id: str,
        attribute_name: str,
    ) -> list[TransitionValidation]:
        return self.attribute_definition(
            class_id,
            attribute_name,
        ).transitions

    def create_rules(
        self,
        class_id: str,
    ) -> tuple[Rule, ...]:
        return self.class_definition(
            class_id,
        ).crud_rules.create_rules

    def read_rules(
        self,
        class_id: str,
    ) -> tuple[Rule, ...]:
        return self.class_definition(
            class_id,
        ).crud_rules.read_rules


    def update_rules(
        self,
        class_id: str,
    ) -> tuple[Rule, ...]:
        return self.class_definition(
            class_id,
        ).crud_rules.update_rules


    def delete_rules(
        self,
        class_id: str,
    ) -> tuple[Rule, ...]:
        return self.class_definition(
            class_id,
        ).crud_rules.delete_rules
