"""
Main entry point for this FastAPI Project
"""

import uvicorn
from app.version import __version__
from app.weather.api import weather
from app.weather.schemas import HealthResponseSchema
from core import config
from core.logger import Logger
from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware

app = FastAPI(title=config.cfg.title, version=__version__)
Logger.setup(app=app, json_format=True)

# CORS
if not config.cfg.prod:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:3000"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )


@app.get("/")
def root():
    """
    Welcome to Appify lab auth service
    """
    return {
        "This is the order service",
    }


@app.get("/health")
def health():
    """
    Health check endpoint that verifies API and dependencies health
    """

    health_status = HealthResponseSchema(
        status="healthy",
        status_code=200,
    )

    return health_status


if __name__ == "__main__":
    uvicorn.run(app, log_level=config.cfg.fastapi_log_level)
