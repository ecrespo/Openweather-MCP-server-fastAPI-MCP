"""
Weather Service Protocols.

This module defines protocol interfaces for weather data retrieval services,
allowing different weather API providers to be used interchangeably while
maintaining type safety and a consistent interface.
"""

from typing import Protocol, Optional
from dataclasses import dataclass
from typing import Any, Dict, List


@dataclass
class WeatherData:
    """
    Standard weather data structure.

    This dataclass provides a standardized representation of weather information
    that can be used across different weather service implementations.

    :ivar coord: Geographic coordinates of the location
    :ivar weather: List of weather condition details
    :ivar base: Internal parameter indicating information source
    :ivar main: Main climate details including temperature, pressure, etc.
    :ivar visibility: Visibility level in meters
    :ivar wind: Wind details including speed and direction
    :ivar clouds: Cloudiness information
    :ivar dt: Timestamp of the data calculation in Unix format
    :ivar sys: System-related information such as country and sunrise/sunset
    :ivar timezone: Timezone offset in seconds from UTC
    :ivar id: Unique identifier for the weather data location
    :ivar name: Name of the location
    :ivar cod: Response code for the weather data
    """
    coord: Dict[str, Any]
    weather: List[Dict[str, Any]]
    base: str
    main: Dict[str, Any]
    visibility: int
    wind: Dict[str, Any]
    clouds: Dict[str, Any]
    dt: int
    sys: Dict[str, Any]
    timezone: int
    id: int
    name: str
    cod: int


class WeatherService(Protocol):
    """
    Protocol for weather service implementations.

    This protocol defines the interface that all weather services must implement.
    It enables different weather API providers (OpenWeatherMap, WeatherAPI.com,
    AccuWeather, etc.) to be used interchangeably throughout the application.

    Example implementations:
        - OpenWeatherMapService: Retrieves data from OpenWeatherMap API
        - WeatherAPIService: Retrieves data from WeatherAPI.com
        - MockWeatherService: Provides mock data for testing
        - CachedWeatherService: Wraps another service with caching
    """

    def get_weather(self, city: str, country: Optional[str] = None) -> WeatherData:
        """
        Retrieves weather information for a specified city and optional country.

        Args:
            city: Name of the city for which weather information is requested
            country: Optional country code to further specify the location
                    (e.g., "US" for United States). Defaults to None.

        Returns:
            A WeatherData instance containing weather information for the
            specified location

        Raises:
            HTTPException: If the request times out, connection fails, or if
                          the requested weather data could not be found
            ValueError: If the city parameter is invalid or empty
        """
        ...

    def get_weather_by_coordinates(
        self, latitude: float, longitude: float
    ) -> WeatherData:
        """
        Retrieves weather information for specified geographic coordinates.

        Args:
            latitude: Latitude coordinate (-90 to 90)
            longitude: Longitude coordinate (-180 to 180)

        Returns:
            A WeatherData instance containing weather information for the
            specified coordinates

        Raises:
            HTTPException: If the request times out, connection fails, or if
                          the requested weather data could not be found
            ValueError: If the coordinates are out of valid range
        """
        ...