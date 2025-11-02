from typing import List, Dict, Any, Optional

from fastapi import FastAPI, HTTPException, status, Depends
from fastapi.responses import ORJSONResponse, JSONResponse

from utils.Weather import weather_request
from utils.config import settings
from utils.logger import log


app = FastAPI()


@app.get("/weather/{city}/{country}",operation_id="get_weather_by_country")
async def weather(city:str, country: Optional[str] = None) ->ORJSONResponse:

    data = weather_request(city, country)
    return ORJSONResponse(content=data.__dict__)


@app.get("/",operation_id="hello_world")
async def hello_world():
    return JSONResponse(content="Hello World!")



