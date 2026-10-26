from http import HTTPStatus

from pydantic import BaseModel


class ResponsePayload[T](BaseModel):
    """Formato unificado de respuesta de todos los endpoints de la API."""

    statusCode: int
    status: str
    message: str
    data: T | None = None
    detailError: str | None = None


def success[T](data: T, message: str, status_code: int = 200) -> ResponsePayload[T]:
    return ResponsePayload[T](
        statusCode=status_code,
        status=HTTPStatus(status_code).name,
        message=message,
        data=data,
        detailError=None,
    )


def failure(status_code: int, message: str, detail_error: str | None = None) -> dict:
    return ResponsePayload[None](
        statusCode=status_code,
        status=HTTPStatus(status_code).name,
        message=message,
        data=None,
        detailError=detail_error,
    ).model_dump()
