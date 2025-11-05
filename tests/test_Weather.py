# tests/test_Weather.py

from unittest.mock import patch, Mock

import pytest
import httpx
from fastapi import HTTPException
from httpx import Response
from utils.Weather import weather_request, Weather


@pytest.fixture
def mock_api_response():
    return {
        "coord": {"lon": -0.13, "lat": 51.51},
        "weather": [{"id": 803, "main": "Clouds", "description": "broken clouds", "icon": "04d"}],
        "base": "stations",
        "main": {"temp": 12.34, "feels_like": 10.5, "temp_min": 10.0, "temp_max": 15.0, "pressure": 1012,
                 "humidity": 81},
        "visibility": 10000,
        "wind": {"speed": 4.63, "deg": 220},
        "clouds": {"all": 60},
        "dt": 1698783600,
        "sys": {"type": 1, "id": 1414, "country": "GB", "sunrise": 1698756000, "sunset": 1698792600},
        "timezone": 0,
        "id": 2643743,
        "name": "London",
        "cod": 200
    }


@patch("httpx.get")
def test_weather_request_success(mock_get, mock_api_response):
    mock_response = Mock(spec=Response)
    mock_response.status_code = 200
    mock_response.json.return_value = mock_api_response
    mock_get.return_value = mock_response

    weather_data = weather_request("London", "GB")

    assert isinstance(weather_data, Weather)
    assert weather_data.name == "London"
    assert weather_data.sys["country"] == "GB"


@patch("httpx.get")
def test_weather_request_not_found(mock_get):
    mock_response = Mock(spec=Response)
    mock_response.status_code = 404
    mock_response.text = "Not Found"
    mock_get.return_value = mock_response

    with pytest.raises(HTTPException) as exc_info:
        weather_request("NonexistentCity", "XX")

    assert exc_info.value.status_code == 404
    assert "Error al obtener la información del clima" in exc_info.value.detail


@patch("httpx.get")
def test_weather_request_timeout(mock_get):
    mock_get.side_effect = httpx.ReadTimeout("Request timed out")

    with pytest.raises(HTTPException) as exc_info:
        weather_request("London", "GB")

    assert exc_info.value.status_code == 408
    assert "Tiempo de espera excedido" in exc_info.value.detail
