import logging
import os
from typing import Optional


def _get_log_level() -> int:
    """Resolve log level from environment, default INFO."""
    raw = os.getenv("LINERNODES_LOG_LEVEL", "INFO")
    level = (raw or "INFO").upper()
    return getattr(logging, level, logging.INFO)


def _use_json() -> bool:
    """Enable JSON logs when LINERNODES_LOG_JSON=1."""
    return os.getenv("LINERNODES_LOG_JSON", "0") in ("1", "true", "TRUE")


class _JsonFormatter(logging.Formatter):
    """Very small JSON formatter (no external deps)."""

    def format(self, record: logging.LogRecord) -> str:
        # Keep it minimal and stable
        data = {
            "timestamp": self.formatTime(record, datefmt="%Y-%m-%dT%H:%M:%S%z"),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        # Optional extras
        if record.exc_info:
            data["exc_info"] = self.formatException(record.exc_info)
        if hasattr(record, "operation"):
            data["operation"] = getattr(record, "operation")
        if hasattr(record, "request_id"):
            data["request_id"] = getattr(record, "request_id")
        # Manual JSON to avoid importing json in hot paths
        # It's acceptable to import json here since it's stdlib and tiny.
        import json as _json

        return _json.dumps(data, ensure_ascii=False)


def setup_logging(
    name: Optional[str] = None, propagate: bool = False
) -> logging.Logger:
    """
    Initialize a console logger with optional JSON formatting.
    Idempotent: calling multiple times will not duplicate handlers.

    Env:
      - LINERNODES_LOG_LEVEL: DEBUG|INFO|WARNING|ERROR (default: INFO)
      - LINERNODES_LOG_JSON: 1 to enable JSON logs (default: 0)
    """
    logger_name = name or "linernodes"
    logger = logging.getLogger(logger_name)

    # Avoid adding multiple handlers if already configured
    if getattr(logger, "_linernodes_configured", False):
        return logger

    logger.setLevel(_get_log_level())
    logger.propagate = propagate

    handler = logging.StreamHandler()
    if _use_json():
        formatter: logging.Formatter = _JsonFormatter()
    else:
        formatter = logging.Formatter(
            fmt="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
    handler.setFormatter(formatter)
    logger.addHandler(handler)

    # Mark as configured to ensure idempotence
    logger._linernodes_configured = True  # type: ignore[attr-defined]
    logger.debug("Logger initialized", extra={"operation": "setup_logging"})
    return logger


def get_logger(name: Optional[str] = None) -> logging.Logger:
    """
    Convenience accessor that ensures the base logger is configured
    and returns a child logger for the given name.
    """
    base = setup_logging()
    if name:
        return base.getChild(name)
    return base
