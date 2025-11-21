"""Weather Service Unit Test"""

from unittest.mock import MagicMock
import datetime
import socket
import pytest
import requests

from app.weather.api.service import WeatherService
from app.weather.schemas import (
    TemperatureData,
    WeatherResponseSchema,
    HealthResponseSchema,
)
from app.version import __version__
from core.config import cfg
from core.error import APIError, AppError
from core.constants import Constants
from core.logger import Logger


class MockResponse:
    """Mock Response class for requests"""

    def __init__(self, json_data, status_code, elapsed_time=0.1):
        self.json_data = json_data
        self.status_code = status_code
        self.elapsed = datetime.timedelta(seconds=elapsed_time)

    def json(self):
        return self.json_data

    def raise_for_status(self):
        if self.status_code >= 400:
            raise requests.HTTPError(f"HTTP Error: {self.status_code}", response=self)


class TestWeatherService:
    """Test suite for Weather Service"""

    @pytest.fixture
    def weather_service(self, monkeypatch):
        """Fixture to create a WeatherService instance with mocked constants"""
        monkeypatch.setattr(Constants, "weather_api_url", "http://mock-api.com")
        monkeypatch.setattr(Constants, "weather_api_units", "metric")
        monkeypatch.setattr(Constants, "weather_api_key", "fake-api-key")
        monkeypatch.setattr(Constants, "api_timeout", 5)

        return WeatherService()

    @pytest.fixture
    def mock_successful_response(self):
        """Fixture for a successful weather API response"""
        return MockResponse({"main": {"temp": 25.5}}, 200)

    def test_get_weather_data_success(
        self, weather_service, mock_successful_response, monkeypatch
    ):
        """Test successful retrieval of weather data"""
        Logger.debug("Starting test_get_weather_data_success")

        # Mock the requests.get method
        monkeypatch.setattr(
            requests, "get", lambda *args, **kwargs: mock_successful_response
        )

        result = weather_service.get_weather_data("Dhaka")

        assert isinstance(result, TemperatureData)
        assert result.temperature == "26"
        assert result.temp_unit == "c"

    def test_get_weather_data_timeout(self, weather_service, monkeypatch):
        """Test timeout while fetching weather data"""
        Logger.debug("Starting test_get_weather_data_timeout")

        def mock_get(*args, **kwargs):
            raise requests.exceptions.Timeout("Connection timed out")

        monkeypatch.setattr(requests, "get", mock_get)

        with pytest.raises(APIError) as exc_info:
            weather_service.get_weather_data("Dhaka")

        assert exc_info.value.status_code == 504
        assert "Weather API timed out" in str(exc_info.value)

    def test_get_weather_data_http_error_404(self, weather_service, monkeypatch):
        """Test HTTP 404 error while fetching weather data"""
        Logger.debug("Starting test_get_weather_data_http_error_404")

        mock_response = MockResponse({}, 404)

        def mock_get(*args, **kwargs):
            mock_response.raise_for_status()
            return mock_response

        monkeypatch.setattr(requests, "get", mock_get)

        with pytest.raises(APIError) as exc_info:
            weather_service.get_weather_data("Dhaka")

        assert exc_info.value.status_code == 404
        assert "Weather data for Dhaka not found" in str(exc_info.value)

    def test_get_weather_data_http_error_401(self, weather_service, monkeypatch):
        """Test HTTP 401 error while fetching weather data"""
        Logger.debug("Starting test_get_weather_data_http_error_401")

        mock_response = MockResponse({}, 401)

        def mock_get(*args, **kwargs):
            mock_response.raise_for_status()
            return mock_response

        monkeypatch.setattr(requests, "get", mock_get)

        with pytest.raises(APIError) as exc_info:
            weather_service.get_weather_data("Dhaka")

        assert exc_info.value.status_code == 400
        assert "Invalid API key" in str(exc_info.value)

    def test_get_weather_data_generic_exception(self, weather_service, monkeypatch):
        """Test generic exception while fetching weather data"""
        Logger.debug("Starting test_get_weather_data_generic_exception")

        # Mock the requests.get method to raise a generic exception
        def mock_get(*args, **kwargs):
            raise Exception("Something went wrong")

        monkeypatch.setattr(requests, "get", mock_get)

        # Call the method and verify it raises the expected exception
        with pytest.raises(AppError) as exc_info:
            weather_service.get_weather_data("Dhaka")

        # Check the error details
        assert "Failed to fetch weather data" in str(exc_info.value)

    def test_get_hello_data(
        self, weather_service, mock_successful_response, monkeypatch
    ):
        """Test get_hello_data method"""
        Logger.debug("Starting test_get_hello_data")

        # Mock the requests.get method
        monkeypatch.setattr(
            requests, "get", lambda *args, **kwargs: mock_successful_response
        )

        monkeypatch.setattr(socket, "gethostname", lambda: "test-server")

        mock_now = datetime.datetime(2023, 7, 15, 22, 30)
        monkeypatch.setattr(datetime, "datetime", MagicMock(now=lambda: mock_now))

        result = weather_service.get_hello_data()

        assert isinstance(result, WeatherResponseSchema)
        assert result.hostname == "test-server"
        assert result.datetime == "2307152230"
        assert result.version == __version__
        assert "dhaka" in result.weather
        assert result.weather["dhaka"].temperature == "26"  # 25.5 rounded to 26
        assert result.weather["dhaka"].temp_unit == "c"

    def test_check_health_healthy(
        self, weather_service, mock_successful_response, monkeypatch
    ):
        """Test check_health method when service is healthy"""
        Logger.debug("Starting test_check_health_healthy")

        monkeypatch.setattr(
            requests, "get", lambda *args, **kwargs: mock_successful_response
        )

        monkeypatch.setattr(socket, "gethostname", lambda: "test-server")

        mock_now = datetime.datetime(2023, 7, 15, 22, 30)
        monkeypatch.setattr(datetime, "datetime", MagicMock(now=lambda: mock_now))

        result = weather_service.check_health()

        assert isinstance(result, HealthResponseSchema)
        assert result.status == "healthy"
        assert result.status_code == 200
        assert result.timestamp == "2307152230"
        assert result.version == __version__
        assert result.external_services["weather_service"] == True

    def test_check_health_unhealthy(self, weather_service, monkeypatch):
        """Test check_health method when service is unhealthy"""
        Logger.debug("Starting test_check_health_unhealthy")

        mock_response = MockResponse({}, 500)

        monkeypatch.setattr(requests, "get", lambda *args, **kwargs: mock_response)

        monkeypatch.setattr(socket, "gethostname", lambda: "test-server")

        mock_now = datetime.datetime(2023, 7, 15, 22, 30)
        monkeypatch.setattr(datetime, "datetime", MagicMock(now=lambda: mock_now))

        result = weather_service.check_health()

        assert isinstance(result, HealthResponseSchema)
        assert result.status == "unhealthy"
        assert result.status_code == 500
        assert result.timestamp == "2307152230"
        assert result.version == __version__
        assert result.external_services["weather_service"] == False

    def test_check_health_exception(self, weather_service, monkeypatch):
        """Test check_health method when an exception occurs"""
        Logger.debug("Starting test_check_health_exception")

        def mock_get(*args, **kwargs):
            raise Exception("Connection error")

        monkeypatch.setattr(requests, "get", mock_get)

        with pytest.raises(UnboundLocalError) as exc_info:
            weather_service.check_health()

        assert "cannot access local variable 'response'" in str(exc_info.value)
