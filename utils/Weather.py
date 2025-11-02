from dataclasses import dataclass
from typing import Any, Dict, List, Optional
from fastapi import HTTPException, status
import httpx

from utils.config import settings
from utils.logger import log

@dataclass
class Weather:
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

    response = httpx.get(url, params=parametros)
    if response.status_code != 200:
        log.error(response.text)
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Error al obtener la información del clima")

    resp = response.json()

    data = Weather(**resp)
    return data
