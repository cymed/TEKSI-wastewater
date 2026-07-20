from teksi_hooks.hook import HookBase, HookContext, HookMetadata
from .services.twwinterlisservice import TWWInterlisService
from .services.interlis import InterlisCapability

class Hook(HookBase):


    required_capabilities = frozenset(
        {
            InterlisCapability,
        }
    )

    @property
    def metadata(self) -> HookMetadata:
        return HookMetadata(
            name="Import Export Diff",
            description=(
                "Imports an XTF into quarantine and exports the resulting "
                "dataset for diff visualisation."
            ),
        )

    def run_hook(
        self,
        context: HookContext,
    ) -> None:
        xtf_input = context.parameters["xtf_input"]

        importer = TWWInterlisService(
            to_quarantine_only=True,
        )

        export_models=importer.find_models(
            xtf_input,
        )

        importer.import_xtf(
            xtf_file_input=xtf_input,
        )

        exporter = TWWInterlisService(
            to_quarantine_only=True,
        )
        exporter.export_xtf(
            xtf_file_output=None,
            export_models=export_models,
        )

        