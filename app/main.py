from fastapi import FastAPI

from app.api.v1 import auth, users
from app.core.config import settings
from app.middleware.authentication import AuthMiddleware

app = FastAPI(title=settings.PROJECT_NAME)

app.add_middleware(AuthMiddleware)

app.include_router(auth.router, prefix="/api/v1/auth", tags=["Authentication"])
app.include_router(users.router, prefix="/api/v1/users", tags=["Users"])


@app.get("/health")
async def health_check() -> dict[str, str]:
    return {"status": "ok", "project": settings.PROJECT_NAME, "db": "connected"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
