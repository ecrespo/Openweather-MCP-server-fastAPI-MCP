"""
Dependency Injection Container Implementation.

This module provides a simple but powerful DI container for managing
application dependencies.
"""

from typing import Type, TypeVar, Callable, Any, Optional, Dict
import threading
from dataclasses import dataclass

from utils.logger import log


T = TypeVar('T')


@dataclass
class Registration:
    """
    Represents a dependency registration.

    :ivar implementation: The concrete implementation class
    :ivar factory: Factory function to create instances
    :ivar singleton: Whether to cache the instance
    :ivar instance: Cached instance (for singletons)
    """
    implementation: Optional[Type] = None
    factory: Optional[Callable] = None
    singleton: bool = True
    instance: Optional[Any] = None


class SimpleDIContainer:
    """
    Simple Dependency Injection Container.

    This container manages application dependencies with support for:
    - Singleton and transient lifetimes
    - Factory functions
    - Instance registration
    - Thread-safe operations

    Example:
        container = SimpleDIContainer()

        # Register dependencies
        container.register(WeatherService, OpenWeatherMapService)
        container.register(CacheService, RedisCacheService, singleton=True)

        # Resolve dependencies
        weather_service = container.resolve(WeatherService)
        weather = weather_service.get_weather("Madrid", "ES")
    """

    def __init__(self):
        """Initialize the DI container."""
        self._registrations: Dict[Type, Registration] = {}
        self._lock = threading.RLock()
        log.info("SimpleDIContainer initialized")

    def register(
        self,
        interface: Type[T],
        implementation: Optional[Type[T]] = None,
        factory: Optional[Callable[[], T]] = None,
        singleton: bool = True
    ) -> 'SimpleDIContainer':
        """
        Register a dependency in the container.

        Args:
            interface: The interface/type to register
            implementation: The concrete implementation class
            factory: Factory function to create the instance
            singleton: Whether to create only one instance

        Returns:
            Self for method chaining

        Raises:
            ValueError: If neither implementation nor factory is provided
        """
        if implementation is None and factory is None:
            raise ValueError("Either implementation or factory must be provided")

        with self._lock:
            registration = Registration(
                implementation=implementation,
                factory=factory,
                singleton=singleton,
                instance=None
            )
            self._registrations[interface] = registration

            log.debug(
                f"Registered {interface.__name__} -> "
                f"{implementation.__name__ if implementation else 'factory'} "
                f"(singleton={singleton})"
            )

        return self

    def register_instance(self, interface: Type[T], instance: T) -> 'SimpleDIContainer':
        """
        Register an existing instance in the container.

        Args:
            interface: The interface/type to register
            instance: The pre-created instance

        Returns:
            Self for method chaining
        """
        with self._lock:
            registration = Registration(
                implementation=None,
                factory=None,
                singleton=True,
                instance=instance
            )
            self._registrations[interface] = registration

            log.debug(f"Registered instance for {interface.__name__}")

        return self

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
        """
        with self._lock:
            if interface not in self._registrations:
                raise KeyError(
                    f"Type {interface.__name__} is not registered. "
                    f"Available types: {list(self._registrations.keys())}"
                )

            registration = self._registrations[interface]

            # Return cached instance if singleton and already created
            if registration.singleton and registration.instance is not None:
                return registration.instance

            # Create new instance
            try:
                if registration.factory:
                    instance = registration.factory()
                elif registration.implementation:
                    instance = registration.implementation()
                else:
                    # Should not happen if registration is valid
                    raise ValueError(
                        f"Invalid registration for {interface.__name__}"
                    )

                # Cache if singleton
                if registration.singleton:
                    registration.instance = instance

                log.debug(f"Resolved {interface.__name__}")
                return instance

            except Exception as e:
                log.error(f"Error resolving {interface.__name__}: {e}")
                raise

    def is_registered(self, interface: Type[T]) -> bool:
        """
        Check if a type is registered in the container.

        Args:
            interface: The interface/type to check

        Returns:
            True if registered, False otherwise
        """
        with self._lock:
            return interface in self._registrations

    def clear(self) -> None:
        """Clear all registrations and cached instances."""
        with self._lock:
            count = len(self._registrations)
            self._registrations.clear()
            log.info(f"Cleared {count} registrations from container")

    def get_registrations(self) -> Dict[Type, Dict[str, Any]]:
        """
        Get all current registrations.

        Returns:
            Dictionary mapping types to their registration info
        """
        with self._lock:
            result = {}
            for interface, reg in self._registrations.items():
                result[interface] = {
                    'implementation': reg.implementation,
                    'has_factory': reg.factory is not None,
                    'singleton': reg.singleton,
                    'has_instance': reg.instance is not None
                }
            return result

    def register_factory(
        self,
        interface: Type[T],
        factory: Callable[['SimpleDIContainer'], T],
        singleton: bool = True
    ) -> 'SimpleDIContainer':
        """
        Register a factory function that receives the container.

        This allows the factory to resolve other dependencies.

        Args:
            interface: The interface/type to register
            factory: Factory function that receives the container
            singleton: Whether to create only one instance

        Returns:
            Self for method chaining

        Example:
            def create_service(container):
                config = container.resolve(Config)
                cache = container.resolve(CacheService)
                return WeatherService(config, cache)

            container.register_factory(WeatherService, create_service)
        """
        def wrapper():
            return factory(self)

        return self.register(interface, factory=wrapper, singleton=singleton)

    def build(self, cls: Type[T]) -> T:
        """
        Build an instance of a class, resolving its dependencies.

        This method attempts to auto-wire constructor dependencies
        by inspecting type hints.

        Args:
            cls: The class to instantiate

        Returns:
            Instance of the class

        Example:
            class MyService:
                def __init__(self, config: Config, cache: CacheService):
                    self.config = config
                    self.cache = cache

            service = container.build(MyService)
        """
        import inspect

        try:
            # Get constructor signature
            sig = inspect.signature(cls.__init__)

            # Resolve parameters
            kwargs = {}
            for param_name, param in sig.parameters.items():
                if param_name == 'self':
                    continue

                # Try to resolve by type hint
                if param.annotation != inspect.Parameter.empty:
                    if self.is_registered(param.annotation):
                        kwargs[param_name] = self.resolve(param.annotation)

            # Create instance
            instance = cls(**kwargs)
            log.debug(f"Built {cls.__name__} with dependencies: {list(kwargs.keys())}")
            return instance

        except Exception as e:
            log.error(f"Error building {cls.__name__}: {e}")
            raise


# Global container instance
_global_container: Optional[SimpleDIContainer] = None
_container_lock = threading.Lock()


def get_container() -> SimpleDIContainer:
    """
    Get the global DI container instance (singleton).

    Returns:
        The global SimpleDIContainer instance
    """
    global _global_container

    if _global_container is None:
        with _container_lock:
            if _global_container is None:
                _global_container = SimpleDIContainer()

    return _global_container


def reset_container() -> None:
    """
    Reset the global container.

    Useful for testing or application restart.
    """
    global _global_container

    with _container_lock:
        if _global_container:
            _global_container.clear()
        _global_container = None
        log.info("Global container reset")