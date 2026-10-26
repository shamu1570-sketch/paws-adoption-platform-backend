import logging

import httpx

from src.core.exceptions import ServiceUnavailableError

logger = logging.getLogger(__name__)

_STORAGE_ERROR_MESSAGE = "No se pudo guardar la fotografía. Intenta de nuevo más tarde."
_TIMEOUT_SECONDS = 30


class SupabaseStorage:
    """Implementación de FileStorage sobre la API REST de Supabase Storage."""

    def __init__(self, base_url: str, service_role_key: str, bucket: str) -> None:
        storage_url = f"{base_url.rstrip('/')}/storage/v1/object"
        self._object_url = f"{storage_url}/{bucket}"
        self._public_url = f"{storage_url}/public/{bucket}/"
        self._headers = {"Authorization": f"Bearer {service_role_key}", "apikey": service_role_key}

    async def upload(self, path: str, content: bytes, content_type: str) -> str:
        headers = {**self._headers, "Content-Type": content_type}
        try:
            async with httpx.AsyncClient(timeout=_TIMEOUT_SECONDS) as client:
                response = await client.post(
                    f"{self._object_url}/{path}", content=content, headers=headers
                )
                response.raise_for_status()
        except httpx.HTTPStatusError as error:
            detail = (
                f"Supabase Storage respondió {error.response.status_code}: {error.response.text}"
            )
            raise ServiceUnavailableError(_STORAGE_ERROR_MESSAGE, detail) from error
        except httpx.HTTPError as error:
            raise ServiceUnavailableError(_STORAGE_ERROR_MESSAGE, str(error)) from error
        return f"{self._public_url}{path}"

    async def delete(self, public_url: str) -> None:
        if not public_url.startswith(self._public_url):
            return
        path = public_url.removeprefix(self._public_url)
        try:
            async with httpx.AsyncClient(timeout=_TIMEOUT_SECONDS) as client:
                response = await client.delete(f"{self._object_url}/{path}", headers=self._headers)
                response.raise_for_status()
        except httpx.HTTPError:
            # Un archivo huérfano no debe impedir la operación de negocio.
            logger.warning("No se pudo eliminar el archivo %s del almacenamiento", path)


class UnconfiguredStorage:
    """Se usa cuando faltan las variables de Supabase: permite leer, pero no subir archivos."""

    async def upload(self, path: str, content: bytes, content_type: str) -> str:
        raise ServiceUnavailableError(
            "El almacenamiento de fotografías no está configurado",
            "SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY must be set to upload files.",
        )

    async def delete(self, public_url: str) -> None:
        """Sin almacenamiento configurado no hay nada que eliminar."""
