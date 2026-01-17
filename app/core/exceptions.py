from fastapi import Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException


# Хендлер для ошибок валидации (Pydantic)
async def validation_exception_handler(
    request: Request, exc: Exception
) -> JSONResponse:
    assert isinstance(exc, RequestValidationError)
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"detail": exc.errors(), "type": "validation_error"},
    )


# Хендлер для обычных HTTP ошибок
async def http_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    assert isinstance(exc, StarletteHTTPException)
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail},
    )


# Хендлер для всех непредвиденных ошибок (500)
async def general_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    # Здесь можно добавить логирование ошибки в Sentry или файл
    print(f"ERROR: {exc}")
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal Server Error"},
    )
