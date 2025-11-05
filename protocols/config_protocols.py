"""
Configuration Provider Protocols.

This module defines protocol interfaces for configuration providers,
allowing different configuration sources to be used interchangeably while
maintaining type safety and a consistent interface.
"""

from typing import Protocol, Any, Optional


class ConfigProvider(Protocol):
    """
    Protocol for configuration provider implementations.

    This protocol defines the interface that all configuration providers must
    implement. It enables different configuration sources (environment variables,
    files, remote config servers, etc.) to be used interchangeably throughout
    the application.

    Example implementations:
        - EnvironmentConfigProvider: Reads from environment variables
        - FileConfigProvider: Reads from configuration files (JSON, YAML, TOML)
        - RemoteConfigProvider: Fetches from remote configuration servers
        - LayeredConfigProvider: Combines multiple config sources with priority
    """

    def get(self, key: str, default: Any = None) -> Any:
        """
        Retrieves a configuration value by key.

        Args:
            key: The configuration key to retrieve
            default: Default value to return if key is not found

        Returns:
            The configuration value if found, otherwise the default value

        Raises:
            KeyError: May raise if key is required but not found and no default
        """
        ...

    def get_string(self, key: str, default: str = "") -> str:
        """
        Retrieves a configuration value as a string.

        Args:
            key: The configuration key to retrieve
            default: Default string value to return if key is not found

        Returns:
            The configuration value as a string
        """
        ...

    def get_int(self, key: str, default: int = 0) -> int:
        """
        Retrieves a configuration value as an integer.

        Args:
            key: The configuration key to retrieve
            default: Default integer value to return if key is not found

        Returns:
            The configuration value as an integer

        Raises:
            ValueError: If the value cannot be converted to an integer
        """
        ...

    def get_bool(self, key: str, default: bool = False) -> bool:
        """
        Retrieves a configuration value as a boolean.

        Args:
            key: The configuration key to retrieve
            default: Default boolean value to return if key is not found

        Returns:
            The configuration value as a boolean
        """
        ...

    def validate(self) -> None:
        """
        Validates that all required configuration values are present and valid.

        Raises:
            ValueError: If required configuration values are missing or invalid
            TypeError: If configuration values have incorrect types
        """
        ...


class MutableConfigProvider(ConfigProvider, Protocol):
    """
    Protocol for mutable configuration providers.

    This protocol extends ConfigProvider with write capabilities, allowing
    configuration values to be updated at runtime. This is useful for
    configuration management systems, dynamic configuration updates, and
    testing scenarios.

    Example implementations:
        - DynamicConfigProvider: Supports runtime configuration updates
        - TestConfigProvider: Allows setting test-specific configuration
        - CachedConfigProvider: Caches remote config with refresh capability
    """

    def set(self, key: str, value: Any) -> None:
        """
        Sets a configuration value.

        Args:
            key: The configuration key to set
            value: The value to set for the key

        Raises:
            TypeError: If the value type is not compatible with the key
            ValueError: If the value is not valid for the key
        """
        ...

    def reload(self) -> None:
        """
        Reloads configuration from the underlying source.

        This method is useful for refreshing configuration from external
        sources without restarting the application.

        Raises:
            IOError: If the configuration source cannot be accessed
            ValueError: If the configuration source contains invalid data
        """
        ...