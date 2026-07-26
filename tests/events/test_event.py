"""Unit tests for PAIOS Event types and schema registry."""

import datetime
from typing import Any, Dict

import pytest

from src.paios.events.event import Event, EventSchemaRegistry, event_schema_registry
from src.paios.events.exceptions import InvalidEventError


class DummyValidator:
    """A simple validator for testing."""

    def __init__(self, required_field: str) -> None:
        self.required_field = required_field

    def validate(self, payload: Dict[str, Any]) -> None:
        if self.required_field not in payload:
            raise InvalidEventError(f"Missing required field: {self.required_field}")


def test_event_creation() -> None:
    """Test creating an event with all fields."""
    event_id = "test-id"
    event_type = "test.event"
    version = "1.0.0"
    timestamp = datetime.datetime(2024, 1, 1, 12, 0, 0, tzinfo=datetime.timezone.utc)
    source = "test.source"
    correlation_id = "corr-123"
    payload = {"key": "value"}

    event = Event(
        id=event_id,
        type=event_type,
        version=version,
        timestamp=timestamp,
        source=source,
        correlationId=correlation_id,
        payload=payload,
    )

    assert event.id == event_id
    assert event.type == event_type
    assert event.version == version
    assert event.timestamp == timestamp
    assert event.source == source
    assert event.correlationId == correlation_id
    assert event.payload == payload


def test_event_creation_defaults() -> None:
    """Test creating an event with default id and correlationId."""
    event_type = "test.event"
    version = "1.0.0"
    source = "test.source"
    payload = {"key": "value"}

    event = Event(type=event_type, version=version, source=source, payload=payload)

    assert isinstance(event.id, str)
    assert event.id  # not empty
    assert event.type == event_type
    assert event.version == version
    assert isinstance(event.timestamp, datetime.datetime)
    assert event.source == source
    assert event.correlationId == event.id  # defaults to event id
    assert event.payload == payload


def test_event_serialization() -> None:
    """Test event to_dict and from_dict roundtrip."""
    original = Event(
        id="test-id",
        type="test.event",
        version="1.0.0",
        timestamp=datetime.datetime(2024, 1, 1, 12, 0, 0, tzinfo=datetime.timezone.utc),
        source="test.source",
        correlationId="corr-123",
        payload={"key": "value"},
    )

    data = original.to_dict()
    restored = Event.from_dict(data)

    assert restored.id == original.id
    assert restored.type == original.type
    assert restored.version == original.version
    assert restored.timestamp == original.timestamp
    assert restored.source == original.source
    assert restored.correlationId == original.correlationId
    assert restored.payload == original.payload


def test_event_schema_registry_register_and_get() -> None:
    """Test registering and retrieving a validator."""
    registry = EventSchemaRegistry()
    validator = DummyValidator("required_field")

    registry.register("test.event", "1.0.0", validator)

    retrieved = registry.get_validator("test.event", "1.0.0")
    assert retrieved is validator

    # Non-existent returns None
    assert registry.get_validator("unknown", "1.0.0") is None


def test_event_schema_registry_validate_event() -> None:
    """Test validating an event against a registered validator."""
    registry = EventSchemaRegistry()
    validator = DummyValidator("required_field")
    registry.register("test.event", "1.0.0", validator)

    # Valid event
    valid_event = Event(
        type="test.event",
        version="1.0.0",
        source="test.source",
        payload={"required_field": "value"},
    )
    # Should not raise
    registry.validate_event(valid_event)

    # Invalid event (missing required field)
    invalid_event = Event(
        type="test.event",
        version="1.0.0",
        source="test.source",
        payload={"other": "value"},
    )
    with pytest.raises(InvalidEventError, match="Missing required field"):
        registry.validate_event(invalid_event)

    # Event with no registered validator
    unknown_event = Event(
        type="unknown.event",
        version="1.0.0",
        source="test.source",
        payload={},
    )
    with pytest.raises(InvalidEventError, match="No schema registered"):
        registry.validate_event(unknown_event)


def test_global_registry() -> None:
    """Test that the global registry instance is of the correct type."""
    assert isinstance(event_schema_registry, EventSchemaRegistry)