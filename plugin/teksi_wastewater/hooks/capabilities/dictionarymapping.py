from teksi_hooks.capabilities import SqlCapability
from ..models.mapping import ModelMapping

class DictionaryMappingCapability:

    def __init__(self, sql: SqlCapability):
        self.sql=sql
    
    def od_table_for_ili(
        self,
        ili_name: str,
    ) -> str:
        ...

    def od_field_for_ili(
        self,
        ili_class: str,
        ili_attribute: str,
    ) -> tuple[str, str]:
        pass

    def od_value_for_ili(
        self,
        ili_class: str,
        ili_attribute: str,
        ili_value: str,
    ) -> tuple[str, str, str]:
        pass