from __future__ import annotations

from dataclasses import dataclass

from ..models.effects import (
    EffectDocument,
    UpdateAttributeEffect,
    EnforceExistsEffect,
    EnforceNotExistsEffect,
)


@dataclass(slots=True)
class EffectDocumentValidator:
    """
    Validates EffectDocument instances.

    The validator performs structural and semantic checks before effects are
    persisted or transformed into snapshots.
    """

    def validate(
        self,
        document: EffectDocument,
    ) -> tuple[str, ...]:
        findings: list[str] = []

        if document.version != 1:
            findings.append(
                f"Unsupported effect document version: "
                f"{document.version}"
            )

        for effect in document.effects:
            if not effect.identity.class_id:
                findings.append(
                    "Effect identity is missing class_id."
                )

            if not effect.identity.attributes:
                findings.append(
                    "Effect identity is missing identity "
                    "attributes."
                )

            if isinstance(
                effect,
                UpdateAttributeEffect,
            ):
                if not effect.tww_attribute_id:
                    findings.append(
                        "Update effect missing "
                        "tww_attribute_id."
                    )

            elif isinstance(
                effect,
                (
                    EnforceExistsEffect,
                    EnforceNotExistsEffect,
                ),
            ):
                pass

            else:
                findings.append(
                    f"Unsupported effect type: "
                    f"{type(effect).__name__}"
                )

        return tuple(
            findings,
        )