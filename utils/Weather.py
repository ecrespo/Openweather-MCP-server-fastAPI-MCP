from dataclasses import dataclass
from typing import Any, Dict, List, Optional
from fastapi import HTTPException, status
import httpx

from utils.config import settings
from utils.logger import log

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
