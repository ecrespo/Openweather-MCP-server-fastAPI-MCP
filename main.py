import uvicorn
import json
from typing import List, Dict, Any, Optional

from fastapi import FastAPI, HTTPException, status, Depends
from fastapi.responses import ORJSONResponse, JSONResponse
from fastapi_mcp import FastApiMCP

from utils.Weather import weather_request
from utils.config import settings
from utils.logger import log, log_json

app = FastAPI()


@app.get("/weather/{city}/{country}",operation_id="get_weather_by_country")
async def weather(city:str, country: Optional[str] = None) ->ORJSONResponse:
    """
    Retrieves weather data for a given city and an optional country. This endpoint
    expects city and country as parameters, fetches the weather information using
    an external function, logs the response, and then returns it as an ORJSONResponse.

    :param city: The name of the city for which the weather data is being fetched.
    :type city: str
    :param country: The optional country name to refine the city query.
    :type country: Optional[str]
    :return: The weather data for the specified city and country in JSON format.
    :rtype: ORJSONResponse
    """
    data = weather_request(city, country)
    log_json(data.__dict__)
    return ORJSONResponse(content=data.__dict__)


@app.get("/",operation_id="hello_world")
async def hello_world():
    """
    Handles requests to the root endpoint and returns a JSON response with a greeting message.

    The request handler logs a "Hello World!" message for informational purposes before
    returning the JSON response.

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
    describe_full_response_schema=True
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