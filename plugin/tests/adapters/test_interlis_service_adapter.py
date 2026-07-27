from teksi_wastewater.hooks_adapters.tww_interlis_service_adapter import TwwInterlisServiceAdapter

class FakeInterlisImporterExporter:
    def __init__(self):
        self.import_calls = []
        self.export_calls = []

    def interlis_import(self, **kwargs):
        self.import_calls.append(kwargs)

    def interlis_export(self, **kwargs):
        self.export_calls.append(kwargs)


def test_interlis_service_adapter_delegates_import():
    fake = FakeInterlisImporterExporter()

    adapter = TwwInterlisServiceAdapter(
        importer_exporter=fake,
    )

    adapter.import_xtf(
        xtf_file="/tmp/input.xtf",
    )

    assert fake.import_calls == [
        {
            "xtf_file": "/tmp/input.xtf",
        }
    ]