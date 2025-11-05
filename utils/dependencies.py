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
from repositories.token_repository import InMemoryTokenRepository
from utils.circuit_breaker import CircuitBreakerRegistry
from utils.http_client import HTTPClient
from utils.logger import log
from slowapi import Limiter
from slowapi.util import get_remote_address


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
    container.register(LocalTokenValidator, LocalTokenValidator, singleton=True)
    container.register(LocalTokenClient, LocalTokenClient, singleton=True)

    # HTTP Client (must be registered before Weather Service)
    container.register_factory(
        HTTPClient,
        factory=lambda c: HTTPClient(timeout=10.0),
        singleton=True
    )

    # Weather Service with Circuit Breaker and HTTP Client injection
    container.register_factory(
        OpenWeatherMapService,
        factory=lambda c: OpenWeatherMapService(
            http_client=c.resolve(HTTPClient),
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

    # Circuit Breaker Registry
    container.register(CircuitBreakerRegistry, CircuitBreakerRegistry, singleton=True)

    # Token Repository
    container.register(InMemoryTokenRepository, InMemoryTokenRepository, singleton=True)

    # Rate Limiter
    container.register_factory(
        Limiter,
        factory=lambda c: Limiter(
            key_func=get_remote_address,
            default_limits=["100/minute"]
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


def get_circuit_breaker_registry() -> CircuitBreakerRegistry:
    """
    FastAPI dependency function to get circuit breaker registry.

    Returns:
        Configured CircuitBreakerRegistry instance
    """
    from utils.container import get_container
    container = get_container()
    return container.resolve(CircuitBreakerRegistry)


def get_token_repository() -> InMemoryTokenRepository:
    """
    FastAPI dependency function to get token repository.

    Returns:
        Configured InMemoryTokenRepository instance
    """
    from utils.container import get_container
    container = get_container()
    return container.resolve(InMemoryTokenRepository)


def get_limiter() -> Limiter:
    """
    FastAPI dependency function to get rate limiter.

    Returns:
        Configured Limiter instance
    """
    from utils.container import get_container
    container = get_container()
    return container.resolve(Limiter)


def get_http_client() -> HTTPClient:
    """
    FastAPI dependency function to get HTTP client.

    Returns:
        Configured HTTPClient instance
    """
    from utils.container import get_container
    container = get_container()
    return container.resolve(HTTPClient)