import abc
from pathlib import Path 
from dataclasses import dataclass

class InterlisService(abc.ABC):

    @abc.abstractmethod
    def import_xtf(
        self,
        xtf_file: Path,
    ) -> None:
        raise NotImplementedError

    @abc.abstractmethod
    def export_xtf(
        self,
        xtf_file: Path | None,
        export_models: list[str],
    ) -> None:
        raise NotImplementedError

    @abc.abstractmethod
    def find_models(
        self,
        xtf_file: Path,
    ) -> list:
        raise NotImplementedError



@dataclass(slots=True)
class InterlisCapability:
    service: InterlisService
