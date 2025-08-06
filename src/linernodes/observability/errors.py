"""Centralized exception hierarchy for LinerNodes.

These exceptions provide a minimal, import-safe taxonomy for future
observability and error handling. They do not change any existing behavior
and are not wired into current code paths in this phase.
"""


class LinerNodesError(Exception):
    """Base exception for all LinerNodes-specific errors."""


class ConfigError(LinerNodesError):
    """Configuration-related error."""


class ResourceError(LinerNodesError):
    """Local resource access/availability error (files, disk, permissions, etc.)."""


class ExternalServiceError(LinerNodesError):
    """Error originating from an external service dependency."""


class RetryableError(LinerNodesError):
    """Error type indicating the operation may succeed on retry."""
