from unittest.mock import patch, Mock

from fastapi import HTTPException
from fastapi.responses import ORJSONResponse
from fastapi.testclient import TestClient
from main import weather, app
from utils.Weather import Weather


@patch("utils.Weather.weather_request")
@patch("utils.logger.log_json")
def test_weather_success(mock_log_json, mock_weather_request):
    mock_weather_data = Mock(spec=Weather)
    mock_weather_data.__dict__ = {
        "name": "London",
        "sys": {"country": "GB"},
        "weather": [{"description": "clear sky"}],
        "main": {"temp": 20.0},
    }
    mock_weather_request.return_value = mock_weather_data

    response = weather("London", "GB")
    assert isinstance(response, ORJSONResponse)
    assert response.status_code == 200
    assert response.body == b'{"name":"London","sys":{"country":"GB"},"weather":[{"description":"clear sky"}],"main":{"temp":20.0}}'

    mock_log_json.assert_called_once_with(mock_weather_data.__dict__)
    mock_weather_request.assert_called_once_with("London", "GB")


@patch("utils.Weather.weather_request")
def test_weather_not_found(mock_weather_request):
    mock_weather_request.side_effect = HTTPException(
        status_code=404, detail="Weather data not found"
    )

    try:
        weather("InvalidCity", "InvalidCountry")
    except HTTPException as exc:
        assert exc.status_code == 404
        assert exc.detail == "Weather data not found"

    mock_weather_request.assert_called_once_with("InvalidCity", "InvalidCountry")


def test_hello_world():
    """
    Test the hello_world function to ensure it returns the correct
    JSON response with "Hello World!" and a 200 status code.
    """
    client = TestClient(app)
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == "Hello World!"
