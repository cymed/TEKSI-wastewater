from teksi_hooks.capabilities import SqlCapability
from ..models.validation import Change
from ..models.mapping import RelationContext, AttributeMapping, ClassMapping, ValueMapping, ModelMapping

from ..capabilities.mapping import DictionaryMappingCapability, ModelMappingCapability


from teksi_hooks.capabilities import SqlCapability

from ..models.validation import Change
from ..models.mapping import RelationContext
from .relation_context_provider import RelationContextProvider


class ChangeLoader:
    def __init__(
        self,
        sql: SqlCapability,
        relation_context_provider: RelationContextProvider,
    ):
        self.sql = sql
        self.relation_context_provider = relation_context_provider

    def load(
        self,
    ) -> tuple[Change, ...]:
        changes: list[Change] = []

        for context in self.relation_context_provider.relation_contexts():
            changes.extend(self._load_inserts(context))
            changes.extend(self._load_updates(context))
            changes.extend(self._load_deletes(context))

        return tuple(changes)

    def _load_inserts(
        self,
        context: RelationContext,
    ) -> tuple[Change, ...]:
        raise NotImplementedError

    def _load_updates(
        self,
        context: RelationContext,
    ) -> tuple[Change, ...]:
        raise NotImplementedError

    def _load_deletes(
        self,
        context: RelationContext,
    ) -> tuple[Change, ...]:
        raise NotImplementedError
