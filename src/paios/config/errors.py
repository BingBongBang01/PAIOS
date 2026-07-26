"""Error types for the Configuration Manager.

Per docs/910_Phase1_Core_Foundation_Specification.md#configuration-manager.
"""

from __future__ import annotations


class ConfigurationError(Exception):
    """Raised when configuration fails schema validation or is missing a
    required key. Per 910's Error Handling for the Configuration Manager,
    this halts boot rather than allowing the system to start on
    unvalidated configuration.
    """

    def __init__(self, key: str, reason: str) -> None:
        self.key = key
        self.reason = reason
        super().__init__(f"Configuration error for key '{key}': {reason}")


class UnknownConfigKeyError(Exception):
    """Raised by ``getRequired()`` for a key not covered by the schema.

    Per 910: this is a programming error, not a runtime case to guard
    defensively against.
    """

    def __init__(self, key: str) -> None:
        self.key = key
        super().__init__(f"Unknown configuration key: '{key}'")
