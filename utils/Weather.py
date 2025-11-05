from dataclasses import dataclass
from typing import Any, Dict, List, Optional
from fastapi import HTTPException, status
import httpx

from utils.config import settings
from utils.logger import log
from utils.circuit_breaker import SimpleCircuitBreaker, circuit_breaker_registry, CircuitBreakerError

@dataclass
class Weather:
    """
    Represents weather data for a specific location.

    This class is a container for weather information, such as coordinates,
    weather conditions, main climate details, visibility, wind data,
    cloudiness, and other related metrics. It is typically used to store
    data retrieved from a weather API or similar source.

    :ivar coord: Geographic coordinates of the location.
    :type coord: Dict[str, Any]
    :ivar weather: List of weather condition details.
    :type weather: List[Dict[str, Any]]
    :ivar base: Internal parameter indicating information source.
    :type base: str
    :ivar main: Main climate details including temperature, pressure, etc.
    :type main: Dict[str, Any]
    :ivar visibility: Visibility level in meters for this location.
    :type visibility: int
    :ivar wind: Wind details including speed and direction.
    :type wind: Dict[str, Any]
    :ivar clouds: Cloudiness information.
    :type clouds: Dict[str, Any]
    :ivar dt: Timestamp of the data calculation in Unix format.
    :type dt: int
    :ivar sys: System-related information such as country and sunrise/sunset.
    :type sys: Dict[str, Any]
    :ivar timezone: Timezone offset in seconds from UTC.
    :type timezone: int
    :ivar id: Unique identifier for the weather data location.
    :type id: int
    :ivar name: Name of the location.
    :type name: str
    :ivar cod: Response code for the weather data.
    :type cod: int
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

def weather_request(city:str, country: Optional[str] = None)-> Weather:
    """
    Retrieves weather information for a specified city and optionally for a country
    using the OpenWeatherMap API. The function sends an HTTP GET request to
    the API's weather endpoint, collects relevant data, and returns it as a
    Weather object.

    :param city: Name of the city for which weather information is requested.
    :type city: str
    :param country: Optional country code to further specify the location.
                    For example, "US" for the United States. Defaults to None.
    :type country: str, optional
    :return: An instance of the Weather class containing weather data for
             the specified location.
    :rtype: Weather
    :raises HTTPException: If the request times out or if the requested
             weather data could not be found, an HTTPException with an appropriate
             status code and error message is raised.
    """
    access_key = settings.ACCESS_KEY
    url = "https://api.openweathermap.org/data/2.5/weather"
    query_param = f"{city}"
    if country:
        query_param += f",{country}"

    parametros = {
        "q": query_param,
        "appid": access_key,
        "units": "metric",  # O 'imperial' para Fahrenheit
        "lang": "es"  # Lenguaje de la respuesta (opcional)
    }
    try:
        response = httpx.get(url, params=parametros)
    except httpx.ReadTimeout:
        raise HTTPException(status_code=status.HTTP_408_REQUEST_TIMEOUT, detail="Tiempo de espera excedido")
    except httpx.ConnectError:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Error de conexión con el servicio de clima")

    if response.status_code != 200:
        log.error(response.text)
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Error al obtener la información del clima")

    resp = response.json()

    data = Weather(**resp)
    return data


class OpenWeatherMapService:
    """
    OpenWeatherMap API implementation of weather service.

    This class provides weather data retrieval functionality using the
    OpenWeatherMap API. It can be used interchangeably with other weather
    service implementations thanks to its adherence to the WeatherService protocol.

    :ivar access_key: API key for OpenWeatherMap authentication
    :type access_key: str
    :ivar base_url: Base URL for the OpenWeatherMap API
    :type base_url: str
    """

    def __init__(
        self,
        access_key: Optional[str] = None,
        enable_circuit_breaker: bool = True,
        failure_threshold: int = 5,
        recovery_timeout: float = 60.0
    ):
        """
        Initialize the OpenWeatherMap service.

        Args:
            access_key: Optional API key. If not provided, uses the key from settings
            enable_circuit_breaker: Whether to enable circuit breaker protection
            failure_threshold: Number of failures before opening circuit
            recovery_timeout: Seconds to wait before attempting recovery
        """
        self.access_key = access_key or settings.ACCESS_KEY
        self.base_url = "https://api.openweathermap.org/data/2.5/weather"

        # Initialize circuit breaker
        self.circuit_breaker: Optional[SimpleCircuitBreaker] = None
        if enable_circuit_breaker:
            self.circuit_breaker = SimpleCircuitBreaker(
                failure_threshold=failure_threshold,
                recovery_timeout=recovery_timeout,
                success_threshold=2,
                expected_exceptions=(httpx.HTTPError, HTTPException, ConnectionError, TimeoutError)
            )
            circuit_breaker_registry.register("openweathermap_api", self.circuit_breaker)
            log.info(
                f"OpenWeatherMapService initialized with Circuit Breaker "
                f"(threshold={failure_threshold}, timeout={recovery_timeout}s)"
            )
        else:
            log.info("OpenWeatherMapService initialized without Circuit Breaker")

    def _make_api_call(self, params: Dict[str, Any]) -> Weather:
        """
        Internal method to make API call. This is wrapped by circuit breaker.

        Args:
            params: Query parameters for the API call

        Returns:
            Weather data

        Raises:
            HTTPException: On API errors
        """
        try:
            response = httpx.get(self.base_url, params=params, timeout=10.0)
        except httpx.ReadTimeout:
            raise HTTPException(
                status_code=status.HTTP_408_REQUEST_TIMEOUT,
                detail="Tiempo de espera excedido"
            )
        except httpx.ConnectError:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Error de conexión con el servicio de clima"
            )

        if response.status_code != 200:
            log.error(f"API error: {response.status_code} - {response.text}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Error al obtener la información del clima"
            )

        resp = response.json()
        return Weather(**resp)

    def get_weather(self, city: str, country: Optional[str] = None) -> Weather:
        """
        Retrieves weather information for a specified city and optional country.

        This method implements the WeatherService protocol's get_weather method.
        Calls are protected by Circuit Breaker if enabled.

        Args:
            city: Name of the city for which weather information is requested
            country: Optional country code to further specify the location
                    (e.g., "US" for United States). Defaults to None.

        Returns:
            A Weather instance containing weather data for the specified location

        Raises:
            HTTPException: If the request times out, connection fails, or if
                          the requested weather data could not be found
            CircuitBreakerError: If circuit breaker is OPEN
        """
        query_param = f"{city}"
        if country:
            query_param += f",{country}"

        parametros = {
            "q": query_param,
            "appid": self.access_key,
            "units": "metric",
            "lang": "es"
        }

        # Use circuit breaker if enabled
        if self.circuit_breaker:
            try:
                return self.circuit_breaker.call(self._make_api_call, parametros)
            except CircuitBreakerError as e:
                log.error(f"Circuit breaker is OPEN for OpenWeatherMap API: {e}")
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail=f"Weather service temporarily unavailable. Retry after {e.retry_after:.0f}s"
                )
        else:
            return self._make_api_call(parametros)

    def get_weather_by_coordinates(
        self, latitude: float, longitude: float
    ) -> Weather:
        """
        Retrieves weather information for specified geographic coordinates.

        This method implements the WeatherService protocol's get_weather_by_coordinates method.
        Calls are protected by Circuit Breaker if enabled.

        Args:
            latitude: Latitude coordinate (-90 to 90)
            longitude: Longitude coordinate (-180 to 180)

        Returns:
            A Weather instance containing weather data for the specified coordinates

        Raises:
            HTTPException: If the request times out, connection fails, or if
                          the requested weather data could not be found
            ValueError: If the coordinates are out of valid range
            CircuitBreakerError: If circuit breaker is OPEN
        """
        if not (-90 <= latitude <= 90):
            raise ValueError(f"Latitude must be between -90 and 90, got {latitude}")
        if not (-180 <= longitude <= 180):
            raise ValueError(f"Longitude must be between -180 and 180, got {longitude}")

        parametros = {
            "lat": latitude,
            "lon": longitude,
            "appid": self.access_key,
            "units": "metric",
            "lang": "es"
        }

        # Use circuit breaker if enabled
        if self.circuit_breaker:
            try:
                return self.circuit_breaker.call(self._make_api_call, parametros)
            except CircuitBreakerError as e:
                log.error(f"Circuit breaker is OPEN for OpenWeatherMap API: {e}")
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail=f"Weather service temporarily unavailable. Retry after {e.retry_after:.0f}s"
                )
        else:
            return self._make_api_call(parametros)
