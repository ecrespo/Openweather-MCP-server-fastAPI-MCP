"""
Tests for Dependency Injection Container.

This module tests the SimpleDIContainer implementation including:
- Registration of dependencies (class, factory, instance)
- Resolution of dependencies
- Singleton and transient lifetimes
- Factory functions with container access
- Auto-wiring with build()
- Thread safety
- Error handling
"""

import pytest
import threading
import time
from typing import Protocol, Optional
from utils.container import SimpleDIContainer, get_container, reset_container


# ============================================================================
# Test Fixtures and Helper Classes
# ============================================================================

class ServiceA:
    """Simple test service A."""
    instance_count = 0

    def __init__(self):
        ServiceA.instance_count += 1
        self.id = ServiceA.instance_count
        self.name = "ServiceA"

    def do_something(self) -> str:
        return f"ServiceA-{self.id}"


class ServiceB:
    """Simple test service B."""

    def __init__(self):
        self.name = "ServiceB"

    def do_something(self) -> str:
        return "ServiceB"


class ServiceWithDependency:
    """Service that depends on ServiceA."""

    def __init__(self, service_a: ServiceA):
        self.service_a = service_a
        self.name = "ServiceWithDependency"

    def do_something(self) -> str:
        return f"Using: {self.service_a.do_something()}"


class ComplexService:
    """Service with multiple dependencies."""

    def __init__(self, service_a: ServiceA, service_b: ServiceB):
        self.service_a = service_a
        self.service_b = service_b

    def combine(self) -> str:
        return f"{self.service_a.do_something()} + {self.service_b.do_something()}"


class Logger(Protocol):
    """Protocol for logger services."""

    def log(self, message: str) -> None:
        ...


class ConsoleLogger:
    """Console logger implementation."""

    def __init__(self):
        self.messages = []

    def log(self, message: str) -> None:
        self.messages.append(message)


class FileLogger:
    """File logger implementation."""

    def __init__(self):
        self.messages = []

    def log(self, message: str) -> None:
        self.messages.append(f"[FILE] {message}")


@pytest.fixture
def container():
    """Provide a fresh container for each test."""
    return SimpleDIContainer()


@pytest.fixture(autouse=True)
def reset_service_counters():
    """Reset service instance counters before each test."""
    ServiceA.instance_count = 0
    yield


# ============================================================================
# Basic Registration Tests
# ============================================================================

def test_container_initialization(container):
    """Test that container initializes correctly."""
    assert container is not None
    assert len(container.get_registrations()) == 0


def test_register_simple_class(container):
    """Test registering a simple class."""
    container.register(ServiceA, ServiceA, singleton=True)

    assert container.is_registered(ServiceA)
    assert not container.is_registered(ServiceB)


def test_register_with_implementation(container):
    """Test registering interface with implementation."""
    container.register(Logger, ConsoleLogger, singleton=True)

    assert container.is_registered(Logger)

    logger = container.resolve(Logger)
    assert isinstance(logger, ConsoleLogger)


def test_register_instance(container):
    """Test registering pre-created instance."""
    service = ServiceA()
    original_id = service.id

    container.register_instance(ServiceA, service)

    resolved = container.resolve(ServiceA)
    assert resolved is service
    assert resolved.id == original_id


def test_register_with_factory(container):
    """Test registering with factory function."""
    call_count = 0

    def factory():
        nonlocal call_count
        call_count += 1
        return ServiceA()

    container.register(ServiceA, factory=factory, singleton=True)

    service1 = container.resolve(ServiceA)
    service2 = container.resolve(ServiceA)

    # Factory called once for singleton
    assert call_count == 1
    assert service1 is service2


def test_register_factory_with_container_access(container):
    """Test register_factory with container parameter."""
    container.register(ServiceA, ServiceA, singleton=True)

    container.register_factory(
        ServiceWithDependency,
        factory=lambda c: ServiceWithDependency(
            service_a=c.resolve(ServiceA)
        ),
        singleton=True
    )

    service = container.resolve(ServiceWithDependency)
    assert service.service_a is not None
    assert service.do_something() == "Using: ServiceA-1"


def test_register_method_chaining(container):
    """Test that register methods support chaining."""
    result = container.register(ServiceA, ServiceA, singleton=True)
    assert result is container

    result2 = container.register(ServiceB, ServiceB, singleton=True)
    assert result2 is container


def test_register_without_implementation_or_factory(container):
    """Test that registering without implementation or factory raises error."""
    with pytest.raises(ValueError, match="Either implementation or factory must be provided"):
        container.register(ServiceA, implementation=None, factory=None)


# ============================================================================
# Resolution Tests
# ============================================================================

def test_resolve_simple_class(container):
    """Test resolving a simple class."""
    container.register(ServiceA, ServiceA, singleton=True)

    service = container.resolve(ServiceA)
    assert service is not None
    assert isinstance(service, ServiceA)
    assert service.do_something() == "ServiceA-1"


def test_resolve_unregistered_type(container):
    """Test that resolving unregistered type raises KeyError."""
    with pytest.raises(KeyError, match="Type ServiceA is not registered"):
        container.resolve(ServiceA)


def test_resolve_via_protocol(container):
    """Test resolving via protocol interface."""
    container.register(Logger, ConsoleLogger, singleton=True)

    logger = container.resolve(Logger)
    assert isinstance(logger, ConsoleLogger)

    logger.log("test message")
    assert "test message" in logger.messages


# ============================================================================
# Singleton vs Transient Tests
# ============================================================================

def test_singleton_returns_same_instance(container):
    """Test that singleton registration returns same instance."""
    container.register(ServiceA, ServiceA, singleton=True)

    service1 = container.resolve(ServiceA)
    service2 = container.resolve(ServiceA)

    assert service1 is service2
    assert service1.id == service2.id
    assert service1.id == 1  # Only created once


def test_transient_returns_different_instances(container):
    """Test that transient registration returns new instances."""
    container.register(ServiceA, ServiceA, singleton=False)

    service1 = container.resolve(ServiceA)
    service2 = container.resolve(ServiceA)

    assert service1 is not service2
    assert service1.id != service2.id
    assert service1.id == 1
    assert service2.id == 2


def test_singleton_factory_called_once(container):
    """Test that singleton factory is called only once."""
    call_count = 0

    def factory():
        nonlocal call_count
        call_count += 1
        return ServiceA()

    container.register(ServiceA, factory=factory, singleton=True)

    container.resolve(ServiceA)
    container.resolve(ServiceA)
    container.resolve(ServiceA)

    assert call_count == 1


def test_transient_factory_called_each_time(container):
    """Test that transient factory is called each time."""
    call_count = 0

    def factory():
        nonlocal call_count
        call_count += 1
        return ServiceA()

    container.register(ServiceA, factory=factory, singleton=False)

    container.resolve(ServiceA)
    container.resolve(ServiceA)
    container.resolve(ServiceA)

    assert call_count == 3


# ============================================================================
# Auto-Wiring Tests
# ============================================================================

def test_build_with_dependencies(container):
    """Test auto-wiring with build()."""
    # Register dependencies
    container.register(ServiceA, ServiceA, singleton=True)
    container.register(ServiceB, ServiceB, singleton=True)

    # Build class with dependencies
    service = container.build(ComplexService)

    assert service is not None
    assert service.service_a is not None
    assert service.service_b is not None
    assert service.combine() == "ServiceA-1 + ServiceB"


def test_build_with_nested_dependencies(container):
    """Test auto-wiring with nested dependencies."""
    container.register(ServiceA, ServiceA, singleton=True)

    # Build ServiceWithDependency which depends on ServiceA
    service = container.build(ServiceWithDependency)

    assert service is not None
    assert service.service_a is not None
    assert service.do_something() == "Using: ServiceA-1"


def test_build_with_unregistered_dependency(container):
    """Test that build fails if dependency not registered."""
    # Don't register ServiceA

    # Should fail when trying to build ServiceWithDependency
    with pytest.raises(TypeError, match="missing 1 required positional argument"):
        container.build(ServiceWithDependency)


# ============================================================================
# Container Management Tests
# ============================================================================

def test_is_registered(container):
    """Test checking if type is registered."""
    assert not container.is_registered(ServiceA)

    container.register(ServiceA, ServiceA, singleton=True)

    assert container.is_registered(ServiceA)
    assert not container.is_registered(ServiceB)


def test_get_registrations(container):
    """Test getting all registrations."""
    container.register(ServiceA, ServiceA, singleton=True)
    container.register(ServiceB, ServiceB, singleton=False)

    registrations = container.get_registrations()

    assert len(registrations) == 2
    assert ServiceA in registrations
    assert ServiceB in registrations

    assert registrations[ServiceA]['singleton'] is True
    assert registrations[ServiceB]['singleton'] is False


def test_get_registrations_with_instance(container):
    """Test that registration info includes instance status."""
    container.register(ServiceA, ServiceA, singleton=True)

    # Before resolution
    registrations = container.get_registrations()
    assert registrations[ServiceA]['has_instance'] is False

    # After resolution
    container.resolve(ServiceA)
    registrations = container.get_registrations()
    assert registrations[ServiceA]['has_instance'] is True


def test_clear_container(container):
    """Test clearing all registrations."""
    container.register(ServiceA, ServiceA, singleton=True)
    container.register(ServiceB, ServiceB, singleton=True)

    service_a = container.resolve(ServiceA)

    assert len(container.get_registrations()) == 2
    assert container.is_registered(ServiceA)

    container.clear()

    assert len(container.get_registrations()) == 0
    assert not container.is_registered(ServiceA)
    assert not container.is_registered(ServiceB)


# ============================================================================
# Complex Factory Tests
# ============================================================================

def test_factory_with_multiple_dependencies(container):
    """Test factory function that resolves multiple dependencies."""
    container.register(ServiceA, ServiceA, singleton=True)
    container.register(ServiceB, ServiceB, singleton=True)

    container.register_factory(
        ComplexService,
        factory=lambda c: ComplexService(
            service_a=c.resolve(ServiceA),
            service_b=c.resolve(ServiceB)
        ),
        singleton=True
    )

    service = container.resolve(ComplexService)
    assert service.combine() == "ServiceA-1 + ServiceB"


def test_factory_with_conditional_logic(container):
    """Test factory with conditional initialization logic."""
    use_console = True

    container.register_factory(
        Logger,
        factory=lambda c: ConsoleLogger() if use_console else FileLogger(),
        singleton=True
    )

    logger = container.resolve(Logger)
    assert isinstance(logger, ConsoleLogger)


def test_nested_factory_resolution(container):
    """Test factories that depend on other factories."""
    # Factory 1: Creates ServiceA
    container.register_factory(
        ServiceA,
        factory=lambda c: ServiceA(),
        singleton=True
    )

    # Factory 2: Uses ServiceA from Factory 1
    container.register_factory(
        ServiceWithDependency,
        factory=lambda c: ServiceWithDependency(
            service_a=c.resolve(ServiceA)
        ),
        singleton=True
    )

    service = container.resolve(ServiceWithDependency)
    assert service.service_a.id == 1


# ============================================================================
# Thread Safety Tests
# ============================================================================

def test_concurrent_resolution(container):
    """Test that concurrent resolution is thread-safe."""
    container.register(ServiceA, ServiceA, singleton=True)

    results = []
    errors = []

    def resolve_service():
        try:
            service = container.resolve(ServiceA)
            results.append(service)
        except Exception as e:
            errors.append(e)

    # Create 20 threads trying to resolve simultaneously
    threads = [threading.Thread(target=resolve_service) for _ in range(20)]

    for t in threads:
        t.start()

    for t in threads:
        t.join()

    # All should succeed
    assert len(results) == 20
    assert len(errors) == 0

    # All should be the same singleton instance
    first_instance = results[0]
    assert all(service is first_instance for service in results)


def test_concurrent_registration(container):
    """Test that concurrent registration is thread-safe."""
    errors = []

    def register_service(service_type):
        try:
            container.register(service_type, service_type, singleton=True)
        except Exception as e:
            errors.append(e)

    # Try to register different services concurrently
    threads = [
        threading.Thread(target=register_service, args=(ServiceA,)),
        threading.Thread(target=register_service, args=(ServiceB,)),
    ]

    for t in threads:
        t.start()

    for t in threads:
        t.join()

    # Should succeed without errors
    assert len(errors) == 0
    assert container.is_registered(ServiceA)
    assert container.is_registered(ServiceB)


def test_concurrent_factory_creation(container):
    """Test that factory creation is thread-safe for singletons."""
    creation_count = 0
    creation_lock = threading.Lock()

    def factory():
        nonlocal creation_count
        time.sleep(0.01)  # Simulate slow creation
        with creation_lock:
            creation_count += 1
        return ServiceA()

    container.register(ServiceA, factory=factory, singleton=True)

    results = []

    def resolve_service():
        service = container.resolve(ServiceA)
        results.append(service)

    # Multiple threads trying to create the singleton
    threads = [threading.Thread(target=resolve_service) for _ in range(10)]

    for t in threads:
        t.start()

    for t in threads:
        t.join()

    # Factory should be called only once despite concurrent access
    assert creation_count == 1
    assert all(service is results[0] for service in results)


# ============================================================================
# Global Container Tests
# ============================================================================

def test_get_global_container():
    """Test getting global container instance."""
    container1 = get_container()
    container2 = get_container()

    assert container1 is container2  # Same instance


def test_reset_global_container():
    """Test resetting global container."""
    container1 = get_container()
    container1.register(ServiceA, ServiceA, singleton=True)

    assert container1.is_registered(ServiceA)

    reset_container()

    container2 = get_container()
    assert not container2.is_registered(ServiceA)


# ============================================================================
# Error Handling Tests
# ============================================================================

def test_resolve_after_factory_error(container):
    """Test that resolution fails gracefully if factory raises error."""

    def failing_factory():
        raise RuntimeError("Factory failed!")

    container.register(ServiceA, factory=failing_factory, singleton=True)

    with pytest.raises(RuntimeError, match="Factory failed!"):
        container.resolve(ServiceA)


def test_resolve_after_constructor_error(container):
    """Test that resolution fails if constructor raises error."""

    class FailingService:
        def __init__(self):
            raise ValueError("Constructor failed!")

    container.register(FailingService, FailingService, singleton=True)

    with pytest.raises(ValueError, match="Constructor failed!"):
        container.resolve(FailingService)


# ============================================================================
# Integration Tests
# ============================================================================

def test_real_world_scenario(container):
    """Test a realistic dependency graph."""

    # Configuration
    class Config:
        def __init__(self):
            self.api_url = "https://api.example.com"
            self.timeout = 30

    # Low-level service
    class HttpClient:
        def __init__(self, config: Config):
            self.config = config

        def get(self, endpoint: str) -> dict:
            return {"url": f"{self.config.api_url}/{endpoint}"}

    # Mid-level service
    class ApiService:
        def __init__(self, client: HttpClient):
            self.client = client

        def fetch_data(self, endpoint: str) -> dict:
            return self.client.get(endpoint)

    # High-level service
    class BusinessLogic:
        def __init__(self, api: ApiService):
            self.api = api

        def get_user_data(self, user_id: int) -> dict:
            return self.api.fetch_data(f"users/{user_id}")

    # Register everything
    config_instance = Config()
    container.register_instance(Config, config_instance)

    container.register_factory(
        HttpClient,
        factory=lambda c: HttpClient(config=c.resolve(Config)),
        singleton=True
    )

    container.register_factory(
        ApiService,
        factory=lambda c: ApiService(client=c.resolve(HttpClient)),
        singleton=True
    )

    container.register_factory(
        BusinessLogic,
        factory=lambda c: BusinessLogic(api=c.resolve(ApiService)),
        singleton=True
    )

    # Resolve top-level service
    business = container.resolve(BusinessLogic)

    # Test full chain
    result = business.get_user_data(123)
    assert result["url"] == "https://api.example.com/users/123"


def test_switching_implementations(container):
    """Test swapping implementations using protocols."""
    # Register console logger first
    container.register(Logger, ConsoleLogger, singleton=True)

    logger1 = container.resolve(Logger)
    assert isinstance(logger1, ConsoleLogger)

    # Switch to file logger
    container.register(Logger, FileLogger, singleton=True)

    logger2 = container.resolve(Logger)
    assert isinstance(logger2, FileLogger)
    assert logger1 is not logger2


# ============================================================================
# Registration Info Tests
# ============================================================================

def test_registration_info_structure(container):
    """Test that registration info has correct structure."""
    container.register(ServiceA, ServiceA, singleton=True)

    info = container.get_registrations()[ServiceA]

    assert 'implementation' in info
    assert 'has_factory' in info
    assert 'singleton' in info
    assert 'has_instance' in info

    assert info['implementation'] == ServiceA
    assert info['has_factory'] is False
    assert info['singleton'] is True
    assert info['has_instance'] is False


def test_registration_info_with_factory(container):
    """Test registration info for factory registrations."""
    container.register(ServiceA, factory=lambda: ServiceA(), singleton=True)

    info = container.get_registrations()[ServiceA]

    assert info['has_factory'] is True
    assert info['implementation'] is None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])