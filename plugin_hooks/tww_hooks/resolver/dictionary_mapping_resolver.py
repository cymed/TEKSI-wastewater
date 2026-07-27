from __future__ import annotations

from dataclasses import dataclass

from ..capabilities.mapping import (
    DictionaryMappingCapability,
)
from ..models.mapping import (
    AttributeMapping,
    ClassMapping,
    ModelMapping,
)


@dataclass(slots=True, frozen=True)
class DictionaryMappingResolver:
    """
    Builds a canonical ModelMapping from dictionary metadata.

    The dictionary tables already contain authoritative mappings between
    INTERLIS identifiers and canonical TWW identifiers. This resolver converts
    those metadata records into a runtime ModelMapping that can be consumed
    through ModelMappingCapability.

    Explicit YAML mappings may still override or supplement the resulting
    model mapping.
    """

    dictionary: DictionaryMappingCapability

    def resolve(self) -> ModelMapping:
        classes: dict[str, ClassMapping] = {}

        for ili_class_name, tww_class_id in (
            self.dictionary.table_mapping.items()
        ):
            classes[ili_class_name] = ClassMapping(
                tww_class_id=tww_class_id,
                attributes=self._attributes_for_class(
                    ili_class_name,
                ),
            )

        return ModelMapping(
            classes=classes,
            is_ssot=False,
        )

    def _attributes_for_class(
        self,
        ili_class_name: str,
    ) -> dict[str, AttributeMapping]:
        attributes: dict[str, AttributeMapping] = {}

        for (
            cls_name,
            ili_attribute,
        ), (
            tww_class_id,
            tww_attr_id,
        ) in self.dictionary.attribute_mapping.items():

            if cls_name != ili_class_name:
                continue

            attributes[ili_attribute] = AttributeMapping(
                tww_class_id=tww_class_id,
                tww_attr_id=tww_attr_id,
            )

        return attributes