"""
Protocols and Interfaces for the OpenWeather MCP Server.

This module provides protocol definitions that establish contracts for various
components in the application, enabling better type safety, testability, and
extensibility.
"""

from protocols.auth_protocols import TokenValidator, TokenProvider
from protocols.weather_protocols import WeatherService
from protocols.config_protocols import ConfigProvider
from protocols.repository_protocols import (
    WeatherRepository,
    TokenRepository,
    ConfigRepository
)
from protocols.circuit_breaker_protocols import CircuitBreaker, CircuitState, CircuitBreakerError
from protocols.container_protocols import DIContainer, ScopedDIContainer

__all__ = [
    'TokenValidator',
    'TokenProvider',
    'WeatherService',
    'ConfigProvider',
    'WeatherRepository',
    'TokenRepository',
    'ConfigRepository',
    'CircuitBreaker',
    'CircuitState',
    'CircuitBreakerError',
    'DIContainer',
    'ScopedDIContainer',
]