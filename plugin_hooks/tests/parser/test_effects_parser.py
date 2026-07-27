from tww_hooks.models.effects import (
    UpdateAttributeEffect,
    EnforceExistsEffect,
    EnforceNotExistsEffect,
)
from tww_hooks.parser.effectparser import EffectParser


def test_parse_update_attribute_effect() -> None:
    parser = EffectParser()

    document = parser.parse_json(
        """
        {
          "version": 1,
          "source": {
            "model": "agxx",
            "class": "GepKnoten",
            "object_id": "ch123456AG987654"
          },
          "effects": [
            {
              "kind": "update_attribute",
              "tww_class_id": "agxx_wastewater_node",
              "tww_identity": {
                "fk_wastewater_node": "ch123456AG987654"
              },
              "tww_attribute_id": "ag64_function",
              "value": 1234
            }
          ]
        }
        """
    )

    assert document.version == 1
    assert document.source.model == "agxx"
    assert document.source.class_id == "GepKnoten"
    assert len(document.effects) == 1

    effect = document.effects[0]

    assert isinstance(
        effect,
        UpdateAttributeEffect,
    )

    assert effect.tww_class_id == "agxx_wastewater_node"
    assert effect.tww_attribute_id == "ag64_function"
    assert effect.value == 1234


def test_parse_enforce_exists_effect() -> None:
    parser = EffectParser()

    document = parser.parse_json(
        """
        {
          "version": 1,
          "source": {
            "model": "agxx",
            "class": "GepKnoten",
            "object_id": "ch123456AG987654"
          },
          "effects": [
            {
              "kind": "enforce_exists",
              "tww_class_id": "agxx_wastewater_node",
              "tww_identity": {
                "fk_wastewater_node": "ch123456AG987654"
              }
            }
          ]
        }
        """
    )

    effect = document.effects[0]

    assert isinstance(
        effect,
        EnforceExistsEffect,
    )

    assert effect.tww_class_id == "agxx_wastewater_node"
    assert effect.tww_identity == {
        "fk_wastewater_node": "ch123456AG987654",
    }


def test_parse_enforce_not_exists_effect() -> None:
    parser = EffectParser()

    document = parser.parse_json(
        """
        {
          "version": 1,
          "source": {
            "model": "agxx",
            "class": "GepKnoten",
            "object_id": "ch123456AG987654"
          },
          "effects": [
            {
              "kind": "enforce_not_exists",
              "tww_class_id": "agxx_wastewater_node",
              "tww_identity": {
                "fk_wastewater_node": "ch123456AG987654"
              }
            }
          ]
        }
        """
    )

    effect = document.effects[0]

    assert isinstance(
        effect,
        EnforceNotExistsEffect,
    )

    assert effect.tww_class_id == "agxx_wastewater_node"


def test_reject_unknown_effect_kind() -> None:
    parser = EffectParser()

    try:
        parser.parse_json(
            """
            {
              "version": 1,
              "source": {
                "model": "agxx",
                "class": "GepKnoten",
                "object_id": "ch123456AG987654"
              },
              "effects": [
                {
                  "kind": "explode_database"
                }
              ]
            }
            """
        )
    except ValueError as exc:
        assert "Unsupported effect kind" in str(
            exc,
        )
    else:
        raise AssertionError(
            "Expected ValueError"
        )


def test_reject_unsupported_version() -> None:
    parser = EffectParser()

    try:
        parser.parse_json(
            """
            {
              "version": 99,
              "source": {
                "model": "agxx",
                "class": "GepKnoten",
                "object_id": "ch123456AG987654"
              },
              "effects": []
            }
            """
        )
    except ValueError as exc:
        assert "Unsupported effect document version" in str(
            exc,
        )
    else:
        raise AssertionError(
            "Expected ValueError"
        )


def test_parse_multiple_effects() -> None:
    parser = EffectParser()

    document = parser.parse_json(
        """
        {
          "version": 1,
          "source": {
            "model": "agxx",
            "class": "GepKnoten",
            "object_id": "ch123456AG987654"
          },
          "effects": [
            {
              "kind": "enforce_exists",
              "tww_class_id": "agxx_wastewater_node",
              "tww_identity": {
                "fk_wastewater_node": "ch123456AG987654"
              }
            },
            {
              "kind": "update_attribute",
              "tww_class_id": "agxx_wastewater_node",
              "tww_identity": {
                "fk_wastewater_node": "ch123456AG987654"
              },
              "tww_attribute_id": "ag64_function",
              "value": 1234
            }
          ]
        }
        """
    )

    assert len(
        document.effects,
    ) == 2

    assert isinstance(
        document.effects[0],
        EnforceExistsEffect,
    )

    assert isinstance(
        document.effects[1],
        UpdateAttributeEffect,
    )