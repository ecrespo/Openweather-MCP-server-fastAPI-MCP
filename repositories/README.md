# Repository Pattern Implementation

This directory contains implementations of the Repository pattern, providing abstraction layers for data access operations throughout the application.

## Overview

The Repository pattern mediates between the domain and data mapping layers, acting like an in-memory collection of domain objects. It provides a more object-oriented view of the persistence layer and separates the business logic from data access concerns.

## Benefits

1. **Separation of Concerns**: Business logic is decoupled from data access logic
2. **Testability**: Easy to mock repositories for unit testing
3. **Flexibility**: Can swap implementations without changing business logic
4. **Centralized Data Logic**: All data access code in one place
5. **Caching**: Easy to add caching layers transparently
6. **Multiple Data Sources**: Abstract away whether data comes from API, database, cache, etc.

## Available Repositories

### 1. Weather Repositories (`weather_repository.py`)

#### `APIWeatherRepository`
Fetches weather data directly from the OpenWeatherMap API without any caching.

**Use Cases:**
- Real-time weather data requirements
- Testing without cache interference
- Single requests where caching isn't beneficial

**Example:**
```python
from repositories.weather_repository import APIWeatherRepository

repo = APIWeatherRepository()
weather = repo.get_by_city("Madrid", "ES")
```

#### `CachedWeatherRepository`
Wraps another repository (typically APIWeatherRepository) and adds caching functionality.

**Features:**
- Configurable TTL (Time-To-Live) for cache entries
- Thread-safe cache operations
- Historical data tracking
- Cache statistics

**Use Cases:**
- Production deployments to reduce API calls
- Improving response times
- Tracking weather history for a location

**Example:**
```python
from repositories.weather_repository import CachedWeatherRepository

# 5-minute cache
repo = CachedWeatherRepository(cache_ttl=300)
weather = repo.get_by_city("Madrid", "ES")  # Fetches from API
weather = repo.get_by_city("Madrid", "ES")  # Returns from cache

# Get cache statistics
stats = repo.get_cache_stats()
print(f"Cache has {stats['valid_entries']} valid entries")

# Get historical data
history = repo.get_history("Madrid", "ES", limit=10)

# Clear cache
repo.clear_cache()
```

#### `InMemoryWeatherRepository`
Stores weather data entirely in memory without external dependencies.

**Use Cases:**
- Unit testing
- Development/debugging
- Mock data scenarios

**Example:**
```python
from repositories.weather_repository import InMemoryWeatherRepository

repo = InMemoryWeatherRepository()

# Save mock data
mock_data = {
    "name": "Madrid",
    "sys": {"country": "ES"},
    "main": {"temp": 20},
    # ... other fields
}
repo.save(mock_data)

# Retrieve it
weather = repo.get_by_city("Madrid", "ES")
```

### 2. Token Repositories (`token_repository.py`)

#### `InMemoryTokenRepository`
Stores authentication tokens in memory.

**Features:**
- Thread-safe operations
- Automatic expiration checking
- Cleanup of expired tokens
- Token statistics

**Use Cases:**
- Development environments
- Single-process deployments
- Testing
- Temporary token storage

**Example:**
```python
from repositories.token_repository import InMemoryTokenRepository
from datetime import datetime, timedelta

repo = InMemoryTokenRepository()

# Save a token
token_data = {
    "token": "abc123",
    "type": "bearer",
    "expires_at": (datetime.now() + timedelta(hours=1)).isoformat()
}
repo.save("token-id-1", token_data)

# Retrieve token
token = repo.get("token-id-1")

# Check if token exists
exists = repo.exists("token-id-1")

# Get all active tokens
active = repo.get_all_active()

# Cleanup expired tokens
removed = repo.cleanup_expired()

# Delete a token
repo.delete("token-id-1")
```

#### `FileTokenRepository`
Persists tokens to a JSON file for durability across restarts.

**Features:**
- File-based persistence
- Automatic directory creation
- Same interface as InMemoryTokenRepository
- Thread-safe file operations

**Use Cases:**
- Production environments
- Multi-instance deployments (with shared file system)
- Token persistence across restarts

**Example:**
```python
from repositories.token_repository import FileTokenRepository

repo = FileTokenRepository(file_path="./data/tokens.json")

# Operations are the same as InMemoryTokenRepository
repo.save("token-id-1", token_data)
token = repo.get("token-id-1")

# Reload from file (useful if file is modified externally)
repo.reload()
```

## Integration with Main Application

The repositories are integrated into `main.py`:

```python
from repositories.weather_repository import CachedWeatherRepository

# Initialize repository
weather_repository = CachedWeatherRepository(cache_ttl=300)

# Use in endpoints
@app.get("/weather/{city}/{country}")
async def weather(city: str, country: Optional[str] = None):
    data = weather_repository.get_by_city(city, country)
    return data
```

## New API Endpoints

The following endpoints have been added to leverage repository capabilities:

### Weather Endpoints

#### `GET /weather/{city}/{country}`
Get weather for a city with caching.

#### `GET /weather/coordinates/{latitude}/{longitude}`
Get weather by geographic coordinates.

#### `GET /weather/history/{city}?country={country}&limit={limit}`
Get historical weather data for a city.

**Query Parameters:**
- `country` (optional): Country code
- `limit` (optional): Number of records (default: 10)

### Cache Management Endpoints

#### `GET /cache/stats`
Get cache statistics.

**Response:**
```json
{
  "total_entries": 15,
  "valid_entries": 12,
  "expired_entries": 3,
  "cache_ttl": 300,
  "history_locations": 8,
  "total_history_entries": 45
}
```

#### `POST /cache/clear`
Clear the weather data cache.

## Testing with Repositories

Repositories make testing much easier:

```python
import pytest
from repositories.weather_repository import InMemoryWeatherRepository

@pytest.fixture
def weather_repo():
    return InMemoryWeatherRepository()

def test_weather_retrieval(weather_repo):
    # Save test data
    test_data = {"name": "TestCity", "main": {"temp": 25}}
    weather_repo.save(test_data)

    # Retrieve and verify
    result = weather_repo.get_by_city("TestCity")
    assert result["main"]["temp"] == 25
```

## Extending Repositories

To create a new repository implementation:

1. **Define the interface** in `protocols/repository_protocols.py` (if not exists)
2. **Create the implementation** in this directory
3. **Follow the protocol** methods exactly
4. **Add to `__init__.py`** for easy imports

Example - Redis Weather Repository:

```python
from protocols.repository_protocols import WeatherRepository
import redis

class RedisWeatherRepository:
    """Weather repository using Redis for caching."""

    def __init__(self, redis_client):
        self.redis = redis_client

    def get_by_city(self, city: str, country: Optional[str] = None):
        key = f"weather:{city}:{country or 'none'}"
        data = self.redis.get(key)
        if data:
            return json.loads(data)
        return None

    def save(self, weather_data: Dict[str, Any]) -> bool:
        # Implementation...
        pass

    # ... other methods
```

## Performance Considerations

### Caching Strategy

The `CachedWeatherRepository` uses a simple TTL-based caching strategy:

- **Default TTL**: 300 seconds (5 minutes)
- **Thread-safe**: Uses locks for concurrent access
- **Memory efficient**: Stores only cached data and recent history

### Optimization Tips

1. **Adjust TTL**: Balance between freshness and API call reduction
2. **Monitor cache stats**: Use `/cache/stats` to optimize
3. **Clear stale data**: Periodically call `clear_cache()` if needed
4. **Use coordinates**: More precise and often cached better

## Best Practices

1. **Dependency Injection**: Pass repositories to functions/classes rather than creating them inside
2. **Interface over Implementation**: Type hint with protocols, not concrete classes
3. **Error Handling**: Always handle None returns from repositories
4. **Logging**: Use the provided logger for repository operations
5. **Testing**: Use InMemory repositories for unit tests
6. **Production**: Use Cached or File-based repositories for persistence

## Configuration

Repository behavior can be configured:

```python
# Long cache TTL for stable data
weather_repo = CachedWeatherRepository(cache_ttl=3600)  # 1 hour

# Custom file location for tokens
token_repo = FileTokenRepository(file_path="/var/data/tokens.json")

# No caching (direct API)
weather_repo = APIWeatherRepository()
```

## Future Enhancements

Potential improvements:

1. **Database Repository**: Persist weather data to PostgreSQL/MongoDB
2. **Redis Repository**: Distributed caching with Redis
3. **Composite Repository**: Combine multiple repositories with fallback
4. **Query Builder**: More complex query capabilities
5. **Event System**: Emit events on data changes
6. **Metrics**: Detailed metrics collection and reporting