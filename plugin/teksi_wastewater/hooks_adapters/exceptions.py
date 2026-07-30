from tww_hooks.exceptions import (
    ValidationError,
)
from tww_hooks.models.validation import (
    ValidationFinding,
)


class QuarantineValidationError(
    ValidationError,
):
    """
    Raised when quarantine schema validation fails.
    """

    def __init__(
        self,
        findings: tuple[
            ValidationFinding,
            ...
        ],
        log_path: str | None = None,
    ) -> None:
        self.log_path = log_path

        super().__init__(
            findings,
        )