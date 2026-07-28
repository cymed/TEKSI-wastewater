from dataclasses import dataclass

from ..capabilities.rights import RightsCapability
from ..models.validation import (
    ValidationFinding,
)


@dataclass(slots=True)
class ValidationEvaluator:
    """
    Evaluates configured attribute and transition validations.
    """

    rights: RightsCapability

    def validate_attribute(
        self,
        *,
        class_id: str,
        attribute_name: str,
        value,
    ) -> tuple[
        ValidationFinding,
        ...
    ]:
        raise NotImplementedError

    def validate_transition(
        self,
        *,
        class_id: str,
        attribute_name: str,
        old_value,
        new_value,
    ) -> tuple[
        ValidationFinding,
        ...
    ]:
        raise NotImplementedError