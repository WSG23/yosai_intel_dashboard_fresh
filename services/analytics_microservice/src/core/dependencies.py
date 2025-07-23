from __future__ import annotations

from dependency_injector import containers, providers

from config import get_database_config
from services.common import async_db


class Container(containers.DeclarativeContainer):
    wiring_config = containers.WiringConfiguration(packages=["services.analytics_microservice.src.api"])

    config = providers.Singleton(get_database_config)

    db_pool = providers.Resource(
        async_db.create_pool,
        shutdown=async_db.close_pool,
        dsn=providers.Callable(lambda cfg: cfg.get_connection_string(), config),
        min_size=providers.Callable(lambda cfg: cfg.initial_pool_size, config),
        max_size=providers.Callable(lambda cfg: cfg.max_pool_size, config),
        timeout=providers.Callable(lambda cfg: cfg.connection_timeout, config),
    )


container = Container()

