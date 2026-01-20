import traceback

import structlog
from fastapi import Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

logger = structlog.get_logger()


# Хендлер для ошибок валидации (Pydantic)
async def validation_exception_handler(
    request: Request, exc: Exception
) -> JSONResponse:
    assert isinstance(exc, RequestValidationError)

    logger.warning(
        "Validation error",
        path=request.url.path,
        method=request.method,
        client_ip=request.client.host if request.client else "unknown",
        errors=exc.errors(),
    )
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"detail": exc.errors(), "type": "validation_error"},
    )


# Хендлер для обычных HTTP ошибок
async def http_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    assert isinstance(exc, StarletteHTTPException)
    if 400 <= exc.status_code < 500:
        logger.warning(
            "HTTP client error",
            status_code=exc.status_code,
            detail=exc.detail,
            path=request.url.path,
            method=request.method,
            client_ip=request.client.host if request.client else "unknown",
        )
    elif exc.status_code >= 500:
        logger.error(
            "HTTP server error",
            status_code=exc.status_code,
            detail=exc.detail,
            path=request.url.path,
            method=request.method,
            client_ip=request.client.host if request.client else "unknown",
        )

    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail},
    )


# Хендлер для всех непредвиденных ошибок (500)
async def general_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    # Здесь можно добавить логирование ошибки в Sentry или файл
    logger.error(
        "Unhandled exception",
        path=request.url.path,
        method=request.method,
        client_ip=request.client.host if request.client else "unknown",
        error_type=type(exc).__name__,
        error_message=str(exc),
        traceback=traceback.format_exception(type(exc), exc, exc.__traceback__),
    )
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal Server Error"},
    )
