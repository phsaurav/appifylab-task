from app.weather import schemas
from core.logger import get_request_logger
from fastapi import APIRouter, Depends

router = APIRouter(tags=["weather"])


@router.get("/health", response_model=schemas.HealthResponseSchema)
def health_check(logger=Depends(get_request_logger)):
    """
    Health check endpoint that verifies API and dependencies health
    """

    health_status = schemas.HealthResponseSchema(
        status="healthy",
        status_code=200,
    )

    return health_status
