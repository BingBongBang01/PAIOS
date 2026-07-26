"""ServiceToken: a nominal, interface-identifying registry key.

Per docs/910_Phase1_Core_Foundation_Specification.md#service-registry:
a `ServiceToken` is compared by identity, not by its `name` string, so two
unrelated interfaces cannot collide by sharing a name.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, eq=False)
class ServiceToken:
    """A handle identifying one registrable interface.

    Equality and hashing use object identity (the default for a class
    without `eq=True`), not `name`, so creating two tokens with the same
    `name` produces two distinct registry keys — `name` is for
    diagnostics and error messages only.
    """

    name: str
