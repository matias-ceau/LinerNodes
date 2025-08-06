"""Observability stubs for metrics, errors and retry.

These are no-op by default and safe to import anywhere in the project.
Future enablement may be controlled via environment variables or config,
for example:
- LINERNODES_METRICS_BACKEND: select metrics backend (not used yet)

Exports:
- metrics facade: counter, gauge, timer, record_distribution
- centralized errors: LinerNodesError, ConfigError, ResourceError,
  ExternalServiceError, RetryableError
- retry decorator: retry
"""

from .metrics import counter, gauge, timer, record_distribution
from .errors import (
    LinerNodesError,
    ConfigError,
    ResourceError,
    ExternalServiceError,
    RetryableError,
)
from .retry import retry

__all__ = [
    "counter",
    "gauge",
    "timer",
    "record_distribution",
    "LinerNodesError",
    "ConfigError",
    "ResourceError",
    "ExternalServiceError",
    "RetryableError",
    "retry",
]
