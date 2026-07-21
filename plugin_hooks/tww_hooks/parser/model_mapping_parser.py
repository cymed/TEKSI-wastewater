from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

from ..models.mapping import (
    AttributeMapping,
    ClassMapping,
    FunctionMapping,
    ModelMapping,
)


@dataclass(slots=True)
class ModelMappingParser:
    """
    Parser for source-model to canonical TWW mapping YAML files.

    The parser supports two class-level mapping modes:

    1. Function-backed class mapping
       The whole source row is projected to canonical JSONB effects by a
       database function.

    2. Attribute-backed class mapping
       Individual source attributes are mapped directly to canonical TWW
       class and attribute identifiers.

    A class mapping must not define both `function` and `attributes`.
    """

    def parse_file(
        self,
        path: str | Path,
    ) -> ModelMapping:
        with open(path, "r", encoding="utf-8") as file:
            data = yaml.safe_load(file)

        return self._parse_dict(
            data or {},
        )

    def _parse_dict(
        self,
        data: dict[str, Any],
    ) -> ModelMapping:
        return ModelMapping(
            classes=self._parse_classes(
                data.get(
                    "classes",
                    {},
                ),
            ),
            is_ssot=data.get(
                "is_ssot",
                False,
            ),
        )

    def _parse_classes(
        self,
        raw_classes: dict[str, Any],
    ) -> dict[str, ClassMapping]:
        return {
            class_id: self._parse_class(
                class_id,
                raw_class or {},
            )
            for class_id, raw_class in raw_classes.items()
        }

    def _parse_class(
        self,
        class_id: str,
        raw: dict[str, Any],
    ) -> ClassMapping:
        function = self._parse_function(
            raw.get(
                "function",
            ),
        )

        raw_attributes = raw.get(
            "attributes",
            {},
        )

        if function is not None and raw_attributes:
            raise ValueError(
                f"Class mapping {class_id!r} must not define both "
                "`function` and `attributes`. A row-level function is "
                "authoritative for the full class mapping."
            )

        return ClassMapping(
            tww_class_id=raw.get(
                "class",
            ),
            function=function,
            attributes=self._parse_attributes(
                raw_attributes,
            ),
        )

    def _parse_function(
        self,
        raw: dict[str, Any] | None,
    ) -> FunctionMapping | None:
        if raw is None:
            return None

        return FunctionMapping(
            schema=raw["schema"],
            name=raw["name"],
            parameters=raw.get(
                "parameters",
                {},
            ),
        )

    def _parse_attributes(
        self,
        raw_attributes: dict[str, Any],
    ) -> dict[str, AttributeMapping]:
        return {
            attribute_name: self._parse_attribute(
                attribute_name,
                raw_attribute or {},
            )
            for attribute_name, raw_attribute in raw_attributes.items()
        }

    def _parse_attribute(
        self,
        attribute_name: str,
        raw: dict[str, Any],
    ) -> AttributeMapping:
        targets = raw.get(
            "targets",
            [],
        )

        if not targets:
            raise ValueError(
                f"Attribute mapping {attribute_name!r} must define "
                "exactly one target."
            )

        if len(targets) != 1:
            raise ValueError(
                f"Attribute mapping {attribute_name!r} defines "
                f"{len(targets)} targets. Exactly one target is currently "
                "supported."
            )

        target = targets[0]

        return AttributeMapping(
            tww_class_id=target["class"],
            tww_attr_id=target["attribute"],
            foreign_key=target.get(
                "foreign_key",
            ),
        )