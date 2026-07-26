"""Service Registry implementation (WP-03).

Per docs/910_Phase1_Core_Foundation_Specification.md#service-registry: the
sole mechanism by which any component obtains an implementation of a
dependency, resolved against a `ServiceToken`, never a concrete type
directly. Phase 1 supports exactly one registered implementation per
token (single binding) with singleton lifetime: a factory is invoked at
most once, on first `resolve()`, and the same instance is returned on
every subsequent `resolve()` for that token.

This module implements the registry mechanism itself. No Phase 1 service
(Configuration Manager, Event Bus, Storage Interface, etc.) is registered
here — each owning work package registers its own token against its own
`ServiceRegistry` instance.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from paios.registry.errors import DuplicateRegistrationError, UnregisteredServiceError
from paios.registry.token import ServiceToken


class ServiceRegistry:
    """Registers and resolves singleton implementations against tokens."""

    def __init__(self) -> None:
        self._factories: dict[ServiceToken, Callable[[], Any]] = {}
        self._instances: dict[ServiceToken, Any] = {}

    def register(self, token: ServiceToken, factory: Callable[[], Any]) -> None:
        """Register `factory` as the sole implementation for `token`.

        Raises `DuplicateRegistrationError` if `token` is already
        registered — Phase 1 has no override/replace semantics.
        """
        if token in self._factories:
            raise DuplicateRegistrationError(token.name)
        self._factories[token] = factory

    def resolve(self, token: ServiceToken) -> Any:
        """Return the singleton instance for `token`.

        The factory registered for `token` is invoked at most once; the
        same instance is returned on every call thereafter. Raises
        `UnregisteredServiceError` if `token` has no registered factory.
        """
        if token not in self._factories:
            raise UnregisteredServiceError(token.name)
        if token not in self._instances:
            self._instances[token] = self._factories[token]()
        return self._instances[token]

    def is_registered(self, token: ServiceToken) -> bool:
        """Return whether `token` has a registered factory."""
        return token in self._factories
