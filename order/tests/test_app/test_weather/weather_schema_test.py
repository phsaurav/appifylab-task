"""Unit Test Weather API Pydantic Schemas"""

import pytest
from pydantic import ValidationError
from app.weather.schemas import (
    TemperatureData,
    WeatherResponseSchema,
    HealthResponseSchema,
)


def test_temperature_data_schema():
    """Test TemperatureData schema"""
    data = {"temperature": "25", "temp_unit": "c"}
    schema = TemperatureData(**data)
    assert schema.model_dump() == data


def test_temperature_data_schema_validation_error():
    """Test TemperatureData with invalid data"""
    data = {"temperature": 25, "temp_unit": "celsius"}  # Type error and invalid unit
    with pytest.raises(ValidationError):
        TemperatureData(**data)


def test_weather_response_schema():
    """Test WeatherResponseSchema"""
    data = {
        "hostname": "server1",
        "datetime": "2307152230",
        "version": "1.0.0",
        "weather": {"dhaka": {"temperature": "14", "temp_unit": "c"}},
    }
    schema = WeatherResponseSchema(**data)
    assert schema.model_dump() == data


def test_weather_response_schema_validation_error():
    """Test WeatherResponseSchema with invalid data"""
    data = {
        "hostname": "server1",
        "datetime": "2307152230",
        "version": "1.0.0",
        "weather": {"dhaka": {"temp": "14", "unit": "c"}},  # Wrong field names
    }
    with pytest.raises(ValidationError):
        WeatherResponseSchema(**data)


def test_health_response_schema():
    """Test HealthResponseSchema"""
    data = {
        "status": "healthy",
        "status_code": 200,
        "timestamp": "2307152230",
        "version": "1.0.0",
        "external_services": {"weather_service": True},
        "response_time": 88.00,
    }
    schema = HealthResponseSchema(**data)
    assert schema.model_dump() == data


def test_health_response_schema_validation_error():
    """Test HealthResponseSchema with invalid data"""
    data = {
        "status": "healthy",
        "status_code": "not_a_number",
        "timestamp": "2307152230",
        "version": "1.0.0",
        "external_services": {"weather_service": True},
        "response_time": 88.00,
    }
    with pytest.raises(ValidationError):
        HealthResponseSchema(**data)
