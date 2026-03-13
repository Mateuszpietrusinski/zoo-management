"""Application entry point: FastAPI app with config, logging, seed, routers, exception handlers."""

from fastapi import FastAPI

from zoo_management.adapters.in_memory import InMemoryRepositories
from zoo_management.adapters.web.exception_handlers import register_exception_handlers
from zoo_management.adapters.web.routers import router
from zoo_management.infrastructure.config import AppConfig
from zoo_management.infrastructure.dependencies import set_repository
from zoo_management.infrastructure.logging import configure_logging
from zoo_management.infrastructure.seed import seed_data

config = AppConfig()
configure_logging(config.log_level)

app = FastAPI(title=config.app_name)

register_exception_handlers(app)
app.include_router(router)

# Seed data at startup
repo = InMemoryRepositories()
seed_data(repo)
set_repository(repo)
