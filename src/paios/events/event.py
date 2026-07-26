"""PAIOS Event types and schema registry."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any, Dict, Optional, Protocol, runtime_checkable

from .exceptions import InvalidEventError


@runtime_checkable
class SchemaValidator(Protocol):
    """Protocol for validating event payloads against a schema."""

    def validate(self, payload: dict[str, Any]) -> None:
        """Validate payload against the schema.

        Raises:
            InvalidEventError: If payload does not conform to schema.
        """
        ...


class Event:
    """Immutable event object.

    Attributes:
        id: Unique identifier for this event instance.
        type: Namespaced event type (e.g., "module.capability.registered").
        version: Schema version of the payload (semver string).
        timestamp: When the event was emitted (ISO 8601 UTC).
        source: Module or capability that emitted the event.
        correlationId: ID linking to the causal request/workflow.
        payload: Event-specific data, validated against schema for type+version.
    """

    def __init__(
        self,
        *,
        id: str | None = None,
        type: str,
        version: str,
        timestamp: datetime | None = None,
        source: str,
        correlationId: str | None = None,
        payload: dict[str, Any],
    ) -> None:
        self.id = id or str(uuid.uuid4())
        self.type = type
        self.version = version
        self.timestamp = timestamp or datetime.now(timezone.utc)
        self.source = source
        self.correlationId = correlationId or self.id
        self.payload = payload

    def to_dict(self) -> dict[str, Any]:
        """Serialize event to a dictionary."""
        return {
            "id": self.id,
            "type": self.type,
            "version": self.version,
            "timestamp": self.timestamp.isoformat(),
            "source": self.source,
            "correlationId": self.correlationId,
            "payload": self.payload,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Event":
        """Deserialize event from a dictionary."""
        return cls(
            id=data.get("id"),
            type=data["type"],
            version=data["version"],
            timestamp=datetime.fromisoformat(data["timestamp"]),
            source=data["source"],
            correlationId=data.get("correlationId"),
            payload=data["payload"],
        )


class EventSchemaRegistry:
    """Registry for event schemas and validation."""

    def __init__(self) -> None:
        self._schemas: dict[tuple[str, str], SchemaValidator] = {}

    def register(
        self,
        event_type: str,
        version: str,
        validator: SchemaValidator,
    ) -> None:
        """Register a validator for an event type and version.

        Args:
            event_type: Namespaced event type.
            version: Semver version string.
            validator: Object implementing SchemaValidator protocol.
        """
        self._schemas[(event_type, version)] = validator

    def get_validator(
        self, event_type: str, version: str
    ) -> SchemaValidator | None:
        """Retrieve validator for event type and version, if registered."""
        return self._schemas.get((event_type, version))

    def validate_event(self, event: Event) -> None:
        """Validate an event's payload against its registered schema.

        Args:
            event: Event to validate.

        Raises:
            InvalidEventError: If no validator registered for type/version
                or payload fails validation.
        """
        validator = self.get_validator(event.type, event.version)
        if validator is None:
            raise InvalidEventError(
                f"No schema registered for event type '{event.type}' "
                f"version '{event.version}'"
            )
        validator.validate(event.payload)


# Global registry instance
event_schema_registry = EventSchemaRegistry()