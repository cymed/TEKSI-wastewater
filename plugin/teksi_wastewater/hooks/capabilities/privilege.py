from dataclasses import dataclass

from ..models.provider import Provider


@dataclass(slots=True)
class ProviderCapability:
    provider: Provider