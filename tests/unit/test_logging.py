"""Unit tests for infrastructure logging (Phase 8.2)."""

import json
import logging

from zoo_management.infrastructure.logging import JSONFormatter, configure_logging


def test_json_formatter_produces_valid_json() -> None:
    """JSONFormatter outputs valid JSON with timestamp, level, logger, message."""
    formatter = JSONFormatter()
    record = logging.LogRecord(
        name="test.logger",
        level=logging.INFO,
        pathname="",
        lineno=0,
        msg="Hello %s",
        args=("world",),
        exc_info=None,
    )
    output = formatter.format(record)
    parsed = json.loads(output)
    assert "timestamp" in parsed
    assert parsed["level"] == "INFO"
    assert parsed["logger"] == "test.logger"
    assert parsed["message"] == "Hello world"


def test_configure_logging_sets_level() -> None:
    """configure_logging sets root logger level."""
    root = logging.getLogger()
    original_level = root.level
    try:
        configure_logging("DEBUG")
        assert root.level == logging.DEBUG
        configure_logging("WARNING")
        assert root.level == logging.WARNING
    finally:
        root.setLevel(original_level)
        root.handlers.clear()
