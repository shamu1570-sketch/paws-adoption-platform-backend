"""Pruebas unitarias de los servicios con repositorios en memoria (sin base de datos ni HTTP)."""

import httpx
import pytest

from src.core.exceptions import (
    BadRequestError,
    ConflictError,
    ForbiddenError,
    ServiceUnavailableError,
    UnauthorizedError,
)
from src.core.security import create_access_token, verify_password
from src.modules.auth.model import Admin
from src.modules.auth.schemas import AdminRegister, AdminRole, LoginRequest
from src.modules.auth.service import AuthService
from src.modules.pets.interfaces import PetReferences
from src.modules.pets.photo import PetPhoto, PetPhotoStore
from src.modules.pets.schemas import PetCreate, PetUpdate
from src.modules.pets.service import PetService
from src.modules.shelters.model import Shelter
from src.storage.supabase import SupabaseStorage, UnconfiguredStorage
from test.conftest import PNG, FakeStorage

PASSWORD = "Sup3rSecreta!"
# Quien registra en estas pruebas: un super administrador con sesión.
ROOT = Admin(id="root", role=AdminRole.SUPER_ADMIN)


class InMemoryRepository:
    def __init__(self, *entities) -> None:
        self.items = {entity.id: entity for entity in entities}

    async def get(self, entity_id):
        return self.items.get(entity_id)

    async def save(self, entity):
        self.items[entity.id] = entity
        return entity

    async def delete(self, entity) -> None:
        del self.items[entity.id]

    async def find_all(self, _filters=None):
        return list(self.items.values())

    async def exists_with_role(self, role):
        return any(item.role == role for item in self.items.values())

    async def sync_pet_snapshot(self, *_args):
        return None

    async def missing(self, _names):
        return []

    async def exists(self, *_args):
        return True

    async def find_by_email(self, email):
        return next((item for item in self.items.values() if item.email == email.lower()), None)


@pytest.fixture
def auth():
    return AuthService(InMemoryRepository(), InMemoryRepository())


async def test_register_hashes_password_and_normalizes_email(auth):
    payload = AdminRegister(email="Ana@Huellitas-Test.org", full_name="Ana", password=PASSWORD)
    admin = await auth.register_admin(payload, ROOT)

    assert admin.email == "ana@huellitas-test.org"
    assert admin.role == AdminRole.ADOPTION_ADMIN
    assert admin.password_hash != PASSWORD
    assert admin.password_hash.startswith("$2")
    assert verify_password(PASSWORD, admin.password_hash)
    with pytest.raises(ConflictError):
        await auth.register_admin(payload, ROOT)


async def test_login_and_authenticate(auth):
    admin = await auth.register_admin(
        AdminRegister(email="ana@huellitas-test.org", full_name="Ana", password=PASSWORD), ROOT
    )
    token = await auth.login(LoginRequest(email="ana@huellitas-test.org", password=PASSWORD))
    assert (await auth.authenticate(token.access_token)).id == admin.id

    with pytest.raises(UnauthorizedError):
        await auth.login(LoginRequest(email="ana@huellitas-test.org", password="incorrecta"))
    with pytest.raises(UnauthorizedError):
        await auth.authenticate(create_access_token("no-existe", AdminRole.SUPER_ADMIN))

    # Cuenta desactivada: 403 "Acceso suspendido o expirado", al entrar y con el token vigente.
    admin.is_active = False
    with pytest.raises(ForbiddenError):
        await auth.login(LoginRequest(email="ana@huellitas-test.org", password=PASSWORD))
    with pytest.raises(ForbiddenError):
        await auth.authenticate(token.access_token)


def pet_payload(**overrides) -> PetCreate:
    data = {
        "name": "Toby",
        "type": "perro",
        "breed": "Mestizo",
        "age_value": 4,
        "age_unit": "meses",
        "gender": "macho",
        "size": "mediano",
        "description": "Alegre.",
        "story": "Rescatado.",
        "health_status": "Sano.",
    }
    return PetCreate(**{**data, **overrides})


async def test_pet_service_resolves_shelter_and_stores_only_the_url():
    storage = FakeStorage()
    shelter = Shelter(id="s1", name="Refugio Uno")
    references = PetReferences(
        shelters=InMemoryRepository(shelter),
        surrenders=InMemoryRepository(),
        personalities=InMemoryRepository(),
        breeds=InMemoryRepository(),
        snapshots=InMemoryRepository(),
    )
    service = PetService(InMemoryRepository(), references, PetPhotoStore(storage, 5))
    photo = PetPhoto(content=PNG[1], content_type=PNG[2])

    pet = await service.create_pet(pet_payload(shelter_id="s1"), [photo])
    assert pet.shelter_name == "Refugio Uno"
    assert pet.image == f"{FakeStorage.BASE_URL}pets/{pet.id}/{pet.image.rsplit('/', 1)[1]}"
    assert pet.image.endswith(".webp")

    pet = await service.update_pet(pet.id, PetUpdate(shelter_id=None), [], [])
    assert pet.shelter_id is None and pet.shelter_name is None

    with pytest.raises(BadRequestError):
        await service.create_pet(pet_payload(shelter_id="no-existe"), [photo])


async def test_storage_without_configuration_refuses_uploads():
    storage = UnconfiguredStorage()
    with pytest.raises(ServiceUnavailableError):
        await storage.upload("pets/1/a.png", b"x", "image/png")
    await storage.delete("https://example.com/a.png")


async def test_supabase_storage_builds_urls_and_reports_failures(monkeypatch):
    calls = []

    class FakeResponse:
        def __init__(self, status_code):
            self.status_code = status_code
            self.text = "bucket not found"

        def raise_for_status(self):
            if self.status_code >= 400:
                request = httpx.Request("POST", "http://supabase.test")
                raise httpx.HTTPStatusError("error", request=request, response=self)

    class FakeClient:
        status_code = 200

        def __init__(self, **_kwargs):
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, *_args):
            return False

        async def post(self, url, content, headers):
            calls.append(("POST", url, headers["Content-Type"], headers["Authorization"]))
            return FakeResponse(self.status_code)

        async def delete(self, url, headers):
            calls.append(("DELETE", url))
            return FakeResponse(self.status_code)

    monkeypatch.setattr("src.storage.supabase.httpx.AsyncClient", FakeClient)
    storage = SupabaseStorage("http://supabase.test/", "service-key", "pet-photos")

    url = await storage.upload("pets/1/a.png", b"x", "image/png")
    assert url == "http://supabase.test/storage/v1/object/public/pet-photos/pets/1/a.png"
    assert calls == [
        (
            "POST",
            "http://supabase.test/storage/v1/object/pet-photos/pets/1/a.png",
            "image/png",
            "Bearer service-key",
        )
    ]

    await storage.delete(url)
    await storage.delete("https://images.unsplash.com/otra.jpg")
    assert calls[1:] == [
        ("DELETE", "http://supabase.test/storage/v1/object/pet-photos/pets/1/a.png")
    ]

    FakeClient.status_code = 404
    with pytest.raises(ServiceUnavailableError):
        await storage.upload("pets/1/b.png", b"x", "image/png")
    await storage.delete(url)
