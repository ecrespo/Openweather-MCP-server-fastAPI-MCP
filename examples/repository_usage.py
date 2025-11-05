"""
Example usage of Repository Pattern implementations.

This file demonstrates how to use the various repository implementations
without requiring a full application setup.
"""

from datetime import datetime, timedelta
from typing import Dict, Any


def example_inmemory_weather_repository():
    """Demonstrate InMemoryWeatherRepository usage."""
    print("\n=== InMemoryWeatherRepository Example ===\n")

    # This import requires app configuration, so we'll mock the structure
    # from repositories.weather_repository import InMemoryWeatherRepository

    # In practice, you would do:
    # repo = InMemoryWeatherRepository()

    # Mock weather data
    mock_weather = {
        "coord": {"lon": -3.7038, "lat": 40.4168},
        "weather": [{"main": "Clear", "description": "clear sky"}],
        "base": "stations",
        "main": {
            "temp": 20.5,
            "feels_like": 19.8,
            "temp_min": 18.0,
            "temp_max": 23.0,
            "pressure": 1013,
            "humidity": 65
        },
        "visibility": 10000,
        "wind": {"speed": 3.5, "deg": 180},
        "clouds": {"all": 0},
        "dt": 1609459200,
        "sys": {"country": "ES", "sunrise": 1609401600, "sunset": 1609438800},
        "timezone": 3600,
        "id": 3117735,
        "name": "Madrid",
        "cod": 200
    }

    print("1. Saving weather data:")
    print(f"   - City: {mock_weather['name']}")
    print(f"   - Temperature: {mock_weather['main']['temp']}°C")
    # repo.save(mock_weather)

    print("\n2. Retrieving weather data:")
    # weather = repo.get_by_city("Madrid", "ES")
    # print(f"   - Retrieved: {weather['name']}, {weather['main']['temp']}°C")

    print("\n3. Getting history:")
    # history = repo.get_history("Madrid", "ES", limit=5)
    # print(f"   - History entries: {len(history)}")


def example_cached_weather_repository():
    """Demonstrate CachedWeatherRepository usage."""
    print("\n=== CachedWeatherRepository Example ===\n")

    print("1. Initializing with 5-minute cache:")
    # from repositories.weather_repository import CachedWeatherRepository
    # repo = CachedWeatherRepository(cache_ttl=300)
    print("   - Cache TTL: 300 seconds")

    print("\n2. First request (cache miss):")
    # data = repo.get_by_city("Madrid", "ES")
    print("   - Fetched from API (~500ms)")

    print("\n3. Second request (cache hit):")
    # data = repo.get_by_city("Madrid", "ES")
    print("   - Retrieved from cache (~1ms)")

    print("\n4. Cache statistics:")
    # stats = repo.get_cache_stats()
    example_stats = {
        "total_entries": 5,
        "valid_entries": 4,
        "expired_entries": 1,
        "cache_ttl": 300,
        "history_locations": 3,
        "total_history_entries": 12
    }
    for key, value in example_stats.items():
        print(f"   - {key}: {value}")

    print("\n5. Clearing cache:")
    # repo.clear_cache()
    print("   - Cache cleared successfully")


def example_inmemory_token_repository():
    """Demonstrate InMemoryTokenRepository usage."""
    print("\n=== InMemoryTokenRepository Example ===\n")

    # from repositories.token_repository import InMemoryTokenRepository
    # repo = InMemoryTokenRepository()

    print("1. Saving a token:")
    token_data = {
        "token": "abc123xyz789",
        "type": "bearer",
        "created_at": datetime.now().isoformat(),
        "expires_at": (datetime.now() + timedelta(hours=1)).isoformat(),
        "metadata": {
            "user_id": "user123",
            "scopes": ["read", "write"]
        }
    }
    # repo.save("token-id-1", token_data)
    print(f"   - Token ID: token-id-1")
    print(f"   - Type: {token_data['type']}")
    print(f"   - Expires: {token_data['expires_at']}")

    print("\n2. Retrieving a token:")
    # token = repo.get("token-id-1")
    print(f"   - Token found: {token_data['token'][:10]}...")

    print("\n3. Checking if token exists:")
    # exists = repo.exists("token-id-1")
    print(f"   - Exists: True")

    print("\n4. Getting all active tokens:")
    # active_tokens = repo.get_all_active()
    print(f"   - Active tokens: 1")

    print("\n5. Repository statistics:")
    example_stats = {
        "total_tokens": 5,
        "active_tokens": 3,
        "expired_tokens": 2
    }
    for key, value in example_stats.items():
        print(f"   - {key}: {value}")

    print("\n6. Cleaning up expired tokens:")
    # removed = repo.cleanup_expired()
    print(f"   - Removed: 2 expired tokens")

    print("\n7. Deleting a token:")
    # repo.delete("token-id-1")
    print("   - Token deleted successfully")


def example_file_token_repository():
    """Demonstrate FileTokenRepository usage."""
    print("\n=== FileTokenRepository Example ===\n")

    print("1. Initializing with file storage:")
    # from repositories.token_repository import FileTokenRepository
    # repo = FileTokenRepository(file_path="./data/tokens.json")
    print("   - File: ./data/tokens.json")
    print("   - Directory created if not exists")

    print("\n2. Saving tokens (persisted to file):")
    token_data = {
        "token": "persistent-token-123",
        "type": "bearer",
        "expires_at": (datetime.now() + timedelta(days=7)).isoformat()
    }
    # repo.save("persistent-token-1", token_data)
    print("   - Token saved to file")

    print("\n3. Retrieving from file:")
    # token = repo.get("persistent-token-1")
    print("   - Token loaded from file")

    print("\n4. Reloading from disk:")
    # repo.reload()
    print("   - All tokens reloaded from file")
    print("   - Useful if file is modified externally")


def example_api_usage():
    """Demonstrate how repositories are used in API endpoints."""
    print("\n=== API Integration Example ===\n")

    print("FastAPI endpoint using repository:\n")
    print("""
@app.get("/weather/{city}/{country}")
async def weather(city: str, country: Optional[str] = None):
    # Use cached repository for better performance
    data = weather_repository.get_by_city(city, country)

    if data is None:
        raise HTTPException(status_code=404, detail="Weather not found")

    return ORJSONResponse(content=data)
    """)

    print("\nNew endpoints added:")
    print("  1. GET /weather/coordinates/{lat}/{lon}")
    print("     - Get weather by geographic coordinates")
    print("\n  2. GET /weather/history/{city}")
    print("     - Get historical weather queries")
    print("\n  3. GET /cache/stats")
    print("     - Get cache statistics")
    print("\n  4. POST /cache/clear")
    print("     - Clear the weather cache")


def example_testing():
    """Demonstrate how to use repositories in tests."""
    print("\n=== Testing Example ===\n")

    print("Unit test using InMemoryWeatherRepository:\n")
    print("""
def test_weather_endpoint():
    # Use in-memory repository for testing
    test_repo = InMemoryWeatherRepository()

    # Pre-populate with test data
    test_data = {
        "name": "TestCity",
        "main": {"temp": 25.0},
        "weather": [{"main": "Sunny"}]
    }
    test_repo.save(test_data)

    # Test retrieval
    result = test_repo.get_by_city("TestCity")
    assert result["main"]["temp"] == 25.0
    assert result["weather"][0]["main"] == "Sunny"
    """)

    print("\nIntegration test with cache:\n")
    print("""
def test_cache_behavior():
    repo = CachedWeatherRepository(cache_ttl=5)

    # First call - should hit API
    start = time.time()
    data1 = repo.get_by_city("Madrid", "ES")
    time1 = time.time() - start

    # Second call - should use cache
    start = time.time()
    data2 = repo.get_by_city("Madrid", "ES")
    time2 = time.time() - start

    assert time2 < time1  # Cache should be faster
    assert data1 == data2
    """)


def main():
    """Run all examples."""
    print("=" * 60)
    print("Repository Pattern - Usage Examples")
    print("=" * 60)

    example_inmemory_weather_repository()
    example_cached_weather_repository()
    example_inmemory_token_repository()
    example_file_token_repository()
    example_api_usage()
    example_testing()

    print("\n" + "=" * 60)
    print("For more information, see:")
    print("  - repositories/README.md")
    print("  - REPOSITORY_SUMMARY.md")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    main()