# OpenWeather MCP Server - Architecture Documentation

## Overview

This document describes the architectural patterns and design principles used in the OpenWeather MCP Server project, focusing on the implementation of Protocols/Interfaces and the Repository Pattern.

## Architectural Principles

1. **Separation of Concerns**: Business logic, data access, and presentation are separated
2. **Dependency Inversion**: High-level modules depend on abstractions, not concrete implementations
3. **Interface Segregation**: Small, focused interfaces rather than large, monolithic ones
4. **Single Responsibility**: Each component has one reason to change
5. **Open/Closed**: Open for extension, closed for modification

## Project Structure

```
openweather-mcp-server/
├── protocols/                    # Protocol definitions (interfaces)
│   ├── __init__.py
│   ├── auth_protocols.py        # TokenValidator, TokenProvider
│   ├── weather_protocols.py     # WeatherService
│   ├── config_protocols.py      # ConfigProvider, MutableConfigProvider
│   ├── repository_protocols.py  # WeatherRepository, TokenRepository, ConfigRepository
│   └── README.md
│
├── repositories/                 # Repository implementations
│   ├── __init__.py
│   ├── weather_repository.py    # API, Cached, InMemory implementations
│   ├── token_repository.py      # InMemory, File implementations
│   └── README.md
│
├── utils/                        # Utility modules
│   ├── __init__.py
│   ├── auth.py                  # LocalTokenValidator, LocalTokenClient
│   ├── Weather.py               # Weather dataclass, OpenWeatherMapService
│   ├── config.py                # Settings (ConfigProvider implementation)
│   └── logger.py                # Logging configuration
│
├── examples/                     # Usage examples
│   └── repository_usage.py
│
├── tests/                        # Test files
│   ├── test_main.py
│   └── test_Weather.py
│
├── main.py                       # FastAPI application
├── PROTOCOLS_SUMMARY.md          # Protocols documentation
├── REPOSITORY_SUMMARY.md         # Repository pattern documentation
└── ARCHITECTURE.md               # This file
```

## Layered Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     Presentation Layer                       │
│                     (FastAPI Endpoints)                      │
│                         main.py                              │
└──────────────────────────┬──────────────────────────────────┘
                           │
                           │ depends on
                           ▼
┌─────────────────────────────────────────────────────────────┐
│                   Business Logic Layer                       │
│              (Services, Validators, Providers)               │
│   OpenWeatherMapService, LocalTokenValidator, etc.          │
└──────────────────────────┬──────────────────────────────────┘
                           │
                           │ implements
                           ▼
┌─────────────────────────────────────────────────────────────┐
│                     Protocol Layer                           │
│                   (Abstract Interfaces)                      │
│   WeatherService, TokenValidator, WeatherRepository, etc.   │
└──────────────────────────┬──────────────────────────────────┘
                           │
                           │ used by
                           ▼
┌─────────────────────────────────────────────────────────────┐
│                   Data Access Layer                          │
│                   (Repository Implementations)               │
│   CachedWeatherRepository, FileTokenRepository, etc.        │
└──────────────────────────┬──────────────────────────────────┘
                           │
                           │ accesses
                           ▼
┌─────────────────────────────────────────────────────────────┐
│                     Data Sources                             │
│           (External APIs, Files, Databases, Cache)           │
│         OpenWeatherMap API, JSON Files, Memory               │
└─────────────────────────────────────────────────────────────┘
```

## Component Diagram

### Weather Data Flow

```
HTTP Request
    │
    ▼
┌─────────────────────────┐
│  FastAPI Endpoint       │
│  /weather/{city}        │
└───────────┬─────────────┘
            │
            │ calls
            ▼
┌─────────────────────────┐
│ CachedWeatherRepository │◄────implements──── WeatherRepository
└───────────┬─────────────┘                          Protocol
            │
            │ wraps
            ▼
┌─────────────────────────┐
│  APIWeatherRepository   │◄────implements──── WeatherRepository
└───────────┬─────────────┘                          Protocol
            │
            │ uses
            ▼
┌─────────────────────────┐
│ OpenWeatherMapService   │◄────implements──── WeatherService
└───────────┬─────────────┘                          Protocol
            │
            │ HTTP GET
            ▼
┌─────────────────────────┐
│  OpenWeatherMap API     │
│  api.openweathermap.org │
└─────────────────────────┘
```

### Authentication Flow

```
HTTP Request with Bearer Token
    │
    ▼
┌─────────────────────────┐
│  authenticate_request   │
│  (Dependency)           │
└───────────┬─────────────┘
            │
            │ uses
            ▼
┌─────────────────────────┐
│  LocalTokenValidator    │◄────implements──── TokenValidator
└───────────┬─────────────┘                          Protocol
            │
            │ validates against
            ▼
┌─────────────────────────┐
│  Settings               │◄────implements──── ConfigProvider
│  (LOCAL_TOKEN)          │                          Protocol
└─────────────────────────┘
```

### Repository Pattern with Caching

```
┌─────────────────────────────────────────────────────────────┐
│                        Client Code                           │
│                  (FastAPI Endpoint)                          │
└───────────────────────────┬─────────────────────────────────┘
                            │
                            │ get_by_city("Madrid", "ES")
                            ▼
┌─────────────────────────────────────────────────────────────┐
│              CachedWeatherRepository                         │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  1. Check cache                                      │   │
│  │     ├─ Hit? → Return cached data (1-5ms)            │   │
│  │     └─ Miss? → Proceed to step 2                    │   │
│  │                                                      │   │
│  │  2. Call underlying repository                      │   │
│  │     └─ APIWeatherRepository.get_by_city()           │   │
│  │                                                      │   │
│  │  3. Cache the result                                │   │
│  │     ├─ Store with timestamp                         │   │
│  │     └─ Add to history                               │   │
│  │                                                      │   │
│  │  4. Return data to client                           │   │
│  └──────────────────────────────────────────────────────┘   │
└───────────────────────────┬─────────────────────────────────┘
                            │
                            │ get_weather("Madrid", "ES")
                            ▼
┌─────────────────────────────────────────────────────────────┐
│               APIWeatherRepository                           │
│                         │                                    │
│                         │ get_weather("Madrid", "ES")        │
│                         ▼                                    │
│              OpenWeatherMapService                           │
│                         │                                    │
│                         │ HTTP GET                           │
│                         ▼                                    │
│              OpenWeatherMap API                              │
└─────────────────────────────────────────────────────────────┘
```

## Design Patterns Used

### 1. Protocol Pattern (Interface Segregation)

**Purpose**: Define contracts without coupling to implementations

**Example**:
```python
class WeatherService(Protocol):
    def get_weather(self, city: str, country: Optional[str] = None) -> WeatherData:
        ...

# Multiple implementations
class OpenWeatherMapService:  # Implements WeatherService
    def get_weather(self, city: str, country: Optional[str] = None) -> WeatherData:
        # OpenWeatherMap API implementation

class WeatherAPIService:  # Also implements WeatherService
    def get_weather(self, city: str, country: Optional[str] = None) -> WeatherData:
        # WeatherAPI.com implementation
```

### 2. Repository Pattern

**Purpose**: Abstract data access logic from business logic

**Benefits**:
- Centralized data access logic
- Easy to swap implementations
- Improved testability
- Caching transparency

**Example**:
```python
# Business logic doesn't care about caching or where data comes from
def get_weather_report(city: str, repo: WeatherRepository) -> dict:
    weather = repo.get_by_city(city)
    return {"city": city, "temp": weather["main"]["temp"]}

# Can use any repository implementation
cached_repo = CachedWeatherRepository()
memory_repo = InMemoryWeatherRepository()
```

### 3. Decorator Pattern (Caching)

**Purpose**: Add caching behavior to existing repository

**Example**:
```python
# CachedWeatherRepository wraps another repository
class CachedWeatherRepository:
    def __init__(self, repository: WeatherRepository):
        self.repository = repository  # Decorated repository
        self.cache = {}

    def get_by_city(self, city, country):
        if city in self.cache:
            return self.cache[city]  # Return cached

        data = self.repository.get_by_city(city, country)  # Delegate
        self.cache[city] = data  # Cache result
        return data
```

### 4. Strategy Pattern

**Purpose**: Select algorithm/implementation at runtime

**Example**:
```python
# Choose repository strategy based on environment
if ENV == "production":
    repo = CachedWeatherRepository(cache_ttl=600)
elif ENV == "testing":
    repo = InMemoryWeatherRepository()
else:
    repo = APIWeatherRepository()

# Use same interface regardless of strategy
weather = repo.get_by_city("Madrid", "ES")
```

### 5. Dependency Injection

**Purpose**: Inject dependencies rather than creating them internally

**Example**:
```python
# Bad: Hard-coded dependency
class WeatherService:
    def __init__(self):
        self.repo = CachedWeatherRepository()  # Hard-coded

# Good: Injected dependency
class WeatherService:
    def __init__(self, repo: WeatherRepository):
        self.repo = repo  # Injected, can be any implementation

# Usage
service = WeatherService(CachedWeatherRepository())
```

## Protocol Implementations Matrix

| Protocol | Implementations | Location |
|----------|----------------|----------|
| `TokenValidator` | `LocalTokenValidator` | `utils/auth.py` |
| `TokenProvider` | `LocalTokenClient` | `utils/auth.py` |
| `WeatherService` | `OpenWeatherMapService` | `utils/Weather.py` |
| `ConfigProvider` | `Settings` | `utils/config.py` |
| `WeatherRepository` | `APIWeatherRepository`<br>`CachedWeatherRepository`<br>`InMemoryWeatherRepository` | `repositories/weather_repository.py` |
| `TokenRepository` | `InMemoryTokenRepository`<br>`FileTokenRepository` | `repositories/token_repository.py` |
| `ConfigRepository` | _None yet_ | _Future implementation_ |

## Data Flow Scenarios

### Scenario 1: First Weather Request (Cache Miss)

```
1. Client → GET /weather/Madrid/ES
2. FastAPI Endpoint → weather_repository.get_by_city("Madrid", "ES")
3. CachedWeatherRepository:
   - Check cache: MISS
   - Call underlying repository
4. APIWeatherRepository.get_by_city("Madrid", "ES")
5. OpenWeatherMapService.get_weather("Madrid", "ES")
6. HTTP GET → api.openweathermap.org
7. Response: Weather data (500ms)
8. APIWeatherRepository → Return WeatherData
9. CachedWeatherRepository:
   - Cache the data with timestamp
   - Add to history
   - Return data
10. FastAPI → Return JSON response
```

### Scenario 2: Subsequent Weather Request (Cache Hit)

```
1. Client → GET /weather/Madrid/ES
2. FastAPI Endpoint → weather_repository.get_by_city("Madrid", "ES")
3. CachedWeatherRepository:
   - Check cache: HIT
   - Validate TTL: Valid
   - Return cached data (1ms)
4. FastAPI → Return JSON response
```

### Scenario 3: Token Validation

```
1. Client → GET /mcp/tools (with Bearer token)
2. FastAPI Dependency → authenticate_request()
3. LocalTokenValidator.validate_token(token)
4. Compare with Settings.LOCAL_TOKEN
5. Return validation result
6. If valid → Continue to endpoint
7. If invalid → Return 401 Unauthorized
```

## Performance Optimizations

### 1. Caching Layer
- **Without cache**: Every request = API call (~500ms)
- **With cache**: Cached requests = ~1-5ms
- **Impact**: 99% latency reduction, 80% fewer API calls

### 2. Thread Safety
- All repositories use locks for concurrent access
- Safe for multi-threaded FastAPI workers

### 3. TTL Management
- Configurable cache expiration
- Automatic cleanup of expired entries
- Balance between freshness and performance

### 4. History Tracking
- Limited to 50 entries per location
- Deque for O(1) append/pop operations
- Efficient memory usage

## Testing Strategy

### Unit Tests
```python
def test_inmemory_repository():
    repo = InMemoryWeatherRepository()
    repo.save(test_data)
    result = repo.get_by_city("TestCity")
    assert result == test_data
```

### Integration Tests
```python
def test_cached_repository_with_api():
    repo = CachedWeatherRepository()
    data1 = repo.get_by_city("Madrid", "ES")
    data2 = repo.get_by_city("Madrid", "ES")
    assert data1 == data2  # Second call uses cache
```

### Mock Testing
```python
class MockWeatherRepository:
    def get_by_city(self, city, country):
        return {"name": city, "main": {"temp": 20}}

def test_endpoint_with_mock():
    app.dependency_overrides[get_repo] = lambda: MockWeatherRepository()
    response = client.get("/weather/Madrid/ES")
    assert response.status_code == 200
```

## Security Considerations

1. **Token Validation**: All MCP endpoints require valid Bearer token
2. **Input Validation**: FastAPI validates all input parameters
3. **Rate Limiting**: slowapi limits requests per client
4. **Error Handling**: Sensitive info not exposed in error messages
5. **Environment Variables**: Secrets stored in .env, not in code

## Scalability Considerations

### Current Design (Single Instance)
- In-memory caching works well
- File-based token storage acceptable
- Handles moderate traffic

### Future Scaling Options
1. **Redis Cache**: Replace in-memory cache with Redis
2. **Database**: Store weather history in PostgreSQL
3. **Message Queue**: Async weather data updates
4. **Load Balancer**: Multiple app instances
5. **CDN**: Cache static responses

## Monitoring and Observability

### Available Metrics
- `GET /cache/stats`: Cache performance metrics
- Repository operation logging
- Request/response logging via logger module

### Recommended Additions
1. Prometheus metrics endpoint
2. Application Performance Monitoring (APM)
3. Distributed tracing
4. Health check endpoints
5. Custom business metrics

## Future Enhancements

### Short Term
1. Add database repository implementations
2. Implement ConfigRepository
3. Add more weather service providers
4. Enhanced error recovery

### Long Term
1. GraphQL API alongside REST
2. WebSocket support for real-time updates
3. Machine learning for weather predictions
4. Multi-region deployment
5. Microservices architecture

## Conclusion

The architecture follows SOLID principles and uses proven design patterns to create a maintainable, testable, and scalable application. The combination of Protocols and Repository Pattern provides flexibility while maintaining type safety and clear separation of concerns.

## References

- [Repository Pattern](https://martinfowler.com/eaaCatalog/repository.html)
- [Python Protocols (PEP 544)](https://peps.python.org/pep-0544/)
- [SOLID Principles](https://en.wikipedia.org/wiki/SOLID)
- [FastAPI Best Practices](https://fastapi.tiangolo.com/tutorial/)
