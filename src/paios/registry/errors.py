"""Error types for the Service Registry.

Per docs/910_Phase1_Core_Foundation_Specification.md#service-registry.
"""

from __future__ import annotations


class UnregisteredServiceError(Exception):
    """Raised by `resolve()` for a token with no registered factory.

    Per 910: this is a programming error, not a handled runtime case —
    every token a component resolves must have been registered first.
    """

    def __init__(self, token_name: str) -> None:
        self.token_name = token_name
        super().__init__(f"No implementation registered for service token '{token_name}'")


class DuplicateRegistrationError(Exception):
    """Raised by `register()` when a token is registered more than once.

    Per 910: Phase 1 has no override/replace semantics — each token has
    exactly one registered implementation.
    """

    def __init__(self, token_name: str) -> None:
        self.token_name = token_name
        super().__init__(f"Service token '{token_name}' is already registered")
