import logging
import os
import re
import sys
import inspect
import time
import abc
from pathlib import Path
import dataclasses
import importlib.util
import uuid

from typing import Any, TypeVar
from .exceptions import TeksiHookError


T = TypeVar("T")
logger = logging.getLogger(__name__)


class HookBase(abc.ABC):
    required_capabilities: frozenset[type[Any]] = frozenset()
    @abc.abstractmethod
    def run_hook(self, context: HookContext) -> None:
        """
        Creates a hook that allows to run python and sql files before or after importing or exporting files.
        :param context: context to bind to the hook statement
        """
        raise NotImplementedError("The run_hook method must be implemented in the subclass.")
        
    @property
    @abc.abstractmethod
    def metadata(self) -> HookMetadata:
        raise NotImplementedError("The HookMetadata must be implemented in the subclass.")

@dataclasses.dataclass(slots=True, frozen=True)
class HookMetadata:
    name: str
    description: str

@dataclasses.dataclass(slots=True)
class HookContext:
    parameters: dict[str, Any]
    logger: logging.Logger

    capabilities: dict[type, Any]

    
    def capability(
        self,
        capability_type: type[T],
    ) -> T:
        return self.capabilities[capability_type]

class HookHandler:
    """Load, validate and execute a hook."""

    def __init__(
        self,
        *,
        file: str | Path,
        base_path: Path | None = None,
    ) -> None:
        self.base_path = base_path

        self.file = Path(file)
        if not self.file.is_absolute():
            if base_path is None:
                raise ValueError(
                    "Base path must be provided for relative hook paths."
                )
            self.file = (base_path / self.file).resolve()

        self._module = None
        self._hook_class: type[HookBase] | None = None
        self._hook_instance: HookBase | None = None
        self._sys_path_additions: list[str] = []

    @property
    def hook(self) -> HookBase:
        if self._hook_instance is None:
            raise TeksiHookError("Hook has not been loaded.")
        return self._hook_instance

    def run(
        self,
        context: HookContext,
    ) -> None:
        try:
            self._load()

            self._validate_context(
                context,
            )
            started = time.monotonic()
            try:
                logger.info(
                    "Executing hook '%s'.",
                    self.hook.metadata.name,
                )
                try:
                    self.hook.run_hook(context)
                except Exception as exc:
                    raise TeksiHookError(
                        f"Execution of hook '{self.file}' failed."
                    ) from exc
            finally:
                duration = (
                    time.monotonic()
                    - started
                )
                logger.info(
                    "Hook '%s' finished in %.3f s.",
                    self.hook.metadata.name,
                    duration,
                )
        finally:
            self._unload()

    def _load(self) -> None:
        """Load and validate the hook."""

        self._validate_file()

        parent_dir = str(self.file.parent.resolve())
        self._sys_path_additions.append(parent_dir)

        if self.base_path is not None:
            base_path_str = str(self.base_path.resolve())

            if base_path_str != parent_dir:
                self._sys_path_additions.append(base_path_str)

        for path in reversed(self._sys_path_additions):
            sys.path.insert(0, path)

        importlib.invalidate_caches()

        try:
            module_name = (
                f"tww_hook_{self.file.stem}_"
                f"{uuid.uuid4().hex}"
            )

            spec = importlib.util.spec_from_file_location(
                self.file.stem,
                self.file,
                submodule_search_locations=[parent_dir],
            )

            if spec is None or spec.loader is None:
                raise TeksiHookError(
                    f"Unable to create module specification for '{self.file}'."
                )

            module = importlib.util.module_from_spec(spec)
            module.__path__ = [parent_dir]

            sys.modules[module_name] = module

            spec.loader.exec_module(module)

            hook_class = getattr(module, "Hook", None)

            if hook_class is None or not inspect.isclass(hook_class):
                raise TeksiHookError(
                    f"Hook file '{self.file}' must define a class named 'Hook'."
                )

            if not issubclass(hook_class, HookBase):
                raise TeksiHookError(
                    f"Class 'Hook' in '{self.file}' must inherit from HookBase."
                )

            self._validate_run_hook_signature(hook_class)

            self._hook_class = hook_class
            self._hook_instance = hook_class()

            self._validate_metadata()
            self._validate_required_capabilities()

            self._module = module

        except Exception:
            self._cleanup_sys_path()
            raise

    def _unload(self) -> None:
        """Unload hook resources."""

        self._cleanup_sys_path()

        if self._module is not None:
            sys.modules.pop(self._module.__name__, None)

        self._module = None
        self._hook_class = None
        self._hook_instance = None

    def validate(self) -> None:
        try:
            self._load()
        finally:
            self._unload()

    def _validate_file(self) -> None:
        """Validate hook file."""

        if not self.file.exists():
            raise TeksiHookError(
                f"Hook file '{self.file}' does not exist."
            )

        if not self.file.is_file():
            raise TeksiHookError(
                f"Hook file '{self.file}' is not a file."
            )

        if self.file.suffix.lower() != ".py":
            raise TeksiHookError(
                f"Unsupported hook file type '{self.file.suffix}'."
            )

        if self.base_path is not None:
            try:
                self.file.relative_to(self.base_path.resolve())
            except ValueError as exc:
                raise TeksiHookError(
                    f"Hook file '{self.file}' is outside base path "
                    f"'{self.base_path}'."
                ) from exc

    def _validate_context(
        self,
        context: HookContext,
    ) -> None:
        """Validate that all required capabilities are available."""

        for capability in self.hook.required_capabilities:
            if getattr(context, capability, None) is None:
                raise TeksiHookError(
                    f"Required capability '{capability}' is missing."
                )

    def _cleanup_sys_path(self) -> None:
        """Remove temporary sys.path additions."""

        for path in self._sys_path_additions:
            try:
                sys.path.remove(path)
            except ValueError:
                pass

        self._sys_path_additions.clear()

    def _validate_run_hook_signature(
        self,
        hook_class: type[HookBase],
    ) -> None:
        signature = inspect.signature(
            hook_class.run_hook,
        )

        parameters = list(
            signature.parameters.values(),
        )

        if parameters[0].name != "self" or parameters[1].name != "context" or len(parameters) != 2:
            raise TeksiHookError(
                "run_hook(self, context) expected."
            )

    def _validate_metadata(self) -> None:
        metadata = self.hook.metadata

        if not isinstance(metadata, HookMetadata):
            raise TeksiHookError(
                "metadata must return a HookMetadata instance."
            )

        if not metadata.name.strip():
            raise TeksiHookError(
                "Hook metadata name must not be empty."
            )

        if not metadata.description.strip():
            raise TeksiHookError(
                "Hook metadata description must not be empty."
            )

    def _validate_required_capabilities(self) -> None:
        capabilities = self.hook.required_capabilities

        if not isinstance(capabilities, frozenset):
            raise TeksiHookError(
                "required_capabilities must be a frozenset."
            )

        valid_capabilities = {
            field.name
            for field in dataclasses.fields(HookContext)
            if field.name not in {"parameters", "logger"}
        }

        invalid_capabilities = (
            capabilities - valid_capabilities
        )

        if invalid_capabilities:
            raise TeksiHookError(
                "Unknown capabilities declared by hook: "
                f"{', '.join(sorted(invalid_capabilities))}"
            )
  

