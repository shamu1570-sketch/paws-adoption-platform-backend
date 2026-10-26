"""Galerías de fotografías (mascotas y refugios): validación, conversión a WebP y almacenamiento."""

from dataclasses import dataclass
from uuid import uuid4

from fastapi import UploadFile

from src.core.exceptions import BadRequestError
from src.storage.images import WEBP_CONTENT_TYPE, optimize_to_webp
from src.storage.interfaces import FileStorage

# Máximo de fotografías por galería (la primera es la principal).
MAX_GALLERY_PHOTOS = 4
_BYTES_PER_MB = 1024 * 1024


@dataclass(frozen=True)
class GalleryPhoto:
    """Fotografía recibida en un formulario, ya leída en memoria."""

    content: bytes
    content_type: str

    def optimized(self, max_size_mb: int) -> "GalleryPhoto":
        """Valida tamaño y contenido y devuelve la versión WebP optimizada."""
        if not self.content:
            raise BadRequestError("La fotografía está vacía", "Uploaded file has no content.")
        if len(self.content) > max_size_mb * _BYTES_PER_MB:
            raise BadRequestError(
                f"Cada fotografía puede pesar como máximo {max_size_mb} MB",
                f"Uploaded file has {len(self.content)} bytes.",
            )
        return GalleryPhoto(content=optimize_to_webp(self.content), content_type=WEBP_CONTENT_TYPE)


async def read_uploads(files: list[UploadFile] | None) -> list[GalleryPhoto]:
    """Lee en memoria los archivos de un formulario multipart."""
    return [
        GalleryPhoto(content=await file.read(), content_type=file.content_type or "")
        for file in files or []
    ]


def ensure_photo_count(count: int, owner: str) -> None:
    """Toda galería debe tener entre 1 y MAX_GALLERY_PHOTOS fotos. `owner`: "La mascota"."""
    if count < 1:
        raise BadRequestError(
            f"{owner} debe tener al menos una fotografía", "A gallery needs at least one photo."
        )
    if count > MAX_GALLERY_PHOTOS:
        raise BadRequestError(
            f"{owner} puede tener como máximo {MAX_GALLERY_PHOTOS} fotografías",
            f"Got {count} photos.",
        )


class PhotoGalleryStore:
    """Optimiza las fotos a WebP y las guarda o elimina bajo `{folder}/{owner_id}/`."""

    def __init__(self, storage: FileStorage, max_size_mb: int, folder: str) -> None:
        self._storage = storage
        self._max_size_mb = max_size_mb
        self._folder = folder

    async def upload_all(self, owner_id: str, photos: list[GalleryPhoto]) -> list[str]:
        """Sube las fotos y devuelve sus URLs; si una falla, borra las ya subidas."""
        # Se validan y optimizan todas antes de subir la primera.
        optimized = [photo.optimized(self._max_size_mb) for photo in photos]
        urls: list[str] = []
        try:
            for photo in optimized:
                # Ruta única dentro del bucket; no usa el nombre original del archivo.
                path = f"{self._folder}/{owner_id}/{uuid4().hex}.webp"
                urls.append(await self._storage.upload(path, photo.content, photo.content_type))
        except Exception:
            await self.delete_all(urls)
            raise
        return urls

    async def delete_all(self, urls: list[str]) -> None:
        for url in urls:
            await self._storage.delete(url)


def apply_gallery_changes(
    current: list[str], remove: list[str], added_count: int, owner: str
) -> tuple[list[str], list[str]]:
    """Devuelve (fotos que se conservan, fotos quitadas) y valida el total resultante."""
    kept = [url for url in current if url not in set(remove)]
    removed = [url for url in current if url not in kept]
    ensure_photo_count(len(kept) + added_count, owner)
    return kept, removed
