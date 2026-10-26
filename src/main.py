from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.api.router import api_router
from src.core.config import settings
from src.core.exceptions import register_exception_handlers

app = FastAPI(
    title=f"{settings.APP_NAME} API",
    description="API para la gestión de mascotas, refugios y adopciones.",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization", "X-Admin-Registration-Key"],
)

register_exception_handlers(app)

app.include_router(api_router, prefix=settings.API_PREFIX)


@app.get("/")
def root() -> dict[str, str]:
    return {"message": "Bienvenido a Huellitas de Amor API"}
