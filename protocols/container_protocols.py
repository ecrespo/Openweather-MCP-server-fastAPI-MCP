"""
Dependency Injection Container Protocols.

This module defines protocol interfaces for Dependency Injection containers,
enabling centralized dependency management and facilitating testing and
component replacement.
"""

from typing import Protocol, TypeVar, Type, Callable, Any, Optional


T = TypeVar('T')


class DIContainer(Protocol):
    """
    Protocol for Dependency Injection Container implementations.

    A DI Container manages the creation and lifecycle of application
    dependencies, providing centralized configuration and easy testing.

    Key Benefits:
        - Centralized dependency configuration
        - Easy mocking and testing
        - Lazy initialization
        - Singleton management
        - Clear dependency graph

    Example implementations:
        - SimpleDIContainer: Basic container with registration and resolution
        - ScopedDIContainer: Container with request-scoped dependencies
        - AsyncDIContainer: Container supporting async factory functions
    """

    def register(
        self,
        interface: Type[T],
        implementation: Optional[Type[T]] = None,
        factory: Optional[Callable[[], T]] = None,
        singleton: bool = True
    ) -> None:
        """
        Register a dependency in the container.

        Args:
            interface: The interface/type to register
            implementation: The concrete implementation class (optional)
            factory: Factory function to create the instance (optional)
            singleton: Whether to create only one instance (default: True)

        Either implementation or factory must be provided.

        Examples:
            # Register implementation
            container.register(WeatherService, OpenWeatherMapService)

            # Register with factory
            container.register(
                Database,
                factory=lambda: Database(connection_string)
            )

            # Register singleton (default)
            container.register(CacheService, RedisCacheService, singleton=True)

            # Register transient (new instance each time)
            container.register(RequestHandler, HTTPRequestHandler, singleton=False)
        """
        ...

    def register_instance(self, interface: Type[T], instance: T) -> None:
        """
        Register an existing instance in the container.

        Use this for pre-configured instances or external dependencies.

        Args:
            interface: The interface/type to register
            instance: The pre-created instance

        Example:
            config = load_config()
            container.register_instance(Config, config)
        """
        ...

    def resolve(self, interface: Type[T]) -> T:
        """
        Resolve and return an instance of the requested type.

        Args:
            interface: The interface/type to resolve

        Returns:
            Instance of the requested type

        Raises:
            KeyError: If the type is not registered
            Exception: If instance creation fails

        Example:
            weather_service = container.resolve(WeatherService)
            weather = weather_service.get_weather("Madrid", "ES")
        """
        ...

    def is_registered(self, interface: Type[T]) -> bool:
        """
        Check if a type is registered in the container.

        Args:
            interface: The interface/type to check

        Returns:
            True if registered, False otherwise
        """
        ...

    def clear(self) -> None:
        """
        Clear all registrations and cached instances.

        Useful for testing or resetting the container state.
        """
        ...

    def get_registrations(self) -> dict[Type, dict[str, Any]]:
        """
        Get all current registrations.

        Returns:
            Dictionary mapping types to their registration info

        Example:
            {
                WeatherService: {
                    'implementation': OpenWeatherMapService,
                    'singleton': True,
                    'instance': <instance or None>
                }
            }
        """
        ...


class ScopedDIContainer(DIContainer, Protocol):
    """
    Protocol for scoped Dependency Injection Container.

    Extends DIContainer with support for request-scoped dependencies,
    useful in web applications where some dependencies should be
    created per-request.

    Example:
        # Request scope - new instance per request
        container.register_scoped(DatabaseSession, MySQLSession)

        # In request handler
        with container.create_scope() as scoped_container:
            session = scoped_container.resolve(DatabaseSession)
            # Use session...
        # Session automatically disposed after request
    """

    def register_scoped(
        self,
        interface: Type[T],
        implementation: Optional[Type[T]] = None,
        factory: Optional[Callable[[], T]] = None
    ) -> None:
        """
        Register a scoped dependency (created per scope).

        Args:
            interface: The interface/type to register
            implementation: The concrete implementation class
            factory: Factory function to create the instance
        """
        ...

    def create_scope(self) -> 'ScopedDIContainer':
        """
        Create a new scope for scoped dependencies.

        Returns:
            A scoped container that creates new instances of scoped dependencies

        Usage:
            with container.create_scope() as scope:
                service = scope.resolve(ScopedService)
                # Use service...
            # Scope disposed here
        """
        ...