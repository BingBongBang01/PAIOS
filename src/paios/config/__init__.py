"""Configuration Manager (WP-02).

Public interface for docs/910_Phase1_Core_Foundation_Specification.md#configuration-manager.
Not wired into the Kernel; that is a later work package, per
docs/920_Phase1_Work_Breakdown.md#wp-07--kernel-boot-and-shutdown-orchestration.
"""

from paios.config.errors import ConfigurationError, UnknownConfigKeyError
from paios.config.manager import (
    DEFAULT_CONFIG_FILE_NAME,
    ENV_VAR_PREFIX,
    ConfigurationManager,
    env_var_name,
)
from paios.config.schema import ConfigKeySchema, ConfigSchema

__all__ = [
    "ConfigurationManager",
    "ConfigurationError",
    "UnknownConfigKeyError",
    "ConfigKeySchema",
    "ConfigSchema",
    "DEFAULT_CONFIG_FILE_NAME",
    "ENV_VAR_PREFIX",
    "env_var_name",
]
