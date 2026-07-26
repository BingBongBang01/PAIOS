"""Configuration schema declaration for the Configuration Manager.

A schema is the set of keys a Configuration Manager instance validates
its merged, loaded configuration against, per
docs/910_Phase1_Core_Foundation_Specification.md#configuration-manager.
WP-02 implements the schema mechanism itself; individual Phase 1
components register their own keys against it in their own work
packages (e.g. `kernel.bootTimeoutMs`, `storage.local.path`), not here.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class ConfigKeySchema:
    """The declared shape of a single configuration key.

    - `value_type`: the Python type the merged value must be an instance
      of (`str`, `int`, `float`, or `bool`).
    - `required`: if True, the key must be present after merging
      defaults, file, and environment sources; a required key missing
      after merge halts loading with `ConfigurationError`.
    - `default`: the value used when the key is not required and not
      supplied by any source. Ignored when `required` is True.
    """

    value_type: type
    required: bool = False
    default: Any = None


ConfigSchema = dict[str, ConfigKeySchema]
