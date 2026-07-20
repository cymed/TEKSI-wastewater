from teksi_hooks.hook import HookBase, HookContext, HookMetadata
from teksi_hooks.capabilities import SqlCapability
from .capabilities.validation import ValidationResult
from .capabilities.privilege import ResolvedProviderCapability
from .capabilities.rights import RightsCapability
from .capabilities.mapping import ModelMappingCapability


class Hook(HookBase):

    required_capabilities = frozenset(
        {
            SqlCapability,
            ResolvedProviderCapability,
            ValidationResult,
            ModelMappingCapability
        }
    )

    @property
    def metadata(
        self,
    ) -> HookMetadata:
        return HookMetadata(
            name="Rights Validation",
            description=(
                "Validates whether the provider is "
                "allowed to modify submitted objects."
            ),
        )

    def run_hook(
        self,
        context: HookContext,
    ) -> None:


        rights = context.capability(
            RightsCapability,
        )

        provider = context.capability(
            ResolvedProviderCapability,
        )

        validation = context.capability(
            ValidationResult,
        )

        mapping = context.capability(
            ModelMappingCapability,
        )

        changes = self._load_changes(sql)


        for change in changes:
            for attribute_change in change.changed_attributes:
                self._validate_change(
                    change=change,
                    rights=rights,
                    provider=provider,
                    mapping=mapping,
                    validation=validation,
                )

