"""Application configuration (PRD §7.5 — plain dataclass, no Pydantic Settings)."""

from dataclasses import dataclass


@dataclass(frozen=True)
class AppConfig:
    """Immutable app configuration (host, port, log level). No DATABASE_URL for MVP."""

    app_name: str = "Zoo Management System"
    host: str = "0.0.0.0"
    port: int = 8000
    log_level: str = "INFO"
