"""Unit tests for the Service Registry (WP-03).

Covers docs/910_Phase1_Core_Foundation_Specification.md#service-registry
and docs/920_Phase1_Work_Breakdown.md#wp-03--service-registry.

Uses synthetic test tokens only; no real Phase 1 service is registered
here, per WP-03's scope.
"""

from __future__ import annotations

import pytest

from paios.registry import (
    DuplicateRegistrationError,
    ServiceRegistry,
    ServiceToken,
    UnregisteredServiceError,
)


class FakeServiceA:
    pass


class FakeServiceB:
    pass


def test_register_then_resolve_returns_factory_instance() -> None:
    registry = ServiceRegistry()
    token = ServiceToken("FakeServiceA")
    instance = FakeServiceA()

    registry.register(token, lambda: instance)

    assert registry.resolve(token) is instance


def test_resolve_unregistered_token_raises() -> None:
    registry = ServiceRegistry()
    token = ServiceToken("FakeServiceA")

    with pytest.raises(UnregisteredServiceError) as exc_info:
        registry.resolve(token)

    assert exc_info.value.token_name == "FakeServiceA"


def test_register_same_token_twice_raises() -> None:
    registry = ServiceRegistry()
    token = ServiceToken("FakeServiceA")
    registry.register(token, lambda: FakeServiceA())

    with pytest.raises(DuplicateRegistrationError) as exc_info:
        registry.register(token, lambda: FakeServiceA())

    assert exc_info.value.token_name == "FakeServiceA"


def test_is_registered_reports_registration_state() -> None:
    registry = ServiceRegistry()
    token = ServiceToken("FakeServiceA")

    assert registry.is_registered(token) is False

    registry.register(token, lambda: FakeServiceA())

    assert registry.is_registered(token) is True


def test_two_tokens_with_same_name_are_distinct_registry_keys() -> None:
    registry = ServiceRegistry()
    token_a = ServiceToken("Shared")
    token_b = ServiceToken("Shared")
    instance_a = FakeServiceA()
    instance_b = FakeServiceB()

    registry.register(token_a, lambda: instance_a)
    registry.register(token_b, lambda: instance_b)

    assert registry.resolve(token_a) is instance_a
    assert registry.resolve(token_b) is instance_b


def test_singleton_lifetime_factory_invoked_once() -> None:
    registry = ServiceRegistry()
    token = ServiceToken("FakeServiceA")
    call_count = {"count": 0}

    def factory() -> FakeServiceA:
        call_count["count"] += 1
        return FakeServiceA()

    registry.register(token, factory)

    first = registry.resolve(token)
    second = registry.resolve(token)

    assert first is second
    assert call_count["count"] == 1


def test_factory_not_invoked_until_first_resolve() -> None:
    registry = ServiceRegistry()
    token = ServiceToken("FakeServiceA")
    call_count = {"count": 0}

    def factory() -> FakeServiceA:
        call_count["count"] += 1
        return FakeServiceA()

    registry.register(token, factory)

    assert call_count["count"] == 0

    registry.resolve(token)

    assert call_count["count"] == 1


def test_two_registries_do_not_share_registrations() -> None:
    registry_a = ServiceRegistry()
    registry_b = ServiceRegistry()
    token = ServiceToken("FakeServiceA")

    registry_a.register(token, lambda: FakeServiceA())

    assert registry_a.is_registered(token) is True
    assert registry_b.is_registered(token) is False
    with pytest.raises(UnregisteredServiceError):
        registry_b.resolve(token)


def test_independent_tokens_resolve_independently() -> None:
    registry = ServiceRegistry()
    token_a = ServiceToken("FakeServiceA")
    token_b = ServiceToken("FakeServiceB")
    instance_a = FakeServiceA()
    instance_b = FakeServiceB()

    registry.register(token_a, lambda: instance_a)
    registry.register(token_b, lambda: instance_b)

    assert registry.resolve(token_a) is instance_a
    assert registry.resolve(token_b) is instance_b
