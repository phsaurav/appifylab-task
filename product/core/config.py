"""
Global Configuration
"""

from typing import Optional

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """
    Base Global Settings
    """

    prod: bool = False
    title: str = "DhakaCelsius"
    fastapi_log_level: str = "info"
    sentry_dsn: Optional[str] = None


cfg = Settings()
sentry_config = dict(dsn=cfg.sentry_dsn)
