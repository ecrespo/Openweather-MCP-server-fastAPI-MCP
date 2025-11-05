# Dependency Injection Container

## Table of Contents

- [Overview](#overview)
- [What is Dependency Injection?](#what-is-dependency-injection)
- [Why Use a DI Container?](#why-use-a-di-container)
- [Architecture](#architecture)
- [Getting Started](#getting-started)
- [Core Concepts](#core-concepts)
- [Usage Patterns](#usage-patterns)
- [FastAPI Integration](#fastapi-integration)
- [Testing](#testing)
- [Best Practices](#best-practices)
- [API Reference](#api-reference)
- [Troubleshooting](#troubleshooting)

---

## Overview

The Dependency Injection (DI) Container is a centralized system for managing application dependencies, their lifecycles, and their relationships. It implements the **Inversion of Control (IoC)** pattern, where the container is responsible for creating and managing object instances instead of objects creating their own dependencies.

### Key Benefits

- **Loose Coupling**: Components depend on abstractions (protocols) rather than concrete implementations
- **Easy Testing**: Replace real dependencies with mocks or stubs during testing
- **Centralized Configuration**: All dependency wiring in one place
- **Lifecycle Management**: Automatic handling of singleton and transient instances
- **Type Safety**: Full type hints and protocol-based design

---

## What is Dependency Injection?

Dependency Injection is a design pattern where objects receive their dependencies from external sources rather than creating them internally.

### Without Dependency Injection

```python
class WeatherController:
    def __init__(self):
        # Hard-coded dependencies
        self.api_key = "hardcoded_key"
        self.weather_service = OpenWeatherMapService(self.api_key)
        self.cache = CacheService(ttl=300)
```

**Problems:**
- Hard to test (can't replace real API calls)
- Tight coupling to concrete implementations
- Configuration scattered throughout code
- Difficult to change implementations

### With Dependency Injection

```python
class WeatherController:
    def __init__(self, weather_service: WeatherService, cache: CacheService):
        # Dependencies injected from outside
        self.weather_service = weather_service
        self.cache = cache
```

**Benefits:**
- Easy to test (inject mocks)
- Depends on abstractions (protocols)
- Flexible - can change implementations
- Configuration centralized in DI container

---

## Why Use a DI Container?

While you can do dependency injection manually, a DI container provides:

1. **Automatic Dependency Resolution**
   - Container resolves nested dependencies automatically
   - No need to manually wire complex object graphs

2. **Lifecycle Management**
   - Singletons: One instance for entire application
   - Transient: New instance every time
   - Automatic caching and reuse

3. **Centralized Configuration**
   - All dependency wiring in one place (`dependencies.py`)
   - Easy to see entire dependency graph
   - Simple to reconfigure for different environments

4. **Factory Functions**
   - Complex initialization logic
   - Dependencies that need other dependencies
   - Conditional creation based on configuration

---

## Architecture

### Components

```
┌─────────────────────────────────────────────────────────────┐
│                    Application Layer                        │
│  (FastAPI endpoints, business logic)                        │
└───────────────────────┬─────────────────────────────────────┘
                        │ Depends()
                        ▼
┌─────────────────────────────────────────────────────────────┐
│              Dependency Functions Layer                     │
│  get_weather_repository(), get_token_validator()            │
└───────────────────────┬─────────────────────────────────────┘
                        │ resolve()
                        ▼
┌─────────────────────────────────────────────────────────────┐
│                 DI Container Layer                          │
│  SimpleDIContainer - manages registrations                  │
└───────────────────────┬─────────────────────────────────────┘
                        │ creates
                        ▼
┌─────────────────────────────────────────────────────────────┐
│              Service Implementations                        │
│  OpenWeatherMapService, CachedWeatherRepository, etc.       │
└─────────────────────────────────────────────────────────────┘
```

### File Structure

```
utils/
├── container.py           # SimpleDIContainer implementation
├── dependencies.py        # Container configuration
└── ...

protocols/
├── container_protocols.py # DIContainer protocol definition
└── ...

examples/
└── di_container_examples.py  # Usage examples

tests/
└── test_container.py      # Container tests
```

---

## Getting Started

### Basic Usage

```python
from utils.container import SimpleDIContainer

# 1. Create container
container = SimpleDIContainer()

# 2. Register dependencies
class GreetingService:
    def greet(self, name: str) -> str:
        return f"Hello, {name}!"

container.register(GreetingService, singleton=True)

# 3. Resolve and use
service = container.resolve(GreetingService)
print(service.greet("World"))  # "Hello, World!"
```

### Using the Global Container

```python
from utils.container import get_container
from utils.dependencies import configure_container

# Get global singleton container
container = get_container()

# Configure with application dependencies
configure_container(container)

# Resolve services
from repositories.weather_repository import CachedWeatherRepository
weather_repo = container.resolve(CachedWeatherRepository)
```

---

## Core Concepts

### 1. Registration

**Register with class:**
```python
container.register(WeatherService, OpenWeatherMapService, singleton=True)
```

**Register with factory:**
```python
def create_weather_service():
    return OpenWeatherMapService(api_key="xxx")

container.register(WeatherService, factory=create_weather_service, singleton=True)
```

**Register existing instance:**
```python
config = Settings()
container.register_instance(Settings, config)
```

### 2. Resolution

**Simple resolution:**
```python
service = container.resolve(WeatherService)
```

**Auto-wiring with build():**
```python
# Automatically resolves constructor dependencies
class UserController:
    def __init__(self, db: Database, logger: Logger):
        self.db = db
        self.logger = logger

controller = container.build(UserController)
```

### 3. Lifetimes

**Singleton (default):**
```python
# Same instance returned every time
container.register(CacheService, singleton=True)
s1 = container.resolve(CacheService)
s2 = container.resolve(CacheService)
# s1 is s2 == True
```

**Transient:**
```python
# New instance created every time
container.register(RequestHandler, singleton=False)
r1 = container.resolve(RequestHandler)
r2 = container.resolve(RequestHandler)
# r1 is r2 == False
```

### 4. Factory with Container Access

For dependencies that need other dependencies:

```python
container.register_factory(
    CachedWeatherRepository,
    factory=lambda c: CachedWeatherRepository(
        repository=c.resolve(APIWeatherRepository),
        cache_ttl=300
    ),
    singleton=True
)
```

---

## Usage Patterns

### Pattern 1: Protocol-Based Registration

Best practice for loose coupling:

```python
from protocols.weather_protocols import WeatherService
from utils.Weather import OpenWeatherMapService

# Register interface -> implementation
container.register(WeatherService, OpenWeatherMapService, singleton=True)

# Code depends on protocol, not concrete class
def get_weather_data(service: WeatherService, city: str):
    return service.get_weather(city)
```

### Pattern 2: Layered Dependencies

Repository pattern with multiple layers:

```python
# Layer 1: Weather Service with circuit breaker
container.register_factory(
    OpenWeatherMapService,
    factory=lambda c: OpenWeatherMapService(
        enable_circuit_breaker=True,
        failure_threshold=5
    ),
    singleton=True
)

# Layer 2: API Repository using service
container.register_factory(
    APIWeatherRepository,
    factory=lambda c: APIWeatherRepository(
        weather_service=c.resolve(OpenWeatherMapService)
    ),
    singleton=True
)

# Layer 3: Cached repository wrapping API repository
container.register_factory(
    CachedWeatherRepository,
    factory=lambda c: CachedWeatherRepository(
        repository=c.resolve(APIWeatherRepository),
        cache_ttl=300
    ),
    singleton=True
)
```

### Pattern 3: Configuration Injection

```python
from utils.config import Settings, settings

# Register configuration instance
container.register_instance(Settings, settings)

# Use in factory
container.register_factory(
    ApiClient,
    factory=lambda c: ApiClient(
        api_url=c.resolve(Settings).API_URL,
        timeout=c.resolve(Settings).TIMEOUT
    ),
    singleton=True
)
```

### Pattern 4: Conditional Registration

```python
from utils.config import settings

# Choose implementation based on environment
if settings.USE_REDIS_CACHE:
    container.register(CacheService, RedisCacheService, singleton=True)
else:
    container.register(CacheService, InMemoryCacheService, singleton=True)
```

---

## FastAPI Integration

The DI Container integrates seamlessly with FastAPI's dependency injection system.

### Step 1: Configure Container at Startup

```python
# main.py
from fastapi import FastAPI
from utils.container import get_container
from utils.dependencies import configure_container

app = FastAPI()

# Configure container on startup
container = get_container()
configure_container(container)
```

### Step 2: Create Dependency Functions

```python
# utils/dependencies.py
from utils.container import get_container
from repositories.weather_repository import CachedWeatherRepository

def get_weather_repository() -> CachedWeatherRepository:
    """FastAPI dependency function."""
    container = get_container()
    return container.resolve(CachedWeatherRepository)
```

### Step 3: Use in Endpoints

```python
# main.py
from fastapi import Depends
from utils.dependencies import get_weather_repository

@app.get("/weather/{city}")
async def get_weather(
    city: str,
    repository: CachedWeatherRepository = Depends(get_weather_repository)
):
    data = repository.get_by_city(city)
    return {"data": data}
```

### Benefits of This Integration

1. **Type Safety**: Full IDE autocomplete and type checking
2. **Clear Dependencies**: Function signature shows what's needed
3. **Easy Testing**: Override dependencies with `app.dependency_overrides`
4. **Automatic Injection**: FastAPI handles calling dependency functions
5. **Request Scoping**: Each request gets correct instances

### Testing FastAPI with DI Container

```python
from fastapi.testclient import TestClient

def test_weather_endpoint():
    # Create mock repository
    class MockWeatherRepository:
        def get_by_city(self, city, country=None):
            return {"city": city, "temp": 25, "mock": True}

    # Override dependency
    app.dependency_overrides[get_weather_repository] = lambda: MockWeatherRepository()

    # Test
    client = TestClient(app)
    response = client.get("/weather/Madrid")

    assert response.status_code == 200
    assert response.json()["data"]["mock"] == True
```

---

## Testing

### Unit Testing Services

```python
import pytest
from utils.container import SimpleDIContainer

def test_weather_service():
    # Create test container
    container = SimpleDIContainer()

    # Register mock dependencies
    class MockApiClient:
        def fetch(self, url):
            return {"temp": 20}

    container.register(ApiClient, MockApiClient, singleton=True)

    # Register service under test
    container.register_factory(
        WeatherService,
        factory=lambda c: WeatherService(client=c.resolve(ApiClient)),
        singleton=True
    )

    # Test
    service = container.resolve(WeatherService)
    result = service.get_weather("Madrid")

    assert result["temp"] == 20
```

### Integration Testing

```python
def test_full_weather_stack():
    """Test entire weather service stack with real implementations."""
    from utils.dependencies import configure_container

    container = SimpleDIContainer()
    configure_container(container)

    # Resolve top-level service
    weather_repo = container.resolve(CachedWeatherRepository)

    # Test that all layers work together
    # (this will make real API calls unless you mock at a lower level)
    data = weather_repo.get_by_city("Madrid", "ES")

    assert data is not None
    assert "main" in data
    assert "temp" in data["main"]
```

### Mocking Strategies

**Strategy 1: Mock at the lowest level (API client)**
```python
# Mocks actual HTTP calls
container.register(HttpClient, MockHttpClient, singleton=True)
```

**Strategy 2: Mock at service level**
```python
# Mocks business logic
container.register(WeatherService, MockWeatherService, singleton=True)
```

**Strategy 3: Mock at repository level**
```python
# Mocks data access
container.register(WeatherRepository, MockWeatherRepository, singleton=True)
```

---

## Best Practices

### 1. Use Protocols for Abstractions

✅ **Good:**
```python
from protocols.weather_protocols import WeatherService

container.register(WeatherService, OpenWeatherMapService, singleton=True)
```

❌ **Avoid:**
```python
container.register(OpenWeatherMapService, singleton=True)
# No abstraction - tightly coupled
```

### 2. Centralize Configuration

Keep all registrations in `utils/dependencies.py`:

```python
def configure_container(container: SimpleDIContainer) -> None:
    """Single place for all dependency configuration."""
    # Configuration
    container.register_instance(Settings, settings)

    # Services
    container.register(WeatherService, OpenWeatherMapService, singleton=True)

    # Repositories
    container.register_factory(
        CachedWeatherRepository,
        factory=lambda c: CachedWeatherRepository(
            repository=c.resolve(APIWeatherRepository)
        ),
        singleton=True
    )
```

### 3. Use Singletons by Default

Most services should be singletons:

```python
# ✅ Good for: Services, repositories, clients, caches
container.register(WeatherService, singleton=True)

# ⚠️ Only use transient for: Request handlers, temporary objects
container.register(RequestHandler, singleton=False)
```

### 4. Use Factory Functions for Complex Init

```python
# ✅ Good: Factory handles complex initialization
container.register_factory(
    WeatherService,
    factory=lambda c: OpenWeatherMapService(
        api_key=c.resolve(Settings).OPENWEATHER_API_KEY,
        enable_circuit_breaker=True,
        failure_threshold=5,
        recovery_timeout=60.0
    ),
    singleton=True
)

# ❌ Avoid: Complex logic at registration time
service = OpenWeatherMapService(...)
container.register_instance(WeatherService, service)
```

### 5. Avoid Circular Dependencies

❌ **Bad:**
```python
class ServiceA:
    def __init__(self, service_b: ServiceB):
        self.service_b = service_b

class ServiceB:
    def __init__(self, service_a: ServiceA):
        self.service_a = service_a
# Circular dependency!
```

✅ **Good:**
```python
# Extract shared logic to a third service
class SharedService:
    pass

class ServiceA:
    def __init__(self, shared: SharedService):
        self.shared = shared

class ServiceB:
    def __init__(self, shared: SharedService):
        self.shared = shared
```

### 6. Use Type Hints Everywhere

```python
# ✅ Good: Full type hints
def get_weather_repository() -> CachedWeatherRepository:
    container = get_container()
    return container.resolve(CachedWeatherRepository)

# ❌ Bad: No type hints
def get_weather_repository():
    return get_container().resolve(CachedWeatherRepository)
```

### 7. Register Interfaces, Not Implementations

```python
# ✅ Good: Register using protocol
container.register(WeatherService, OpenWeatherMapService, singleton=True)
service = container.resolve(WeatherService)  # Resolve using protocol

# ❌ Avoid: Register concrete class directly
container.register(OpenWeatherMapService, singleton=True)
service = container.resolve(OpenWeatherMapService)  # Tightly coupled
```

---

## API Reference

### SimpleDIContainer

#### `__init__()`

Creates a new container instance.

```python
container = SimpleDIContainer()
```

#### `register(interface, implementation=None, factory=None, singleton=True)`

Register a dependency.

**Parameters:**
- `interface` (Type[T]): The interface/type to register
- `implementation` (Optional[Type[T]]): The concrete implementation class
- `factory` (Optional[Callable[[], T]]): Factory function to create instances
- `singleton` (bool): Whether to cache instances (default: True)

**Returns:** Self for method chaining

**Example:**
```python
container.register(WeatherService, OpenWeatherMapService, singleton=True)
```

#### `register_factory(interface, factory, singleton=True)`

Register a factory function that receives the container.

**Parameters:**
- `interface` (Type[T]): The interface/type to register
- `factory` (Callable[[SimpleDIContainer], T]): Factory receiving container
- `singleton` (bool): Whether to cache instances (default: True)

**Returns:** Self for method chaining

**Example:**
```python
container.register_factory(
    ApiClient,
    factory=lambda c: ApiClient(config=c.resolve(Config)),
    singleton=True
)
```

#### `register_instance(interface, instance)`

Register a pre-created instance.

**Parameters:**
- `interface` (Type[T]): The interface/type to register
- `instance` (T): The pre-created instance

**Returns:** Self for method chaining

**Example:**
```python
settings = Settings()
container.register_instance(Settings, settings)
```

#### `resolve(interface)`

Resolve and return an instance of the requested type.

**Parameters:**
- `interface` (Type[T]): The interface/type to resolve

**Returns:** Instance of the requested type

**Raises:**
- `KeyError`: If the type is not registered
- `Exception`: If instance creation fails

**Example:**
```python
service = container.resolve(WeatherService)
```

#### `build(cls)`

Build an instance with automatic dependency resolution.

**Parameters:**
- `cls` (Type[T]): The class to instantiate

**Returns:** Instance with resolved dependencies

**Example:**
```python
class Controller:
    def __init__(self, service: WeatherService, logger: Logger):
        ...

controller = container.build(Controller)
```

#### `is_registered(interface)`

Check if a type is registered.

**Parameters:**
- `interface` (Type[T]): The interface/type to check

**Returns:** bool

**Example:**
```python
if container.is_registered(WeatherService):
    service = container.resolve(WeatherService)
```

#### `get_registrations()`

Get all current registrations.

**Returns:** dict[Type, dict[str, Any]]

**Example:**
```python
registrations = container.get_registrations()
for service_type, info in registrations.items():
    print(f"{service_type.__name__}: singleton={info['singleton']}")
```

#### `clear()`

Clear all registrations and cached instances.

**Example:**
```python
container.clear()
```

### Global Functions

#### `get_container()`

Get the global DI container instance (singleton).

**Returns:** SimpleDIContainer

**Example:**
```python
from utils.container import get_container

container = get_container()
```

#### `reset_container()`

Reset the global container. Useful for testing.

**Example:**
```python
from utils.container import reset_container

reset_container()  # Clears and recreates global container
```

---

## Troubleshooting

### Issue: "Type X is not registered"

**Error:**
```
KeyError: Type WeatherService is not registered
```

**Solution:**
1. Check that `configure_container()` was called
2. Verify the type is registered in `utils/dependencies.py`
3. Make sure you're using the correct protocol/interface type

```python
# ✅ Correct
container.resolve(WeatherService)  # Protocol

# ❌ Wrong
container.resolve(OpenWeatherMapService)  # Implementation
```

### Issue: Circular Dependencies

**Error:**
```
RecursionError: maximum recursion depth exceeded
```

**Solution:**
Refactor to eliminate circular dependencies:
```python
# Instead of A -> B -> A
# Use: A -> C, B -> C (shared dependency)
```

### Issue: Singleton Not Working

**Problem:** Getting different instances when expecting the same one.

**Solution:**
Check that `singleton=True`:
```python
container.register(Service, singleton=True)  # Not False
```

### Issue: Factory Not Receiving Container

**Problem:** Factory function fails with missing container parameter.

**Solution:**
Use `register_factory()` instead of `register()`:
```python
# ✅ Correct
container.register_factory(
    Service,
    factory=lambda c: Service(config=c.resolve(Config)),
    singleton=True
)

# ❌ Wrong
container.register(
    Service,
    factory=lambda c: Service(config=c.resolve(Config)),  # c is not defined!
    singleton=True
)
```

### Issue: Type Hints Not Working

**Problem:** IDE doesn't autocomplete or type check.

**Solution:**
Always use explicit return types:
```python
# ✅ Good
def get_service() -> WeatherService:
    return container.resolve(WeatherService)

# ❌ Bad
def get_service():
    return container.resolve(WeatherService)
```

### Issue: Tests Affecting Each Other

**Problem:** Tests interfere due to shared global container.

**Solution:**
Reset container between tests:
```python
import pytest
from utils.container import reset_container

@pytest.fixture(autouse=True)
def reset_di_container():
    reset_container()
    yield
    reset_container()
```

---

## Additional Resources

- **Examples**: See `examples/di_container_examples.py` for 14 detailed usage examples
- **Protocol Definitions**: See `protocols/container_protocols.py`
- **Implementation**: See `utils/container.py`
- **Configuration**: See `utils/dependencies.py`
- **Tests**: See `tests/test_container.py`

---

## Summary

The Dependency Injection Container provides:

✅ **Centralized dependency management**
✅ **Loose coupling via protocols**
✅ **Easy testing with mocks**
✅ **Automatic lifecycle management**
✅ **Type-safe dependency resolution**
✅ **Seamless FastAPI integration**

Follow the patterns and best practices in this guide to build maintainable, testable, and flexible applications.