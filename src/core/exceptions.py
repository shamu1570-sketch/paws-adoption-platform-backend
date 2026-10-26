import logging

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from src.core.config import settings
from src.core.responses import failure
from src.core.schemas import USER_MESSAGE_ERROR

logger = logging.getLogger(__name__)

_REQUEST_LOCATIONS = frozenset({"body", "query", "path"})

_HTTP_ERROR_MESSAGES = {
    404: "El recurso solicitado no existe",
    405: "Método no permitido para este recurso",
}


class AppError(Exception):
    """Error de negocio controlado que se traduce a un ResponsePayload."""

    status_code = 500

    def __init__(self, message: str, detail_error: str | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.detail_error = detail_error


class NotFoundError(AppError):
    status_code = 404


class BadRequestError(AppError):
    status_code = 400


class UnauthorizedError(AppError):
    status_code = 401


class ForbiddenError(AppError):
    status_code = 403


class ConflictError(AppError):
    status_code = 409


class ServiceUnavailableError(AppError):
    status_code = 503


def _json(status_code: int, message: str, detail_error: str | None) -> JSONResponse:
    return JSONResponse(
        status_code=status_code, content=failure(status_code, message, detail_error)
    )


def _validation_message(error: dict) -> tuple[str, str]:
    """Traduce un error de Pydantic a (mensaje para el usuario, detalle técnico)."""
    location = [str(part) for part in error.get("loc", ()) if part not in _REQUEST_LOCATIONS]
    field = ".".join(location) or "body"
    if error.get("type") == USER_MESSAGE_ERROR:
        # Validadores propios: su mensaje ya está redactado para el usuario.
        return error["msg"], f"{field}: {error['msg']}"
    if error.get("type") == "missing":
        return f"El campo '{field}' es obligatorio", f"{field} is required"
    reason = error.get("msg", "invalid value")
    return f"El campo '{field}' no cumple con un formato válido", f"{field}: {reason}"


def _handle_app_error(_: Request, exc: AppError) -> JSONResponse:
    response = _json(exc.status_code, exc.message, exc.detail_error)
    if isinstance(exc, UnauthorizedError):
        response.headers["WWW-Authenticate"] = "Bearer"
    return response


def _handle_validation_error(_: Request, exc: RequestValidationError) -> JSONResponse:
    errors = [_validation_message(error) for error in exc.errors()]
    message = errors[0][0] if errors else "La solicitud contiene datos inválidos"
    detail = "Validation failed: " + "; ".join(detail for _, detail in errors)
    return _json(400, message, detail)


def _handle_http_error(_: Request, exc: StarletteHTTPException) -> JSONResponse:
    message = _HTTP_ERROR_MESSAGES.get(exc.status_code, "No se pudo procesar la solicitud")
    return _json(exc.status_code, message, str(exc.detail))


def _handle_unexpected_error(_: Request, exc: Exception) -> JSONResponse:
    logger.exception("Error no controlado", exc_info=exc)
    # El detalle técnico solo se expone con DEBUG activo, nunca en producción.
    detail = f"{type(exc).__name__}: {exc}" if settings.DEBUG else type(exc).__name__
    return _json(500, "Ha ocurrido un error inesperado en el servidor", detail)


def register_exception_handlers(app: FastAPI) -> None:
    """Garantiza que cualquier error salga con el formato ResponsePayload."""
    app.add_exception_handler(AppError, _handle_app_error)
    app.add_exception_handler(RequestValidationError, _handle_validation_error)
    app.add_exception_handler(StarletteHTTPException, _handle_http_error)
    app.add_exception_handler(Exception, _handle_unexpected_error)
