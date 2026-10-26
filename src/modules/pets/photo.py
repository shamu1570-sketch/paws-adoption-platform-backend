"""Fotografías de mascotas: galería compartida (src/storage/gallery.py) bajo la carpeta `pets/`."""

from src.storage.gallery import (
    MAX_GALLERY_PHOTOS,
    GalleryPhoto,
    PhotoGalleryStore,
)
from src.storage.gallery import (
    ensure_photo_count as _ensure_gallery_count,
)
from src.storage.interfaces import FileStorage

MAX_PET_PHOTOS = MAX_GALLERY_PHOTOS
PetPhoto = GalleryPhoto


def ensure_photo_count(count: int) -> None:
    """Toda mascota debe tener entre 1 y MAX_PET_PHOTOS fotografías."""
    _ensure_gallery_count(count, "La mascota")


class PetPhotoStore(PhotoGalleryStore):
    def __init__(self, storage: FileStorage, max_size_mb: int) -> None:
        super().__init__(storage, max_size_mb, folder="pets")
