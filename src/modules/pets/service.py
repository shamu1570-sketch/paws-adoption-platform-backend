from uuid import uuid4

from src.core.exceptions import BadRequestError, ConflictError, NotFoundError
from src.core.schemas import RequestStatus
from src.modules.auth.access import GLOBAL_SCOPE, AdminScope
from src.modules.pets.interfaces import PetReferences, PetRepositoryPort
from src.modules.pets.life_stage import age_error, age_label, life_stage
from src.modules.pets.model import Pet
from src.modules.pets.photo import PetPhoto, PetPhotoStore, ensure_photo_count
from src.modules.pets.schemas import PetCreate, PetFilters, PetUpdate
from src.modules.surrender_requests.model import SurrenderRequest


class PetService:
    def __init__(
        self,
        pets: PetRepositoryPort,
        references: PetReferences,
        photos: PetPhotoStore,
    ) -> None:
        self._pets = pets
        self._shelters = references.shelters
        self._surrenders = references.surrenders
        self._personalities = references.personalities
        self._breeds = references.breeds
        self._snapshots = references.snapshots
        self._photos = photos

    async def list_pets(self, filters: PetFilters) -> list[Pet]:
        return await self._pets.find_all(filters)

    async def get_pet(self, pet_id: str, scope: AdminScope | None = None) -> Pet:
        """Devuelve la ficha; una mascota no publicada solo existe para los administradores
        que gestionan su refugio."""
        pet = await self._pets.get(pet_id)
        can_see_hidden = scope is not None and pet is not None and scope.can_access(pet.shelter_id)
        if pet is None or not (pet.is_visible or can_see_hidden):
            raise NotFoundError(
                "No se encontró la mascota con el ID especificado",
                f"Pet with ID {pet_id} was not found in table 'pets'.",
            )
        return pet

    async def create_pet(
        self, payload: PetCreate, photos: list[PetPhoto], scope: AdminScope = GLOBAL_SCOPE
    ) -> Pet:
        scope.ensure_access(payload.shelter_id)
        ensure_photo_count(len(photos))
        await self._ensure_personalities_exist(payload.personality)
        await self._ensure_breed_exists(payload.type, payload.breed)
        shelter_name = await self._resolve_shelter_name(payload.shelter_id)
        surrender = await self._get_receivable_surrender(payload.surrender_request_id)
        if surrender is not None:
            # La entrega debe ser de un refugio que gestione quien registra la ficha.
            scope.ensure_access(surrender.shelter_id)
        pet_id = str(uuid4())
        urls = await self._photos.upload_all(pet_id, photos)
        data = payload.model_dump(exclude={"surrender_request_id"})
        pet = Pet(
            id=pet_id,
            image=urls[0],
            photos=urls,
            shelter_name=shelter_name,
            **data,
            **self._derived_age(payload.age_value, payload.age_unit),
        )
        if surrender is not None:
            # Se confirma en el mismo commit que el alta: o quedan enlazadas o no se crea nada.
            surrender.pet_id = pet_id
        try:
            return await self._pets.save(pet)
        except Exception:
            await self._photos.delete_all(urls)
            raise

    async def update_pet(
        self,
        pet_id: str,
        payload: PetUpdate,
        new_photos: list[PetPhoto],
        remove_photos: list[str],
        scope: AdminScope = GLOBAL_SCOPE,
    ) -> Pet:
        """Aplica solo los campos enviados (delta) y los cambios de la galería."""
        pet = await self.get_pet(pet_id, scope)
        scope.ensure_access(pet.shelter_id)
        changes = payload.model_dump(exclude_unset=True)
        if "shelter_id" in changes:
            # Solo puede moverla a un refugio que también gestione.
            scope.ensure_access(changes["shelter_id"])
        await self._validate_changes(pet, changes)
        if "shelter_id" in payload.model_fields_set:
            changes["shelter_name"] = await self._resolve_shelter_name(payload.shelter_id)

        current = list(pet.photos or [pet.image])
        kept = [url for url in current if url not in set(remove_photos)]
        removed = [url for url in current if url not in kept]
        ensure_photo_count(len(kept) + len(new_photos))
        added = await self._photos.upload_all(pet_id, new_photos)
        if added or removed:
            changes["photos"] = kept + added
            changes["image"] = changes["photos"][0]

        for field, value in changes.items():
            setattr(pet, field, value)
        if "name" in changes or "image" in changes:
            # Las solicitudes guardan nombre y foto de la mascota: se mantienen al día
            # en el mismo commit para que todas las vistas muestren la ficha vigente.
            await self._snapshots.sync_pet_snapshot(pet.id, pet.name, pet.image)
        try:
            pet = await self._pets.save(pet)
        except Exception:
            await self._photos.delete_all(added)
            raise
        await self._photos.delete_all(removed)
        return pet

    async def delete_pet(self, pet_id: str, scope: AdminScope = GLOBAL_SCOPE) -> None:
        pet = await self.get_pet(pet_id, scope)
        scope.ensure_access(pet.shelter_id)
        urls = list(pet.photos or [pet.image])
        await self._pets.delete(pet)
        await self._photos.delete_all(urls)

    async def _validate_changes(self, pet: Pet, changes: dict) -> None:
        """Valida catálogo, raza y edad de una edición y agrega los campos derivados."""
        if "personality" in changes:
            await self._ensure_personalities_exist(changes["personality"])
        if "breed" in changes or "type" in changes:
            await self._ensure_breed_exists(
                changes.get("type", pet.type), changes.get("breed", pet.breed)
            )
        if "age_value" in changes or "age_unit" in changes:
            value = changes.get("age_value", pet.age_value)
            unit = changes.get("age_unit", pet.age_unit)
            error = age_error(value, unit)
            if error:
                raise BadRequestError(error, f"Invalid age: {value} {unit}.")
            changes.update(self._derived_age(value, unit))

    @staticmethod
    def _derived_age(value: int, unit: str) -> dict[str, str]:
        """Texto de la edad y etapa de vida: siempre se calculan, nunca se reciben."""
        return {"age": age_label(value, unit), "age_category": life_stage(value, unit)}

    async def _ensure_breed_exists(self, species: str, breed: str) -> None:
        if not await self._breeds.exists(species, breed):
            raise BadRequestError(
                f"La raza '{breed}' no está en el catálogo de {species}s",
                f"Unknown breed '{breed}' for species '{species}'.",
            )

    async def _ensure_personalities_exist(self, names: list[str]) -> None:
        missing = await self._personalities.missing(names)
        if missing:
            raise BadRequestError(
                f"Personalidades fuera del catálogo: {', '.join(missing)}",
                f"Unknown personalities: {missing}.",
            )

    async def _get_receivable_surrender(self, surrender_id: str | None) -> SurrenderRequest | None:
        """Valida que la entrega esté aprobada y aún no tenga una mascota registrada."""
        if surrender_id is None:
            return None
        surrender = await self._surrenders.get(surrender_id)
        if surrender is None:
            raise BadRequestError(
                "La solicitud de entrega indicada no existe",
                f"Surrender request with ID {surrender_id} was not found.",
            )
        if surrender.status != RequestStatus.APPROVED:
            raise ConflictError(
                "Solo se puede registrar la mascota de una entrega aprobada",
                f"Surrender request {surrender_id} has status '{surrender.status}'.",
            )
        if surrender.pet_id is not None:
            raise ConflictError(
                "La mascota de esta entrega ya fue registrada",
                f"Surrender request {surrender_id} is already linked to pet {surrender.pet_id}.",
            )
        return surrender

    async def _resolve_shelter_name(self, shelter_id: str | None) -> str | None:
        """Valida el refugio asignado y devuelve su nombre para guardarlo en la ficha."""
        if shelter_id is None:
            return None
        shelter = await self._shelters.get(shelter_id)
        if shelter is None:
            raise BadRequestError(
                "El refugio indicado en 'shelterId' no existe",
                f"Shelter with ID {shelter_id} was not found in table 'shelters'.",
            )
        return shelter.name
