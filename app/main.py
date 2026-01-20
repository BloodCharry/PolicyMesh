from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

import structlog
from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from prometheus_fastapi_instrumentator import Instrumentator
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.api.v1 import admin, auth, mock, users
from app.core.config import settings
from app.core.exceptions import (
    general_exception_handler,
    http_exception_handler,
    validation_exception_handler,
)
from app.core.logging import setup_logging
from app.middleware.authentication import AuthMiddleware

# Настройка логгера
logger = structlog.get_logger()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    # Startup
    setup_logging(log_level="INFO")
    logger.info("Startup application", project=settings.PROJECT_NAME)
    yield
    # Shutdown
    logger.info("Shutdown application")


app = FastAPI(title=settings.PROJECT_NAME, lifespan=lifespan)

# Metrics Prometheus
Instrumentator().instrument(app).expose(app)

# Middleware
app.add_middleware(AuthMiddleware)

# Exception Handlers
app.add_exception_handler(StarletteHTTPException, http_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(Exception, general_exception_handler)

# Routers
app.include_router(auth.router, prefix="/api/v1/auth", tags=["Authentication"])
app.include_router(users.router, prefix="/api/v1/users", tags=["Users"])
app.include_router(mock.router, prefix="/api/v1/mock-orders", tags=["Mock Orders"])
app.include_router(admin.router, prefix="/api/v1/admin", tags=["Admin Control"])


@app.get("/health")
async def health_check() -> dict[str, str]:
    return {"status": "ok", "project": settings.PROJECT_NAME, "db": "connected"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
