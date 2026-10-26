from collections.abc import Sequence

from src.core.exceptions import NotFoundError
from src.core.ids import generate_id
from src.modules.shelters.interfaces import ShelterNameSync, ShelterRepositoryPort
from src.modules.shelters.model import Shelter
from src.modules.shelters.schemas import ShelterCreate, ShelterUpdate
from src.storage.gallery import (
    GalleryPhoto,
    PhotoGalleryStore,
    apply_gallery_changes,
    ensure_photo_count,
)

GALLERY_OWNER = "El refugio"


class ShelterService:
    def __init__(
        self,
        shelters: ShelterRepositoryPort,
        photos: PhotoGalleryStore,
        name_syncs: Sequence[ShelterNameSync] = (),
    ) -> None:
        self._shelters = shelters
        self._photos = photos
        self._name_syncs = name_syncs

    async def list_shelters(self) -> list[Shelter]:
        return await self._shelters.find_all()

    async def get_shelter(self, shelter_id: str) -> Shelter:
        shelter = await self._shelters.get(shelter_id)
        if shelter is None:
            raise NotFoundError(
                "No se encontró el refugio con el ID especificado",
                f"Shelter with ID {shelter_id} was not found in table 'shelters'.",
            )
        return shelter

    async def create_shelter(self, payload: ShelterCreate, photos: list[GalleryPhoto]) -> Shelter:
        ensure_photo_count(len(photos), GALLERY_OWNER)
        shelter_id = generate_id("s")
        urls = await self._photos.upload_all(shelter_id, photos)
        shelter = Shelter(id=shelter_id, image=urls[0], photos=urls, **payload.model_dump())
        try:
            return await self._shelters.save(shelter)
        except Exception:
            await self._photos.delete_all(urls)
            raise

    async def update_shelter(
        self,
        shelter_id: str,
        payload: ShelterUpdate,
        new_photos: list[GalleryPhoto],
        remove_photos: list[str],
    ) -> Shelter:
        """Aplica solo los campos enviados (delta) y los cambios de la galería."""
        shelter = await self.get_shelter(shelter_id)
        changes = payload.model_dump(exclude_unset=True)
        kept, removed = apply_gallery_changes(
            list(shelter.photos or [shelter.image]), remove_photos, len(new_photos), GALLERY_OWNER
        )
        added = await self._photos.upload_all(shelter_id, new_photos)
        if added or removed:
            changes["photos"] = kept + added
            changes["image"] = changes["photos"][0]

        for field, value in changes.items():
            setattr(shelter, field, value)
        if payload.name is not None:
            # El nombre está desnormalizado en otras tablas; se confirma en el mismo commit.
            for sync in self._name_syncs:
                await sync.rename_shelter(shelter_id, payload.name)
        try:
            shelter = await self._shelters.save(shelter)
        except Exception:
            await self._photos.delete_all(added)
            raise
        await self._photos.delete_all(removed)
        return shelter

    async def delete_shelter(self, shelter_id: str) -> None:
        shelter = await self.get_shelter(shelter_id)
        urls = list(shelter.photos or [shelter.image])
        await self._shelters.delete(shelter)
        await self._photos.delete_all(urls)
