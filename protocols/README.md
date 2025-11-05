# Protocols Documentation

This directory contains Protocol definitions (interfaces) for the OpenWeather MCP Server application. These protocols enable better type safety, testability, and extensibility.

## Overview

Protocols in Python (using `typing.Protocol`) provide structural subtyping, allowing different implementations to be used interchangeably as long as they satisfy the protocol's interface.

## Available Protocols

### 1. Authentication Protocols (`auth_protocols.py`)

#### `TokenValidator`
Interface for token validation implementations.

**Methods:**
- `validate_token(token: str) -> Optional[Dict]`: Validates a token and returns token information if valid

**Implementations:**
- `LocalTokenValidator` (utils/auth.py): Validates against a locally stored token

**Example Usage:**
```python
from protocols.auth_protocols import TokenValidator
from utils.auth import LocalTokenValidator

validator: TokenValidator = LocalTokenValidator()
result = validator.validate_token("my-token")
if result:
    print(f"Token valid: {result['type']}")
```

#### `TokenProvider`
Interface for token provisioning implementations.

**Methods:**
- `get_token() -> Optional[str]`: Retrieves or generates an authentication token

**Implementations:**
- `LocalTokenClient` (utils/auth.py): Retrieves a locally stored token

**Example Usage:**
```python
from protocols.auth_protocols import TokenProvider
from utils.auth import LocalTokenClient

provider: TokenProvider = LocalTokenClient()
token = provider.get_token()
```

### 2. Weather Service Protocol (`weather_protocols.py`)

#### `WeatherService`
Interface for weather service implementations.

**Methods:**
- `get_weather(city: str, country: Optional[str] = None) -> WeatherData`: Get weather by city/country
- `get_weather_by_coordinates(latitude: float, longitude: float) -> WeatherData`: Get weather by coordinates

**Implementations:**
- `OpenWeatherMapService` (utils/Weather.py): OpenWeatherMap API implementation

**Example Usage:**
```python
from protocols.weather_protocols import WeatherService
from utils.Weather import OpenWeatherMapService

service: WeatherService = OpenWeatherMapService()
weather = service.get_weather("Madrid", "ES")
print(f"Temperature: {weather.main['temp']}°C")

# Using coordinates
weather = service.get_weather_by_coordinates(40.4168, -3.7038)
```

### 3. Configuration Protocol (`config_protocols.py`)

#### `ConfigProvider`
Interface for configuration provider implementations.

**Methods:**
- `get(key: str, default: Any = None) -> Any`: Get any configuration value
- `get_string(key: str, default: str = "") -> str`: Get configuration as string
- `get_int(key: str, default: int = 0) -> int`: Get configuration as integer
- `get_bool(key: str, default: bool = False) -> bool`: Get configuration as boolean
- `validate() -> None`: Validate required configuration values are present

**Implementations:**
- `Settings` (utils/config.py): Environment-based configuration provider

**Example Usage:**
```python
from protocols.config_protocols import ConfigProvider
from utils.config import Settings

config: ConfigProvider = Settings
port = config.get_int('PORT', 8000)
debug = config.get_bool('DEBUG', False)
config.validate()
```

#### `MutableConfigProvider`
Extends `ConfigProvider` with write capabilities.

**Additional Methods:**
- `set(key: str, value: Any) -> None`: Set a configuration value
- `reload() -> None`: Reload configuration from source

**Note:** Currently no implementations, but available for future use.

## Benefits of Using Protocols

1. **Type Safety**: Static type checkers (mypy, pyright) can verify that implementations satisfy the protocol
2. **Testability**: Easy to create mock implementations for testing
3. **Extensibility**: New implementations can be added without modifying existing code
4. **Documentation**: Protocols serve as clear contracts for what implementations must provide
5. **Flexibility**: Multiple implementations can be used interchangeably

## Adding New Implementations

To create a new implementation of a protocol:

1. Import the protocol
2. Create a class that implements all protocol methods
3. Optionally inherit from the protocol for explicit documentation

Example:
```python
from protocols.weather_protocols import WeatherService, WeatherData
from typing import Optional

class MockWeatherService(WeatherService):
    def get_weather(self, city: str, country: Optional[str] = None) -> WeatherData:
        # Return mock data for testing
        return WeatherData(
            coord={"lat": 0, "lon": 0},
            weather=[{"main": "Clear", "description": "clear sky"}],
            # ... other required fields
        )

    def get_weather_by_coordinates(self, latitude: float, longitude: float) -> WeatherData:
        # Return mock data for testing
        return self.get_weather("MockCity")
```

## Type Checking

To verify protocol compliance, use a static type checker:

```bash
# Using mypy
mypy utils/auth.py utils/Weather.py utils/config.py

# Using pyright
pyright utils/
```

## Testing with Protocols

Protocols make it easy to create test doubles:

```python
from protocols.auth_protocols import TokenValidator
from typing import Optional, Dict

class TestTokenValidator(TokenValidator):
    def __init__(self, should_validate: bool = True):
        self.should_validate = should_validate

    def validate_token(self, token: str) -> Optional[Dict]:
        if self.should_validate:
            return {"valid": True, "type": "test"}
        return None

# In tests
def test_authentication():
    validator = TestTokenValidator(should_validate=True)
    result = validator.validate_token("any-token")
    assert result is not None
```

## Future Enhancements

Potential new protocols to consider:

- **CacheProvider**: For different caching strategies (Redis, in-memory, etc.)
- **LoggerProtocol**: For different logging implementations
- **DatabaseProvider**: For different database backends
- **RateLimiterProtocol**: For different rate limiting strategies