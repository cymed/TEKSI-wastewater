
from __future__ import annotations
from dataclasses import dataclass
from typing import Protocol

from ..models.mapping import (
    AttributeMapping,
    ClassMapping,
    ValueMapping,
    ModelMapping,
)


@dataclass(slots=True, frozen=True)
class ModelMappingCapability:
    """
    Runtime lookup capability for a `ModelMapping`.

    A model mapping describes how a source model maps to the canonical
    internal TWW model. This capability provides convenient accessors for
    class, attribute and value mappings.

    The mapping itself is immutable and should already be parsed or resolved
    before this capability is created.
    """
    mapping: ModelMapping


    def class_definition(
        self,
        class_id: str,
    ) -> ClassMapping:
        """
        Return the class mapping for a source-model class identifier.

        Parameters
        ----------
        class_id:
            Source-model class identifier.

        Raises
        ------
        KeyError
            If the source class is unknown in this mapping.
        """

        try:
            return self.mapping.classes[class_id]
        except KeyError as exc:
            raise KeyError(
                f"Unknown class: {class_id}"
            ) from exc

    def try_class_definition(
        self,
        class_id: str,
    ) -> ClassMapping | None:
        """
        Return a class mapping if it exists, otherwise `None`.
        """

        return self.mapping.classes.get(class_id)

    def attribute_definition(
        self,
        class_id: str,
        attribute_name: str,
    ) -> AttributeMapping:
        """
        Return the attribute mapping for a source-model attribute.

        Parameters
        ----------
        class_id:
            Source-model class identifier.

        attribute_name:
            Source-model attribute identifier.

        Raises
        ------
        KeyError
            If the class or attribute is unknown in this mapping.
        """
        cls = self.class_definition(class_id)

        try:
            return cls.attributes[attribute_name]
        except KeyError as exc:
            raise KeyError(
                f"Unknown attribute "
                f"{attribute_name!r} "
                f"for class {class_id!r}"
            ) from exc

    def try_attribute_definition(
        self,
        class_id: str,
        attribute_name: str,
    ) -> AttributeMapping | None:
        """
        Return an attribute mapping if it exists, otherwise `None`.
        """

        cls = self.mapping.classes.get(class_id)
        if cls is None:
            return None

        return cls.attributes.get(attribute_name)

    def value_mapping(
        self,
        class_id: str,
        attribute_name: str,
        value: str,
    ) -> ValueMapping:
        """
        Return the value mapping for a source-model value.

        Parameters
        ----------
        class_id:
            Source-model class identifier.

        attribute_name:
            Source-model attribute identifier.

        value:
            Source-model value.

        Raises
        ------
        KeyError
            If the class, attribute or value is unknown.
        """

        return self.attribute_definition(
            class_id,
            attribute_name,
        ).values[value]

    def try_value_mapping(
        self,
        class_id: str,
        attribute_name: str,
        value: str,
    ) -> ValueMapping | None:

        """
        Return a value mapping if it exists, otherwise `None`.
        """


        attribute = self.try_attribute_definition(
            class_id,
            attribute_name,
        )

        if attribute is None:
            return None

        return attribute.values.get(value)


class ImplicitModelMappingCapability(Protocol):
    """
    Provides source-to-canonical mappings derived implicitly from metadata.

    Implementations may use dictionary metadata, generated code, static maps,
    or another source. SQL-backed implementations belong in the plugin layer.
    """

    def class_definition(
        self,
        class_id: str,
    ) -> ClassMapping:
        ...

    def try_class_definition(
        self,
        class_id: str,
    ) -> ClassMapping | None:
        ...

    def attribute_definition(
        self,
        class_id: str,
        attribute_name: str,
    ) -> AttributeMapping:
        ...

    def try_attribute_definition(
        self,
        class_id: str,
        attribute_name: str,
    ) -> AttributeMapping | None:
        ...

    def value_mapping(
        self,
        class_id: str,
        attribute_name: str,
        value: str,
    ) -> ValueMapping:
        ...

    def try_value_mapping(
        self,
        class_id: str,
        attribute_name: str,
        value: str,
    ) -> ValueMapping | None:
        ...

@dataclass(slots=True, frozen=True)
class EffectiveModelMappingCapability:
    """
    Resolves effective source-to-canonical mappings.

    Explicit ModelMapping entries take precedence. If a class, attribute or
    value is not explicitly mapped, the implicit mapping provider is used as
    fallback.
    """

    explicit_mapping: ModelMappingCapability
    implicit_mapping: ImplicitModelMappingCapability | None = None

    def class_definition(
        self,
        class_id: str,
    ) -> ClassMapping:
        explicit = self.explicit_mapping.try_class_definition(
            class_id,
        )

        if explicit is not None:
            return explicit

        if self.implicit_mapping is None:
            return self.explicit_mapping.class_definition(
                class_id,
            )

        return self.implicit_mapping.class_definition(
            class_id,
        )

    def try_class_definition(
        self,
        class_id: str,
    ) -> ClassMapping | None:
        explicit = self.explicit_mapping.try_class_definition(
            class_id,
        )

        if explicit is not None:
            return explicit

        if self.implicit_mapping is None:
            return None

        return self.implicit_mapping.try_class_definition(
            class_id,
        )

    def attribute_definition(
        self,
        class_id: str,
        attribute_name: str,
    ) -> AttributeMapping:
        explicit = self.explicit_mapping.try_attribute_definition(
            class_id,
            attribute_name,
        )

        if explicit is not None:
            return explicit

        if self.implicit_mapping is None:
            return self.explicit_mapping.attribute_definition(
                class_id,
                attribute_name,
            )

        return self.implicit_mapping.attribute_definition(
            class_id,
            attribute_name,
        )

    def try_attribute_definition(
        self,
        class_id: str,
        attribute_name: str,
    ) -> AttributeMapping | None:
        explicit = self.explicit_mapping.try_attribute_definition(
            class_id,
            attribute_name,
        )

        if explicit is not None:
            return explicit

        if self.implicit_mapping is None:
            return None

        return self.implicit_mapping.try_attribute_definition(
            class_id,
            attribute_name,
        )

    def value_mapping(
        self,
        class_id: str,
        attribute_name: str,
        value: str,
    ) -> ValueMapping:
        explicit = self.explicit_mapping.try_value_mapping(
            class_id,
            attribute_name,
            value,
        )

        if explicit is not None:
            return explicit

        if self.implicit_mapping is None:
            return self.explicit_mapping.value_mapping(
                class_id,
                attribute_name,
                value,
            )

        return self.implicit_mapping.value_mapping(
            class_id,
            attribute_name,
            value,
        )

    def try_value_mapping(
        self,
        class_id: str,
        attribute_name: str,
        value: str,
    ) -> ValueMapping | None:
        explicit = self.explicit_mapping.try_value_mapping(
            class_id,
            attribute_name,
            value,
        )

        if explicit is not None:
            return explicit

        if self.implicit_mapping is None:
            return None

        return self.implicit_mapping.try_value_mapping(
            class_id,
            attribute_name,
            value,
        )