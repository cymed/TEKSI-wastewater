from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import json

from ..models.effects import (
    EffectDocument,
    EffectSource,
    Effect,
    UpdateAttributeEffect,
    EnforceExistsEffect,
    EnforceNotExistsEffect,
)


@dataclass(slots=True)
class EffectParser:
    """
    Parser for JSONB effect documents.

    Converts JSON effect documents into strongly typed effect models.
    """

    SUPPORTED_VERSION = 1

    def parse_file(
        self,
        path: str | Path,
    ) -> EffectDocument:
        with open(path, "r", encoding="utf-8") as file:
            data = json.load(file)

        return self._parse_dict(
            data,
        )

    def parse_json(
        self,
        document: str,
    ) -> EffectDocument:
        return self._parse_dict(
            json.loads(document),
        )

    def _parse_dict(
        self,
        data: dict[str, Any],
    ) -> EffectDocument:
        version = data.get(
            "version",
        )

        if version != self.SUPPORTED_VERSION:
            raise ValueError(
                f"Unsupported effect document version: {version!r}"
            )

        return EffectDocument(
            version=version,
            source=self._parse_source(
                data["source"],
            ),
            effects=tuple(
                self._parse_effect(
                    effect,
                )
                for effect in data.get(
                    "effects",
                    [],
                )
            ),
        )

    def _parse_source(
        self,
        data: dict[str, Any],
    ) -> EffectSource:
        return EffectSource(
            model=data["model"],
            class_id=data["class"],
            object_id=data["object_id"],
        )

    def _parse_effect(
        self,
        data: dict[str, Any],
    ) -> Effect:
        kind = data["kind"]

        if kind == "update_attribute":
            return UpdateAttributeEffect(
                tww_class_id=data["tww_class_id"],
                tww_identity=data["tww_identity"],
                tww_attribute_id=data["tww_attribute_id"],
                value=data.get("value"),
            )

        if kind == "enforce_exists":
            return EnforceExistsEffect(
                tww_class_id=data["tww_class_id"],
                tww_identity=data["tww_identity"],
            )

        if kind == "enforce_not_exists":
            return EnforceNotExistsEffect(
                tww_class_id=data["tww_class_id"],
                tww_identity=data["tww_identity"],
            )

        raise ValueError(
            f"Unsupported effect kind: {kind!r}"
        )