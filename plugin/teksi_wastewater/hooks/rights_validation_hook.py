from teksi_hooks.hook import HookBase, HookContext, HookMetadata
from .capabilities.twwcapabilities import SqlCapability
from .capabilities.validation import ValidationCapability
from .capabilities.provider import ProviderCapability


class Hook(HookBase):

    required_capabilities = frozenset(
        {
            SqlCapability,
            ProviderCapability,
            ValidationCapability,
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

        provider = context.capability(
            ProviderCapability,
        ).provider

        sql = context.capability(
            SqlCapability,
        )

        validation = context.capability(
            ValidationCapability,
        )

        
        changes = ...

        for change in changes:

            for rule in RULES:

                findings = rule.validate(
                    change,
                    provider,
                )
