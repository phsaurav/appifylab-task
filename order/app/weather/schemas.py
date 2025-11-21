"""
Weather API Response Pydantic Schemas
"""

from pydantic import BaseModel, Field
from typing import Dict


class TemperatureData(BaseModel):
    """Schema for temperature data of a location"""

    temperature: str = Field(..., description="Temperature value")
    temp_unit: str = Field(..., description="Temperature unit (c/f)")


class WeatherResponseSchema(BaseModel):
    """
    Response schema for weather request on /hello endpoint
    """

    hostname: str = Field(..., description="Server hostname")
    datetime: str = Field(..., description="Current datetime in YYMMDDHHmm format")
    version: str = Field(..., description="API version")
    weather: Dict[str, TemperatureData] = Field(
        ..., description="Weather information for Dhaka"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "hostname": "server1",
                "datetime": "2307152230",
                "version": "1.0.0",
                "weather": {"dhaka": {"temperature": "14", "temp_unit": "c"}},
            }
        }


class HealthResponseSchema(BaseModel):
    """
    Response schema for /health endpoint
    """

    status: str = Field(
        ..., description="Health status of the application (healthy/degraded/unhealthy)"
    )
    status_code: int = Field(
        ..., description="HTTP status code reflecting health state"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "status": "healthy",
                "status_code": 200,
            }
        }
