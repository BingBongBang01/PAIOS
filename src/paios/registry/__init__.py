"""Service Registry (WP-03).

Public interface for docs/910_Phase1_Core_Foundation_Specification.md#service-registry.
No Phase 1 service is registered here; each owning work package registers
its own token, per docs/920_Phase1_Work_Breakdown.md.
"""

from paios.registry.errors import DuplicateRegistrationError, UnregisteredServiceError
from paios.registry.service_registry import ServiceRegistry
from paios.registry.token import ServiceToken

__all__ = [
    "ServiceRegistry",
    "ServiceToken",
    "DuplicateRegistrationError",
    "UnregisteredServiceError",
]
