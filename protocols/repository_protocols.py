"""
Repository Protocols for Data Access Abstraction.

This module defines repository interfaces that abstract data access operations,
following the Repository pattern. Repositories encapsulate the logic required
to access data sources, providing a more object-oriented view of the persistence layer.
"""

from typing import Protocol, Optional, List, Dict, Any
from datetime import datetime


class WeatherRepository(Protocol):
    """
    Repository interface for weather data access and persistence.

    This protocol defines the contract for weather data repositories, allowing
    different storage mechanisms (API, database, cache, file system) to be used
    interchangeably while maintaining consistent access patterns.

    Example implementations:
        - APIWeatherRepository: Fetches data from weather APIs
        - CachedWeatherRepository: Wraps another repository with caching
        - DatabaseWeatherRepository: Stores and retrieves from database
        - InMemoryWeatherRepository: Stores in memory (for testing)
    """

    def get_by_city(self, city: str, country: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        Retrieves weather data for a specified city and optional country.

        Args:
            city: Name of the city
            country: Optional country code (e.g., "US", "ES")

        Returns:
            Dictionary containing weather data if found, None otherwise

        Raises:
            Exception: For unexpected errors during retrieval
        """
        ...

    def get_by_coordinates(self, latitude: float, longitude: float) -> Optional[Dict[str, Any]]:
        """
        Retrieves weather data for specified geographic coordinates.

        Args:
            latitude: Latitude coordinate (-90 to 90)
            longitude: Longitude coordinate (-180 to 180)

        Returns:
            Dictionary containing weather data if found, None otherwise

        Raises:
            ValueError: If coordinates are out of valid range
            Exception: For unexpected errors during retrieval
        """
        ...

    def save(self, weather_data: Dict[str, Any]) -> bool:
        """
        Saves weather data to the repository.

        Args:
            weather_data: Dictionary containing weather information

        Returns:
            True if saved successfully, False otherwise

        Raises:
            ValueError: If weather_data is invalid or incomplete
        """
        ...

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
            limit: Maximum number of historical records to return

        Returns:
            List of weather data dictionaries, ordered by timestamp (newest first)
        """
        ...

    def clear_cache(self) -> None:
        """
        Clears any cached data in the repository.

        This method is useful for cache implementations to invalidate stale data.
        """
        ...


class TokenRepository(Protocol):
    """
    Repository interface for token storage and retrieval.

    This protocol defines the contract for token repositories, allowing
    different storage mechanisms to be used interchangeably for managing
    authentication tokens.

    Example implementations:
        - InMemoryTokenRepository: Stores tokens in memory
        - DatabaseTokenRepository: Persists tokens in a database
        - FileTokenRepository: Stores tokens in encrypted files
        - RedisTokenRepository: Stores tokens in Redis cache
    """

    def get(self, token_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieves token information by token ID.

        Args:
            token_id: Unique identifier for the token

        Returns:
            Dictionary containing token information if found, None otherwise
            Expected keys: 'token', 'type', 'created_at', 'expires_at', 'metadata'
        """
        ...

    def save(self, token_id: str, token_data: Dict[str, Any]) -> bool:
        """
        Saves token information to the repository.

        Args:
            token_id: Unique identifier for the token
            token_data: Dictionary containing token information

        Returns:
            True if saved successfully, False otherwise

        Raises:
            ValueError: If token_data is invalid
        """
        ...

    def delete(self, token_id: str) -> bool:
        """
        Deletes a token from the repository.

        Args:
            token_id: Unique identifier for the token to delete

        Returns:
            True if deleted successfully, False if token not found
        """
        ...

    def exists(self, token_id: str) -> bool:
        """
        Checks if a token exists in the repository.

        Args:
            token_id: Unique identifier for the token

        Returns:
            True if token exists, False otherwise
        """
        ...

    def get_all_active(self) -> List[Dict[str, Any]]:
        """
        Retrieves all active (non-expired) tokens.

        Returns:
            List of token information dictionaries
        """
        ...

    def cleanup_expired(self) -> int:
        """
        Removes expired tokens from the repository.

        Returns:
            Number of expired tokens removed
        """
        ...


class ConfigRepository(Protocol):
    """
    Repository interface for configuration data persistence.

    This protocol defines the contract for configuration repositories, allowing
    different storage mechanisms for application configuration with the ability
    to persist changes.

    Example implementations:
        - FileConfigRepository: Stores config in JSON/YAML/TOML files
        - DatabaseConfigRepository: Stores config in a database
        - RemoteConfigRepository: Syncs with remote configuration service
        - EnvironmentConfigRepository: Reads from environment variables
    """

    def get(self, key: str) -> Optional[Any]:
        """
        Retrieves a configuration value by key.

        Args:
            key: Configuration key

        Returns:
            Configuration value if found, None otherwise
        """
        ...

    def set(self, key: str, value: Any) -> bool:
        """
        Sets a configuration value.

        Args:
            key: Configuration key
            value: Configuration value

        Returns:
            True if saved successfully, False otherwise
        """
        ...

    def get_all(self) -> Dict[str, Any]:
        """
        Retrieves all configuration key-value pairs.

        Returns:
            Dictionary containing all configuration
        """
        ...

    def delete(self, key: str) -> bool:
        """
        Deletes a configuration key.

        Args:
            key: Configuration key to delete

        Returns:
            True if deleted successfully, False if key not found
        """
        ...

    def reload(self) -> None:
        """
        Reloads configuration from the underlying storage.

        This method refreshes the configuration from its source,
        useful for picking up external changes.
        """
        ...

    def persist(self) -> bool:
        """
        Persists current configuration to storage.

        Returns:
            True if persisted successfully, False otherwise
        """
        ...
