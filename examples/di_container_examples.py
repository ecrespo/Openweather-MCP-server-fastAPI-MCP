"""
Dependency Injection Container Examples

This module demonstrates various usage patterns for the SimpleDIContainer
implementation in this project. These examples show how to effectively use
the DI container for different scenarios.
"""

from typing import Protocol, Optional
from utils.container import SimpleDIContainer, get_container
from utils.logger import log


# ============================================================================
# Example 1: Basic Registration and Resolution
# ============================================================================

def example_basic_usage():
    """Demonstrates basic container registration and resolution."""
    print("\n=== Example 1: Basic Registration and Resolution ===\n")

    # Create a new container
    container = SimpleDIContainer()

    # Define a simple service
    class GreetingService:
        def greet(self, name: str) -> str:
            return f"Hello, {name}!"

    # Register the service
    container.register(GreetingService, singleton=True)

    # Resolve and use the service
    service = container.resolve(GreetingService)
    print(service.greet("Alice"))

    # Singleton means we get the same instance
    service2 = container.resolve(GreetingService)
    print(f"Same instance? {service is service2}")  # True


# ============================================================================
# Example 2: Protocol-Based Registration
# ============================================================================

def example_protocol_based():
    """Demonstrates registration using protocols for abstraction."""
    print("\n=== Example 2: Protocol-Based Registration ===\n")

    # Define a protocol
    class Logger(Protocol):
        def log(self, message: str) -> None:
            ...

    # Define implementations
    class ConsoleLogger:
        def log(self, message: str) -> None:
            print(f"[CONSOLE] {message}")

    class FileLogger:
        def log(self, message: str) -> None:
            print(f"[FILE] Writing to file: {message}")

    # Register with protocol
    container = SimpleDIContainer()
    container.register(Logger, ConsoleLogger, singleton=True)

    # Resolve and use
    logger = container.resolve(Logger)
    logger.log("This is a test message")

    # Can easily swap implementations
    container.register(Logger, FileLogger, singleton=True)
    logger2 = container.resolve(Logger)
    logger2.log("Now using file logger")


# ============================================================================
# Example 3: Factory Functions
# ============================================================================

def example_factory_functions():
    """Demonstrates using factory functions for complex initialization."""
    print("\n=== Example 3: Factory Functions ===\n")

    class DatabaseConnection:
        def __init__(self, connection_string: str):
            self.connection_string = connection_string
            self.connected = False

        def connect(self):
            self.connected = True
            print(f"Connected to: {self.connection_string}")

    container = SimpleDIContainer()

    # Register with factory function
    def create_database():
        db = DatabaseConnection("postgresql://localhost:5432/mydb")
        db.connect()
        return db

    container.register(DatabaseConnection, factory=create_database, singleton=True)

    # Resolve - factory is called automatically
    db = container.resolve(DatabaseConnection)
    print(f"Database connected? {db.connected}")


# ============================================================================
# Example 4: Factory with Container Access
# ============================================================================

def example_factory_with_container():
    """Demonstrates factories that can resolve other dependencies."""
    print("\n=== Example 4: Factory with Container Access ===\n")

    # Define services
    class Config:
        def __init__(self):
            self.api_url = "https://api.example.com"
            self.timeout = 30

    class ApiClient:
        def __init__(self, config: Config):
            self.config = config
            print(f"ApiClient initialized with URL: {config.api_url}")

    container = SimpleDIContainer()

    # Register config
    container.register(Config, singleton=True)

    # Register ApiClient with factory that resolves Config
    container.register_factory(
        ApiClient,
        factory=lambda c: ApiClient(config=c.resolve(Config)),
        singleton=True
    )

    # Resolve - Config is automatically resolved for ApiClient
    client = container.resolve(ApiClient)
    print(f"Client timeout: {client.config.timeout}s")


# ============================================================================
# Example 5: Instance Registration
# ============================================================================

def example_instance_registration():
    """Demonstrates registering pre-created instances."""
    print("\n=== Example 5: Instance Registration ===\n")

    class AppSettings:
        def __init__(self, debug: bool, version: str):
            self.debug = debug
            self.version = version

    # Create instance manually
    settings = AppSettings(debug=True, version="1.0.0")

    container = SimpleDIContainer()

    # Register the existing instance
    container.register_instance(AppSettings, settings)

    # Resolve - returns the same instance we registered
    resolved_settings = container.resolve(AppSettings)
    print(f"Version: {resolved_settings.version}, Debug: {resolved_settings.debug}")
    print(f"Same instance? {settings is resolved_settings}")  # True


# ============================================================================
# Example 6: Transient vs Singleton
# ============================================================================

def example_transient_vs_singleton():
    """Demonstrates the difference between transient and singleton lifetimes."""
    print("\n=== Example 6: Transient vs Singleton ===\n")

    class Counter:
        instance_count = 0

        def __init__(self):
            Counter.instance_count += 1
            self.id = Counter.instance_count
            print(f"Created Counter instance #{self.id}")

    # Singleton - same instance every time
    print("Singleton registration:")
    container1 = SimpleDIContainer()
    container1.register(Counter, singleton=True)

    c1 = container1.resolve(Counter)
    c2 = container1.resolve(Counter)
    print(f"Instance IDs: {c1.id}, {c2.id}")
    print(f"Same instance? {c1 is c2}")  # True

    # Transient - new instance every time
    print("\nTransient registration:")
    Counter.instance_count = 0  # Reset counter
    container2 = SimpleDIContainer()
    container2.register(Counter, singleton=False)

    c3 = container2.resolve(Counter)
    c4 = container2.resolve(Counter)
    print(f"Instance IDs: {c3.id}, {c4.id}")
    print(f"Same instance? {c3 is c4}")  # False


# ============================================================================
# Example 7: Auto-wiring with Build
# ============================================================================

def example_auto_wiring():
    """Demonstrates automatic dependency resolution using build()."""
    print("\n=== Example 7: Auto-wiring with Build ===\n")

    # Define services with type hints
    class Logger:
        def log(self, msg: str):
            print(f"[LOG] {msg}")

    class Database:
        def query(self, sql: str):
            print(f"[DB] Executing: {sql}")

    class UserService:
        def __init__(self, logger: Logger, database: Database):
            self.logger = logger
            self.database = database
            self.logger.log("UserService initialized")

        def get_user(self, user_id: int):
            self.database.query(f"SELECT * FROM users WHERE id = {user_id}")

    container = SimpleDIContainer()

    # Register dependencies
    container.register(Logger, singleton=True)
    container.register(Database, singleton=True)

    # Build UserService - dependencies are auto-resolved
    user_service = container.build(UserService)
    user_service.get_user(123)


# ============================================================================
# Example 8: Checking Registration Status
# ============================================================================

def example_registration_checks():
    """Demonstrates checking registration status."""
    print("\n=== Example 8: Checking Registration Status ===\n")

    class ServiceA:
        pass

    class ServiceB:
        pass

    container = SimpleDIContainer()
    container.register(ServiceA, singleton=True)

    # Check if registered
    print(f"ServiceA registered? {container.is_registered(ServiceA)}")
    print(f"ServiceB registered? {container.is_registered(ServiceB)}")

    # Get all registrations
    registrations = container.get_registrations()
    print(f"\nRegistered types: {list(registrations.keys())}")

    for service_type, info in registrations.items():
        print(f"\n{service_type.__name__}:")
        print(f"  Singleton: {info['singleton']}")
        print(f"  Has instance: {info['has_instance']}")
        print(f"  Has factory: {info['has_factory']}")


# ============================================================================
# Example 9: Container Reset and Clear
# ============================================================================

def example_container_management():
    """Demonstrates container management operations."""
    print("\n=== Example 9: Container Reset and Clear ===\n")

    class Service:
        def __init__(self):
            print("Service created")

    container = SimpleDIContainer()
    container.register(Service, singleton=True)

    # First resolution creates instance
    print("First resolve:")
    s1 = container.resolve(Service)

    # Second resolution returns cached instance
    print("\nSecond resolve (cached):")
    s2 = container.resolve(Service)
    print(f"Same instance? {s1 is s2}")

    # Clear removes all registrations
    print("\nClearing container...")
    container.clear()

    # Now Service is not registered
    print(f"Service still registered? {container.is_registered(Service)}")


# ============================================================================
# Example 10: Real-World Weather Service Example
# ============================================================================

def example_weather_service():
    """Demonstrates real-world usage with weather services from this project."""
    print("\n=== Example 10: Real-World Weather Service ===\n")

    from utils.config import Settings, settings
    from utils.auth import LocalTokenValidator, LocalTokenClient
    from utils.Weather import OpenWeatherMapService
    from repositories.weather_repository import APIWeatherRepository, CachedWeatherRepository

    # Create and configure container
    container = SimpleDIContainer()

    # Register configuration
    container.register_instance(Settings, settings)

    # Register authentication services
    container.register(LocalTokenValidator, singleton=True)
    container.register(LocalTokenClient, singleton=True)

    # Register weather service with circuit breaker
    container.register_factory(
        OpenWeatherMapService,
        factory=lambda c: OpenWeatherMapService(
            enable_circuit_breaker=True,
            failure_threshold=5,
            recovery_timeout=60.0
        ),
        singleton=True
    )

    # Register weather repositories
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
            cache_ttl=300
        ),
        singleton=True
    )

    # Resolve weather repository
    weather_repo = container.resolve(CachedWeatherRepository)
    print(f"Weather repository type: {type(weather_repo).__name__}")
    print(f"Cache TTL: {weather_repo.cache_ttl}s")

    # Check registrations
    registrations = container.get_registrations()
    print(f"\nTotal registered services: {len(registrations)}")
    for service_type in registrations.keys():
        print(f"  - {service_type.__name__}")


# ============================================================================
# Example 11: Using Global Container
# ============================================================================

def example_global_container():
    """Demonstrates using the global container singleton."""
    print("\n=== Example 11: Using Global Container ===\n")

    from utils.container import get_container, reset_container
    from utils.dependencies import configure_container

    # Get global container
    container = get_container()
    print(f"Container type: {type(container).__name__}")

    # Configure with application dependencies
    configure_container(container)

    # Check what's registered
    registrations = container.get_registrations()
    print(f"\nRegistered services: {len(registrations)}")

    # Get the same container from anywhere
    same_container = get_container()
    print(f"Same container instance? {container is same_container}")

    # Reset for testing
    print("\nResetting global container...")
    reset_container()

    # New container after reset
    new_container = get_container()
    print(f"Different container after reset? {container is not new_container}")


# ============================================================================
# Example 12: Error Handling
# ============================================================================

def example_error_handling():
    """Demonstrates error handling with the container."""
    print("\n=== Example 12: Error Handling ===\n")

    class ServiceA:
        pass

    class ServiceB:
        pass

    container = SimpleDIContainer()
    container.register(ServiceA, singleton=True)

    # Try to resolve unregistered type
    print("Attempting to resolve unregistered service:")
    try:
        service = container.resolve(ServiceB)
    except KeyError as e:
        print(f"Error: {e}")

    # Try to register without implementation or factory
    print("\nAttempting invalid registration:")
    try:
        container.register(ServiceB)  # No implementation or factory
    except ValueError as e:
        print(f"Error: {e}")


# ============================================================================
# Example 13: FastAPI Integration Pattern
# ============================================================================

def example_fastapi_integration():
    """Demonstrates how to use DI container with FastAPI."""
    print("\n=== Example 13: FastAPI Integration Pattern ===\n")

    print("""
    # FastAPI Integration Pattern

    ## 1. Create dependency functions:

    ```python
    from utils.container import get_container
    from repositories.weather_repository import CachedWeatherRepository

    def get_weather_repository() -> CachedWeatherRepository:
        container = get_container()
        return container.resolve(CachedWeatherRepository)
    ```

    ## 2. Use in FastAPI endpoints:

    ```python
    from fastapi import FastAPI, Depends

    @app.get("/weather/{city}")
    async def get_weather(
        city: str,
        repository: CachedWeatherRepository = Depends(get_weather_repository)
    ):
        data = repository.get_by_city(city)
        return {"data": data}
    ```

    ## 3. Benefits:
    - FastAPI handles dependency injection automatically
    - Easy to test by mocking dependencies
    - Clear dependency requirements in function signatures
    - Type hints provide IDE autocompletion
    """)


# ============================================================================
# Example 14: Testing with DI Container
# ============================================================================

def example_testing_pattern():
    """Demonstrates testing patterns using DI container."""
    print("\n=== Example 14: Testing with DI Container ===\n")

    print("""
    # Testing Pattern with DI Container

    ## 1. Original implementation:

    ```python
    class WeatherService:
        def get_weather(self, city: str) -> dict:
            # Real API call
            return {"city": city, "temp": 20}
    ```

    ## 2. Create mock for testing:

    ```python
    class MockWeatherService:
        def get_weather(self, city: str) -> dict:
            # Return fake data for testing
            return {"city": city, "temp": 25, "mock": True}
    ```

    ## 3. Use in tests:

    ```python
    def test_weather_endpoint():
        # Create test container
        container = SimpleDIContainer()

        # Register mock instead of real service
        container.register(WeatherService, MockWeatherService, singleton=True)

        # Resolve and test
        service = container.resolve(WeatherService)
        result = service.get_weather("Madrid")

        assert result["mock"] == True
        assert result["temp"] == 25
    ```

    ## 4. Benefits:
    - No actual API calls in tests
    - Fast and reliable tests
    - Easy to simulate different scenarios
    - Isolated unit tests
    """)


# ============================================================================
# Run All Examples
# ============================================================================

def run_all_examples():
    """Run all examples in sequence."""
    examples = [
        example_basic_usage,
        example_protocol_based,
        example_factory_functions,
        example_factory_with_container,
        example_instance_registration,
        example_transient_vs_singleton,
        example_auto_wiring,
        example_registration_checks,
        example_container_management,
        example_weather_service,
        example_global_container,
        example_error_handling,
        example_fastapi_integration,
        example_testing_pattern,
    ]

    print("=" * 70)
    print("DEPENDENCY INJECTION CONTAINER EXAMPLES")
    print("=" * 70)

    for example_func in examples:
        try:
            example_func()
        except Exception as e:
            print(f"\n❌ Error in {example_func.__name__}: {e}\n")

    print("\n" + "=" * 70)
    print("All examples completed!")
    print("=" * 70)


if __name__ == "__main__":
    run_all_examples()