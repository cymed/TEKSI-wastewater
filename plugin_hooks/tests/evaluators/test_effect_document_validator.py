from tww_hooks.evaluators.effects import (
    EffectDocumentValidator,
)
from tww_hooks.models.canonical_object import (
    CanonicalObjectIdentity,
)
from tww_hooks.models.effects import (
    EffectDocument,
    EffectSource,
    UpdateAttributeEffect,
)


def test_validator_accepts_valid_document() -> None:
    validator = EffectDocumentValidator()

    findings = validator.validate(
        EffectDocument(
            source=EffectSource(
                model="ag64",
                class_id="GepKnoten",
                object_id="ch123456AG987654",
            ),
            effects=(
                UpdateAttributeEffect(
                    identity=CanonicalObjectIdentity(
                        class_id="agxx_wastewater_node",
                        attributes={
                            "fk_wastewater_node":
                                "ch123456AG987654",
                        },
                    ),
                    tww_attribute_id="ag64_function",
                    value=1234,
                ),
            ),
        )
    )

    assert findings == ()

def test_validator_rejects_unknown_version() -> None:
    validator = EffectDocumentValidator()

    findings = validator.validate(
        EffectDocument(
            version=999,
            source=EffectSource(
                model="ag64",
                class_id="GepKnoten",
                object_id="ch123456AG987654",
            ),
            effects=(),
        )
    )

    assert len(findings) == 1

    assert (
        "Unsupported effect document version"
        in findings[0].message
    )

def test_validator_rejects_missing_identity_attributes() -> None:
    validator = EffectDocumentValidator()

    findings = validator.validate(
        EffectDocument(
            source=EffectSource(
                model="ag64",
                class_id="GepKnoten",
                object_id="ch123456AG987654",
            ),
            effects=(
                UpdateAttributeEffect(
                    identity=CanonicalObjectIdentity(
                        class_id="agxx_wastewater_node",
                        attributes={},
                    ),
                    tww_attribute_id="ag64_function",
                    value=1234,
                ),
            ),
        )
    )

    assert len(findings) == 1

    assert (
        "Effect identity is missing identity attributes."
        in findings[0].message
    )

def test_validator_rejects_missing_attribute_id() -> None:
    validator = EffectDocumentValidator()

    findings = validator.validate(
        EffectDocument(
            source=EffectSource(
                model="ag64",
                class_id="GepKnoten",
                object_id="ch123456AG987654",
            ),
            effects=(
                UpdateAttributeEffect(
                    identity=CanonicalObjectIdentity(
                        class_id="agxx_wastewater_node",
                        attributes={
                            "fk_wastewater_node":
                                "ch123456AG987654",
                        },
                    ),
                    tww_attribute_id="",
                    value=1234,
                ),
            ),
        )
    )

    assert len(findings) == 1

    assert (
        "Update effect missing tww_attribute_id."
        in findings[0].message
    )

def test_validator_rejects_missing_identity_class() -> None:
    validator = EffectDocumentValidator()

    findings = validator.validate(
        EffectDocument(
            source=EffectSource(
                model="ag64",
                class_id="GepKnoten",
                object_id="ch123456AG987654",
            ),
            effects=(
                UpdateAttributeEffect(
                    identity=CanonicalObjectIdentity(
                        class_id="",
                        attributes={
                            "fk_wastewater_node":
                                "ch123456AG987654",
                        },
                    ),
                    tww_attribute_id="ag64_function",
                    value=1234,
                ),
            ),
        )
    )

    assert len(findings) == 1

    assert (
        "Effect identity is missing class_id."
        in findings[0].message
    )