"""
Dependency Injection Configuration.

This module configures the DI container with all application dependencies.
"""

from utils.container import SimpleDIContainer
from utils.config import Settings, settings
from utils.auth import LocalTokenValidator, LocalTokenClient
from utils.Weather import OpenWeatherMapService
from repositories.weather_repository import (
    APIWeatherRepository,
    CachedWeatherRepository
)
from utils.logger import log


def configure_container(container: SimpleDIContainer) -> None:
    """
    Configure the DI container with application dependencies.

    This is the central place to register all dependencies.

    Args:
        container: The DI container to configure
    """
    log.info("Configuring DI container...")

    # Configuration
    container.register_instance(Settings, settings)

    # Authentication
    container.register(LocalTokenValidator, singleton=True)
    container.register(LocalTokenClient, singleton=True)

    # Weather Service with Circuit Breaker
    container.register_factory(
        OpenWeatherMapService,
        factory=lambda c: OpenWeatherMapService(
            enable_circuit_breaker=True,
            failure_threshold=5,
            recovery_timeout=60.0
        ),
        singleton=True
    )

    # Weather Repositories
    container.register_factory(
        APIWeatherRepository,
        factory=lambda c: APIWeatherRepository(
            weather_service=c.resolve(OpenWeatherMapService),
            enable_circuit_breaker=True
        ),
        singleton=True
    )

    container.register_factory(
        CachedWeatherRepository,
        factory=lambda c: CachedWeatherRepository(
            repository=c.resolve(APIWeatherRepository),
            cache_ttl=300  # 5 minutes
        ),
        singleton=True
    )

    log.info("DI container configured successfully")


def get_weather_repository() -> CachedWeatherRepository:
    """
    FastAPI dependency function to get weather repository.

    Returns:
        Configured CachedWeatherRepository instance
    """
    from utils.container import get_container
    container = get_container()
    return container.resolve(CachedWeatherRepository)


def get_token_validator() -> LocalTokenValidator:
    """
    FastAPI dependency function to get token validator.

    Returns:
        Configured LocalTokenValidator instance
    """
    from utils.container import get_container
    container = get_container()
    return container.resolve(LocalTokenValidator)


def get_weather_service() -> OpenWeatherMapService:
    """
    FastAPI dependency function to get weather service.

    Returns:
        Configured OpenWeatherMapService instance
    """
    from utils.container import get_container
    container = get_container()
    return container.resolve(OpenWeatherMapService)