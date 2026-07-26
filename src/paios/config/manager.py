"""Configuration Manager implementation.

Per docs/910_Phase1_Core_Foundation_Specification.md#configuration-manager:
the sole path by which any module reads configuration. Configuration is
loaded once, merging defaults, a file source, and environment variables
in precedence order `defaults < file < environment` (910's Phase 1
Resolution), validated against a caller-supplied schema, and exposed
read-only thereafter.

This module implements the Configuration Manager mechanism itself. It
does not define the schema for any specific Phase 1 component
(`kernel.bootTimeoutMs`, `storage.local.path`, etc.) — those keys are
registered by the work packages that own them, against the schema they
pass to their own `ConfigurationManager` instance.

Two Phase 1 load conventions are fixed here, per 910: the default
configuration file name is `paios.config.json`, and environment variables
are read with a `PAIOS_` prefix. A dotted schema key (e.g.
`storage.local.path`) maps to the environment variable name
`PAIOS_STORAGE__LOCAL__PATH` (dots become double underscores, the whole
name is upper-cased). The file source, when present, is a flat JSON
object whose top-level keys are the same dotted schema key strings.
"""

from __future__ import annotations

import json
import os
from collections.abc import Mapping
from pathlib import Path
from typing import Any, TypeVar

from paios.config.errors import ConfigurationError, UnknownConfigKeyError
from paios.config.schema import ConfigSchema

DEFAULT_CONFIG_FILE_NAME = "paios.config.json"
ENV_VAR_PREFIX = "PAIOS_"

T = TypeVar("T")

_CASTABLE_TYPES = (str, int, float, bool)


def env_var_name(key: str) -> str:
    """Return the environment variable name for a dotted schema key."""
    return ENV_VAR_PREFIX + key.upper().replace(".", "__")


def _cast_env_value(key: str, raw: str, value_type: type) -> Any:
    if value_type is bool:
        normalized = raw.strip().lower()
        if normalized in ("true", "1", "yes"):
            return True
        if normalized in ("false", "0", "no"):
            return False
        raise ConfigurationError(key, f"cannot interpret '{raw}' as a boolean")
    if value_type is int:
        try:
            return int(raw)
        except ValueError as exc:
            raise ConfigurationError(key, f"cannot interpret '{raw}' as an integer") from exc
    if value_type is float:
        try:
            return float(raw)
        except ValueError as exc:
            raise ConfigurationError(key, f"cannot interpret '{raw}' as a float") from exc
    return raw


def _validate_type(key: str, value: Any, value_type: type) -> None:
    if value_type is float and isinstance(value, int) and not isinstance(value, bool):
        return
    if not isinstance(value, value_type):
        raise ConfigurationError(
            key,
            f"expected type '{value_type.__name__}', got '{type(value).__name__}'",
        )


class ConfigurationManager:
    """Loads, validates, and exposes configuration for a declared schema."""

    def __init__(self, schema: ConfigSchema) -> None:
        for key, key_schema in schema.items():
            if key_schema.value_type not in _CASTABLE_TYPES:
                raise ValueError(
                    f"Unsupported schema value_type for key '{key}': {key_schema.value_type!r}"
                )
        self._schema = dict(schema)
        self._values: dict[str, Any] = {}
        self._loaded = False

    def load(
        self,
        *,
        file_path: str | Path | None = None,
        env: Mapping[str, str] | None = None,
    ) -> None:
        """Load configuration once from defaults, an optional file, and
        environment variables, validating the merged result against the
        schema. Raises `ConfigurationError` and leaves the manager
        unloaded if validation fails, per 910's Boot Lifecycle rule that
        no service starts on unvalidated configuration.
        """
        file_values = self._read_file(file_path)
        env_source = os.environ if env is None else env

        merged: dict[str, Any] = {}
        for key, key_schema in self._schema.items():
            env_name = env_var_name(key)
            if env_name in env_source:
                merged[key] = _cast_env_value(key, env_source[env_name], key_schema.value_type)
            elif key in file_values:
                value = file_values[key]
                _validate_type(key, value, key_schema.value_type)
                merged[key] = value
            elif not key_schema.required:
                merged[key] = key_schema.default
            else:
                raise ConfigurationError(key, "required key missing from all configuration sources")

        self._values = merged
        self._loaded = True

    def _read_file(self, file_path: str | Path | None) -> dict[str, Any]:
        if file_path is None:
            return {}
        path = Path(file_path)
        if not path.is_file():
            raise ConfigurationError(str(path), "configuration file not found")
        try:
            content = json.loads(path.read_text())
        except json.JSONDecodeError as exc:
            raise ConfigurationError(str(path), f"invalid JSON: {exc}") from exc
        if not isinstance(content, dict):
            raise ConfigurationError(str(path), "configuration file must contain a JSON object")
        return content

    def get(self, key: str, default_value: T | None = None) -> T | None:
        """Return the loaded value for `key`, or `default_value` if the
        manager has not been loaded, or the schema-declared default if
        `key` was absent from every source. Unlike `getRequired`, an
        unknown key raises `UnknownConfigKeyError` rather than silently
        returning `default_value`, since a key outside the schema was
        never validated and reading it is a programming error, per 910.
        """
        if key not in self._schema:
            raise UnknownConfigKeyError(key)
        if not self._loaded:
            return default_value
        return self._values.get(key, default_value)

    def get_required(self, key: str) -> Any:
        """Return the loaded value for `key`. Raises `UnknownConfigKeyError`
        for a key not covered by the schema, and `ConfigurationError` if
        the manager has not yet been loaded, per 910's Error Handling.
        """
        if key not in self._schema:
            raise UnknownConfigKeyError(key)
        if not self._loaded:
            raise ConfigurationError(key, "configuration has not been loaded yet")
        return self._values[key]

    def is_loaded(self) -> bool:
        """Return whether `load()` has completed successfully."""
        return self._loaded
