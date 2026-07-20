from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

from teksi_hooks.ili_definitions import Standardoid

from ..models.privilege import Privilege
from ..models.provider import (
    Provider,
    ProviderPermission,
)


@dataclass(slots=True)
class ProviderRightsParser:
    """
    Parser for provider privilege assignment YAML files.

    The parser converts YAML provider definitions into parsed Provider objects.
    It does not merge duplicate data-owner permissions. Merging belongs to the
    ProviderResolver.
    """

    def parse_file(
        self,
        path: str | Path,
    ) -> tuple[Provider, ...]:
        with open(path, "r", encoding="utf-8") as file:
            data = yaml.safe_load(file)

        return self._parse_dict(
            data or {},
        )

    def _parse_dict(
        self,
        data: dict[str, Any],
    ) -> tuple[Provider, ...]:
        return tuple(
            self._parse_provider(raw_provider)
            for raw_provider in data.get(
                "providers",
                [],
            )
        )

    def _parse_provider(
        self,
        raw: dict[str, Any],
    ) -> Provider:
        return Provider(
            name=raw["name"],
            organisation_oid=Standardoid(
                raw["organisation_oid"],
            ),
            permissions=frozenset(
                self._parse_permission(raw_permission)
                for raw_permission in raw.get(
                    "permissions",
                    [],
                )
            ),
        )

    def _parse_permission(
        self,
        raw: dict[str, Any],
    ) -> ProviderPermission:
        return ProviderPermission(
            dataowner_oid=Standardoid(
                raw["dataowner_oid"],
            ),
            privileges=self._parse_privileges(
                raw.get("privileges") or [],
            ),
        )

    def _parse_privileges(
        self,
        raw: list[str],
    ) -> frozenset:
        return frozenset(
            Privilege(value)
            for value in raw
        )