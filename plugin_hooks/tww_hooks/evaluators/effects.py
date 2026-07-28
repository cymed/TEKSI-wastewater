from __future__ import annotations

from dataclasses import dataclass
from collections import defaultdict

from ..models.effects import (
    Effect,
    EffectDocument,
    UpdateAttributeEffect,
    EnforceExistsEffect,
    EnforceNotExistsEffect,
)
from ..models.validation import ValidationFinding
from ..models.canonical_object import (
    CanonicalObjectIdentity,
)

from ..exceptions import EffectValidationError, Severity

DOCUMENT_MAX_VERSION = 1

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
    ) -> tuple[ValidationFinding, ...]:
        findings: list[ValidationFinding] = []

        if document.version > DOCUMENT_MAX_VERSION:
                findings.append(
                    ValidationFinding(
                    code="invalid_version",
                    severity=Severity.ERROR,
                    message=(
                        f"Unsupported effect document version: "
                        f"{document.version}"
                    ),
                )
                )

        for effect in document.effects:
            if not effect.identity.class_id:
                findings.append(
                    ValidationFinding(
                    code="missing_attribute",
                    severity=Severity.ERROR,
                    message=(
                        "Effect identity is missing class_id "
                    ),
                )
                )

            if not effect.identity.attributes:
                findings.append(
                    ValidationFinding(
                    code="missing_attribute",
                    severity=Severity.ERROR,
                    message=(
                        "Effect identity is missing identity "
                        "attributes."
                    ),
                )
                )

            if isinstance(
                effect,
                UpdateAttributeEffect,
            ):
                if not effect.tww_attribute_id:
                    findings.append(
                        ValidationFinding(
                        code="missing_attribute",
                        severity=Severity.ERROR,
                        message=(
                            "Update effect missing "
                            "tww_attribute_id."
                        ),
                    )
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
                    ValidationFinding(
                        code="unsupported_effect",
                        severity=Severity.ERROR,
                        message=(
                            f"Unsupported effect type: "
                            f"{type(effect).__name__}"
                        ),
                    )

                )

        findings.extend(
            self._validate_conflicting_effects(
                document,
            )
        )
        return tuple(
            findings,
        )

    def validate_or_raise(
        self,
        document: EffectDocument,
    ) -> tuple[ValidationFinding, ...]:
        findings=self.validate(document)
        EffectValidationError.raise_if_errors(findings,)
        return findings

    def _identity_key(
        self,
        identity: CanonicalObjectIdentity,
    ) -> tuple:
        return (
            identity.class_id,
            tuple(
                sorted(
                    identity.attributes.items(),
                ),
            ),
        )
    
    def _validate_conflicting_effects(
        self,
        document: EffectDocument,
    ) -> tuple[ValidationFinding, ...]:
        findings: list[ValidationFinding] = []

        effects_by_identity: dict[
            str,
            list[Effect],
        ] = defaultdict(
            list,
        )

        for effect in document.effects:
            effects_by_identity[
                self._identity_key(
                    effect.identity,
                )
            ].append(effect)

        for identity, effects in effects_by_identity.items():
            has_update = any(
                isinstance(
                    effect,
                    UpdateAttributeEffect,
                )
                for effect in effects
            )

            has_exists = any(
                isinstance(
                    effect,
                    EnforceExistsEffect,
                )
                for effect in effects
            )

            has_not_exists = any(
                isinstance(
                    effect,
                    EnforceNotExistsEffect,
                )
                for effect in effects
            )

            if has_exists and has_not_exists:
                findings.append(
                    ValidationFinding(
                        code="contradicting_effects",
                        attribute_name=None,
                        severity=Severity.ERROR,
                        message=(
                            "Object cannot be required to "
                            "exist and to not exist at the "
                            "same time."
                        ),
                    )
                )

            if has_update and has_not_exists:
                findings.append(
                    ValidationFinding(
                        code="contradicting_effects",
                        attribute_name=None,
                        severity=Severity.ERROR,
                        message=(
                            "Object cannot be updated and "
                            "required to not exist at the "
                            "same time."
                        ),
                    )
                )

        return tuple(
            findings,
        )