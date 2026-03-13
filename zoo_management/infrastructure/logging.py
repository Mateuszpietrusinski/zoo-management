"""Structured JSON logging (PRD §7.6)."""

import json
import logging
from datetime import UTC, datetime


class JSONFormatter(logging.Formatter):
    """Format log records as JSON with timestamp, level, logger, message, and optional extra."""

    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON with timestamp, level, logger, message, extra.

        Args:
            record: Log record to format.

        Returns:
            JSON string representation of the record.
        """
        log_record: dict[str, object] = {
            "timestamp": datetime.now(UTC).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        if hasattr(record, "__dict__"):
            extras = {
                k: v
                for k, v in record.__dict__.items()
                if k not in logging.LogRecord.__dict__ and not k.startswith("_")
            }
            if extras:
                log_record["extra"] = extras
        return json.dumps(log_record)


def configure_logging(level: str = "INFO") -> None:
    """Configure root logger with JSON formatter and given level.

    Args:
        level: Log level (e.g. 'INFO', 'DEBUG').
    """
    handler = logging.StreamHandler()
    handler.setFormatter(JSONFormatter())
    root = logging.getLogger()
    root.setLevel(level)
    root.addHandler(handler)
