import uvicorn
import json
from typing import List, Dict, Any, Optional

from fastapi import FastAPI, HTTPException, status, Depends, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.responses import ORJSONResponse, JSONResponse
from fastapi_mcp import FastApiMCP
from fastapi_mcp.types import AuthConfig
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from utils.Weather import weather_request
from utils.config import settings
from utils.logger import log, log_json
from utils.auth import LocalTokenValidator
from repositories.weather_repository import CachedWeatherRepository
from utils.circuit_breaker import CircuitBreakerRegistry
from utils.container import get_container, SimpleDIContainer
from utils.dependencies import (
    configure_container,
    get_weather_repository,
    get_token_validator,
    get_limiter,
    get_circuit_breaker_registry
)

app = FastAPI()

# --- Dependency Injection Container Setup ---
container = get_container()
configure_container(container)
log.info("Application dependencies configured via DI container")

# --- Rate Limiting setup with slowapi (using DI) ---
limiter = get_limiter()
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# --- MCP Authentication setup using LocalTokenValidator ---
security = HTTPBearer(auto_error=True)


async def authenticate_request(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    validator: LocalTokenValidator = Depends(get_token_validator)
) -> dict:
    """
    Dependency used by fastapi-mcp to require a valid Bearer token for MCP tool invocations.
    The token is validated using the LocalTokenValidator from DI container.
    """
    token = credentials.credentials if credentials else None
    info = validator.validate_token(token)
    if not info:
        log.warning("Unauthorized MCP request - invalid or missing token")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized")
    log.debug("MCP request authenticated successfully")
    return info




@app.get("/weather/{city}/{country}",operation_id="get_weather_by_country")
@limiter.limit("50/minute")
async def weather(
    request: Request,
    city: str,
    country: Optional[str] = None,
    repository: CachedWeatherRepository = Depends(get_weather_repository)
) -> ORJSONResponse:
    """
    Retrieves weather data for a given city and an optional country. This endpoint
    uses a cached repository (injected via DI) to fetch weather information,
    reducing API calls and improving performance.

    :param request: The FastAPI Request object (required for rate limiting)
    :type request: Request
    :param city: The name of the city for which the weather data is being fetched
    :type city: str
    :param country: The optional country name to refine the city query
    :type country: Optional[str]
    :param repository: Weather repository (injected via DI)
    :type repository: CachedWeatherRepository
    :return: The weather data for the specified city and country in JSON format
    :rtype: ORJSONResponse
    """
    # Use repository from DI container
    data = repository.get_by_city(city, country)

    if data is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Weather data not found for {city}"
        )

    log_json(data)
    return ORJSONResponse(content=data)


@app.get("/weather/coordinates/{latitude}/{longitude}", operation_id="get_weather_by_coordinates")
@limiter.limit("50/minute")
async def weather_by_coordinates(
    request: Request,
    latitude: float,
    longitude: float,
    repository: CachedWeatherRepository = Depends(get_weather_repository)
) -> ORJSONResponse:
    """
    Retrieves weather data for specified geographic coordinates.

    :param request: The FastAPI Request object (required for rate limiting)
    :type request: Request
    :param latitude: Latitude coordinate (-90 to 90)
    :type latitude: float
    :param longitude: Longitude coordinate (-180 to 180)
    :type longitude: float
    :param repository: Weather repository (injected via DI)
    :type repository: CachedWeatherRepository
    :return: The weather data for the specified coordinates in JSON format
    :rtype: ORJSONResponse
    """
    data = repository.get_by_coordinates(latitude, longitude)

    if data is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Weather data not found for coordinates ({latitude}, {longitude})"
        )

    log_json(data)
    return ORJSONResponse(content=data)


@app.get("/weather/history/{city}", operation_id="get_weather_history")
@limiter.limit("30/minute")
async def weather_history(
    request: Request,
    city: str,
    country: Optional[str] = None,
    limit: int = 10,
    repository: CachedWeatherRepository = Depends(get_weather_repository)
) -> JSONResponse:
    """
    Retrieves historical weather data for a specified city.

    :param request: The FastAPI Request object (required for rate limiting)
    :type request: Request
    :param city: The name of the city
    :type city: str
    :param country: Optional country code
    :type country: Optional[str]
    :param limit: Maximum number of historical records (default: 10)
    :type limit: int
    :param repository: Weather repository (injected via DI)
    :type repository: CachedWeatherRepository
    :return: List of historical weather data in JSON format
    :rtype: JSONResponse
    """
    history = repository.get_history(city, country, limit)
    return JSONResponse(content={
        "city": city,
        "country": country,
        "count": len(history),
        "history": history
    })


@app.get("/cache/stats", operation_id="get_cache_stats")
@limiter.limit("100/minute")
async def cache_stats(
    request: Request,
    repository: CachedWeatherRepository = Depends(get_weather_repository)
) -> JSONResponse:
    """
    Retrieves cache statistics.

    :param request: The FastAPI Request object (required for rate limiting)
    :type request: Request
    :param repository: Weather repository (injected via DI)
    :type repository: CachedWeatherRepository
    :return: Cache statistics in JSON format
    :rtype: JSONResponse
    """
    stats = repository.get_cache_stats()
    return JSONResponse(content=stats)


@app.post("/cache/clear", operation_id="clear_cache")
@limiter.limit("10/minute")
async def clear_cache(
    request: Request,
    repository: CachedWeatherRepository = Depends(get_weather_repository)
) -> JSONResponse:
    """
    Clears the weather data cache.

    :param request: The FastAPI Request object (required for rate limiting)
    :type request: Request
    :param repository: Weather repository (injected via DI)
    :type repository: CachedWeatherRepository
    :return: Confirmation message in JSON format
    :rtype: JSONResponse
    """
    repository.clear_cache()
    log.info("Weather cache cleared via API")
    return JSONResponse(content={"message": "Cache cleared successfully"})


@app.get("/circuit-breaker/stats", operation_id="get_circuit_breaker_stats")
@limiter.limit("100/minute")
async def circuit_breaker_stats(
    request: Request,
    registry: CircuitBreakerRegistry = Depends(get_circuit_breaker_registry)
) -> JSONResponse:
    """
    Get statistics for all circuit breakers.

    :param request: The FastAPI Request object (required for rate limiting)
    :type request: Request
    :param registry: Circuit breaker registry (injected via DI)
    :type registry: CircuitBreakerRegistry
    :return: Circuit breaker statistics in JSON format
    :rtype: JSONResponse
    """
    stats = registry.get_all_stats()
    return JSONResponse(content=stats)


@app.get("/circuit-breaker/{name}/stats", operation_id="get_specific_circuit_breaker_stats")
@limiter.limit("100/minute")
async def specific_circuit_breaker_stats(
    request: Request,
    name: str,
    registry: CircuitBreakerRegistry = Depends(get_circuit_breaker_registry)
) -> JSONResponse:
    """
    Get statistics for a specific circuit breaker.

    :param request: The FastAPI Request object (required for rate limiting)
    :type request: Request
    :param name: Name of the circuit breaker
    :type name: str
    :param registry: Circuit breaker registry (injected via DI)
    :type registry: CircuitBreakerRegistry
    :return: Circuit breaker statistics in JSON format
    :rtype: JSONResponse
    """
    breaker = registry.get(name)
    if not breaker:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Circuit breaker '{name}' not found"
        )

    stats = breaker.get_stats()
    return JSONResponse(content=stats)


@app.post("/circuit-breaker/{name}/reset", operation_id="reset_circuit_breaker")
@limiter.limit("10/minute")
async def reset_circuit_breaker(
    request: Request,
    name: str,
    registry: CircuitBreakerRegistry = Depends(get_circuit_breaker_registry)
) -> JSONResponse:
    """
    Reset a specific circuit breaker to CLOSED state.

    :param request: The FastAPI Request object (required for rate limiting)
    :type request: Request
    :param name: Name of the circuit breaker to reset
    :type name: str
    :param registry: Circuit breaker registry (injected via DI)
    :type registry: CircuitBreakerRegistry
    :return: Confirmation message in JSON format
    :rtype: JSONResponse
    """
    breaker = registry.get(name)
    if not breaker:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Circuit breaker '{name}' not found"
        )

    breaker.reset()
    log.info(f"Circuit breaker '{name}' reset via API")
    return JSONResponse(content={
        "message": f"Circuit breaker '{name}' reset successfully",
        "state": breaker.state.value
    })


@app.get("/circuit-breaker/list", operation_id="list_circuit_breakers")
@limiter.limit("100/minute")
async def list_circuit_breakers(
    request: Request,
    registry: CircuitBreakerRegistry = Depends(get_circuit_breaker_registry)
) -> JSONResponse:
    """
    List all registered circuit breakers.

    :param request: The FastAPI Request object (required for rate limiting)
    :type request: Request
    :param registry: Circuit breaker registry (injected via DI)
    :type registry: CircuitBreakerRegistry
    :return: List of circuit breaker names in JSON format
    :rtype: JSONResponse
    """
    breakers = registry.list_breakers()
    return JSONResponse(content={"breakers": breakers, "count": len(breakers)})


@app.get("/",operation_id="hello_world")
@limiter.limit("100/minute")
async def hello_world(request: Request):
    """
    Handles requests to the root endpoint and returns a JSON response with a greeting message.

    The request handler logs a "Hello World!" message for informational purposes before
    returning the JSON response.

    :param request: The FastAPI Request object (required for rate limiting).
    :type request: Request
    :returns:
        JSONResponse object containing the greeting message "Hello World!".
    """
    log.info("Hello World!")
    return JSONResponse(content="Hello World!")



mcp = FastApiMCP(
    app,
    name="Weather MCP Server",
    include_operations=["get_weather_by_country"],
    description="Weather MCP Server provides weather information for a given country.",
    describe_all_responses=True,
    describe_full_response_schema=True,
    auth_config=AuthConfig(dependencies=[Depends(authenticate_request)]),
)



mcp.mount_http()

def main():
    host = settings.HOST
    port = settings.PORT
    workers = settings.WORKERS
    reload_flag = str(settings.RELOAD).strip().lower() in {"1", "true", "yes", "on"}

    if reload_flag and workers != 1:
        workers = 1

    uvicorn.run(
        'main:app',
        host=host,
        port=port,
        reload=reload_flag,
        workers=workers,
        factory=False,
    )


if __name__ == "__main__":
    main()