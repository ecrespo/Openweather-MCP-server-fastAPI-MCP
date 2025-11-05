"""
Weather Repository Implementations.

This module provides concrete implementations of the WeatherRepository protocol,
offering different strategies for weather data access and storage.
"""

from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from collections import deque
import threading

from utils.Weather import OpenWeatherMapService
from utils.logger import log


class APIWeatherRepository:
    """
    Weather repository that fetches data from OpenWeatherMap API.

    This implementation delegates to OpenWeatherMapService for real-time
    weather data retrieval. It does not cache or persist data.

    Implements the WeatherRepository protocol.

    :ivar weather_service: The weather service used for API calls
    :type weather_service: OpenWeatherMapService
    """

    def __init__(self, weather_service: Optional[OpenWeatherMapService] = None):
        """
        Initialize the API weather repository.

        Args:
            weather_service: Optional weather service. If not provided,
                           creates a new OpenWeatherMapService instance
        """
        self.weather_service = weather_service or OpenWeatherMapService()
        log.info("APIWeatherRepository initialized")

    def get_by_city(self, city: str, country: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        Retrieves weather data for a city from the API.

        Args:
            city: Name of the city
            country: Optional country code

        Returns:
            Dictionary containing weather data if successful, None otherwise
        """
        try:
            weather = self.weather_service.get_weather(city, country)
            return weather.__dict__
        except Exception as e:
            log.error(f"Error retrieving weather for {city}: {e}")
            return None

    def get_by_coordinates(self, latitude: float, longitude: float) -> Optional[Dict[str, Any]]:
        """
        Retrieves weather data for coordinates from the API.

        Args:
            latitude: Latitude coordinate
            longitude: Longitude coordinate

        Returns:
            Dictionary containing weather data if successful, None otherwise
        """
        try:
            weather = self.weather_service.get_weather_by_coordinates(latitude, longitude)
            return weather.__dict__
        except Exception as e:
            log.error(f"Error retrieving weather for coordinates ({latitude}, {longitude}): {e}")
            return None

    def save(self, weather_data: Dict[str, Any]) -> bool:
        """
        Save operation not supported for API-only repository.

        Args:
            weather_data: Weather data to save

        Returns:
            False (operation not supported)
        """
        log.warning("Save operation not supported in APIWeatherRepository")
        return False

    def get_history(
        self,
        city: str,
        country: Optional[str] = None,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        History not available in API-only repository.

        Args:
            city: Name of the city
            country: Optional country code
            limit: Maximum number of records

        Returns:
            Empty list (history not available)
        """
        log.warning("History not available in APIWeatherRepository")
        return []

    def clear_cache(self) -> None:
        """No cache to clear in API-only repository."""
        pass


class CachedWeatherRepository:
    """
    Weather repository with caching capabilities.

    This implementation wraps another WeatherRepository and adds caching
    functionality to reduce API calls and improve performance.

    Implements the WeatherRepository protocol.

    :ivar repository: The underlying repository to wrap
    :ivar cache: Dictionary storing cached weather data
    :ivar cache_ttl: Time-to-live for cached entries in seconds
    :ivar cache_lock: Thread lock for cache operations
    """

    def __init__(
        self,
        repository: Optional['APIWeatherRepository'] = None,
        cache_ttl: int = 300  # 5 minutes default
    ):
        """
        Initialize the cached weather repository.

        Args:
            repository: Underlying repository to wrap. If not provided,
                       creates a new APIWeatherRepository
            cache_ttl: Cache time-to-live in seconds (default: 300)
        """
        self.repository = repository or APIWeatherRepository()
        self.cache: Dict[str, Dict[str, Any]] = {}
        self.cache_ttl = cache_ttl
        self.cache_lock = threading.Lock()
        self.history_store: Dict[str, deque] = {}
        self.max_history_per_location = 50
        log.info(f"CachedWeatherRepository initialized with TTL={cache_ttl}s")

    def _get_cache_key(self, city: str, country: Optional[str] = None) -> str:
        """Generate a cache key for city/country combination."""
        return f"{city}_{country or 'none'}".lower()

    def _get_coord_cache_key(self, latitude: float, longitude: float) -> str:
        """Generate a cache key for coordinates."""
        return f"coord_{latitude}_{longitude}"

    def _is_cache_valid(self, cache_entry: Dict[str, Any]) -> bool:
        """Check if a cache entry is still valid."""
        if 'cached_at' not in cache_entry:
            return False
        cached_at = cache_entry['cached_at']
        age = (datetime.now() - cached_at).total_seconds()
        return age < self.cache_ttl

    def get_by_city(self, city: str, country: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        Retrieves weather data for a city, using cache when available.

        Args:
            city: Name of the city
            country: Optional country code

        Returns:
            Dictionary containing weather data if successful, None otherwise
        """
        cache_key = self._get_cache_key(city, country)

        with self.cache_lock:
            # Check cache first
            if cache_key in self.cache:
                cache_entry = self.cache[cache_key]
                if self._is_cache_valid(cache_entry):
                    log.debug(f"Cache hit for {city}")
                    return cache_entry['data']
                else:
                    log.debug(f"Cache expired for {city}")
                    del self.cache[cache_key]

        # Cache miss or expired - fetch from repository
        log.debug(f"Cache miss for {city}, fetching from repository")
        data = self.repository.get_by_city(city, country)

        if data:
            with self.cache_lock:
                # Cache the result
                self.cache[cache_key] = {
                    'data': data,
                    'cached_at': datetime.now()
                }
                # Add to history
                if cache_key not in self.history_store:
                    self.history_store[cache_key] = deque(maxlen=self.max_history_per_location)

                history_entry = data.copy()
                history_entry['retrieved_at'] = datetime.now().isoformat()
                self.history_store[cache_key].append(history_entry)

        return data

    def get_by_coordinates(self, latitude: float, longitude: float) -> Optional[Dict[str, Any]]:
        """
        Retrieves weather data for coordinates, using cache when available.

        Args:
            latitude: Latitude coordinate
            longitude: Longitude coordinate

        Returns:
            Dictionary containing weather data if successful, None otherwise
        """
        cache_key = self._get_coord_cache_key(latitude, longitude)

        with self.cache_lock:
            # Check cache first
            if cache_key in self.cache:
                cache_entry = self.cache[cache_key]
                if self._is_cache_valid(cache_entry):
                    log.debug(f"Cache hit for coordinates ({latitude}, {longitude})")
                    return cache_entry['data']
                else:
                    log.debug(f"Cache expired for coordinates ({latitude}, {longitude})")
                    del self.cache[cache_key]

        # Cache miss or expired - fetch from repository
        data = self.repository.get_by_coordinates(latitude, longitude)

        if data:
            with self.cache_lock:
                # Cache the result
                self.cache[cache_key] = {
                    'data': data,
                    'cached_at': datetime.now()
                }

        return data

    def save(self, weather_data: Dict[str, Any]) -> bool:
        """
        Saves weather data (delegates to underlying repository).

        Args:
            weather_data: Weather data to save

        Returns:
            True if saved successfully, False otherwise
        """
        return self.repository.save(weather_data)

    def get_history(
        self,
        city: str,
        country: Optional[str] = None,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Retrieves historical weather data for a location.

        Args:
            city: Name of the city
            country: Optional country code
            limit: Maximum number of historical records

        Returns:
            List of weather data dictionaries, newest first
        """
        cache_key = self._get_cache_key(city, country)

        with self.cache_lock:
            if cache_key in self.history_store:
                # Return most recent entries first
                history = list(self.history_store[cache_key])
                history.reverse()
                return history[:limit]

        return []

    def clear_cache(self) -> None:
        """Clears all cached data."""
        with self.cache_lock:
            cache_size = len(self.cache)
            self.cache.clear()
            log.info(f"Cleared {cache_size} cache entries")

    def get_cache_stats(self) -> Dict[str, Any]:
        """
        Get statistics about the cache.

        Returns:
            Dictionary with cache statistics
        """
        with self.cache_lock:
            total_entries = len(self.cache)
            valid_entries = sum(1 for entry in self.cache.values() if self._is_cache_valid(entry))

            return {
                'total_entries': total_entries,
                'valid_entries': valid_entries,
                'expired_entries': total_entries - valid_entries,
                'cache_ttl': self.cache_ttl,
                'history_locations': len(self.history_store),
                'total_history_entries': sum(len(h) for h in self.history_store.values())
            }


class InMemoryWeatherRepository:
    """
    In-memory weather repository for testing purposes.

    This implementation stores weather data in memory without any external
    dependencies, making it ideal for unit testing.

    Implements the WeatherRepository protocol.

    :ivar storage: Dictionary storing weather data
    :ivar history: Dictionary storing historical weather data
    """

    def __init__(self):
        """Initialize the in-memory weather repository."""
        self.storage: Dict[str, Dict[str, Any]] = {}
        self.history: Dict[str, List[Dict[str, Any]]] = {}
        log.info("InMemoryWeatherRepository initialized")

    def _get_key(self, city: str, country: Optional[str] = None) -> str:
        """Generate a storage key for city/country combination."""
        return f"{city}_{country or 'none'}".lower()

    def get_by_city(self, city: str, country: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        Retrieves weather data for a city from memory.

        Args:
            city: Name of the city
            country: Optional country code

        Returns:
            Dictionary containing weather data if found, None otherwise
        """
        key = self._get_key(city, country)
        return self.storage.get(key)

    def get_by_coordinates(self, latitude: float, longitude: float) -> Optional[Dict[str, Any]]:
        """
        Retrieves weather data for coordinates from memory.

        Args:
            latitude: Latitude coordinate
            longitude: Longitude coordinate

        Returns:
            Dictionary containing weather data if found, None otherwise
        """
        key = f"coord_{latitude}_{longitude}"
        return self.storage.get(key)

    def save(self, weather_data: Dict[str, Any]) -> bool:
        """
        Saves weather data to memory.

        Args:
            weather_data: Weather data to save

        Returns:
            True if saved successfully
        """
        try:
            # Extract location info
            name = weather_data.get('name', 'unknown')
            country = weather_data.get('sys', {}).get('country')
            key = self._get_key(name, country)

            # Save current data
            self.storage[key] = weather_data

            # Add to history
            if key not in self.history:
                self.history[key] = []

            history_entry = weather_data.copy()
            history_entry['saved_at'] = datetime.now().isoformat()
            self.history[key].append(history_entry)

            log.debug(f"Saved weather data for {name}")
            return True
        except Exception as e:
            log.error(f"Error saving weather data: {e}")
            return False

    def get_history(
        self,
        city: str,
        country: Optional[str] = None,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Retrieves historical weather data for a location.

        Args:
            city: Name of the city
            country: Optional country code
            limit: Maximum number of historical records

        Returns:
            List of weather data dictionaries, newest first
        """
        key = self._get_key(city, country)
        if key in self.history:
            history = self.history[key][-limit:]
            history.reverse()
            return history
        return []

    def clear_cache(self) -> None:
        """Clears all stored data."""
        self.storage.clear()
        self.history.clear()
        log.info("Cleared all in-memory weather data")