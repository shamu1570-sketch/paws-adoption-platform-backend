import io

import pytest
from httpx import ASGITransport, AsyncClient
from PIL import Image
from sqlalchemy import event
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from src.core.config import settings
from src.database.connection import get_db
from src.database.init_db import create_tables
from src.main import app
from src.modules.breeds.model import Breed
from src.modules.personalities.model import Personality
from src.storage.dependencies import get_file_storage

API = settings.API_PREFIX
REGISTRATION_KEY = "test-registration-key"
PASSWORD = "Sup3rSecreta!"


def _image_bytes(image_format: str) -> bytes:
    """Imagen real mínima: la API la valida y convierte a WebP con Pillow."""
    buffer = io.BytesIO()
    Image.new("RGB", (32, 24), (222, 46, 3)).save(buffer, format=image_format)
    return buffer.getvalue()


PNG = ("toby.png", _image_bytes("PNG"), "image/png")
JPG = ("toby.jpg", _image_bytes("JPEG"), "image/jpeg")
# Rasgos que usan las fichas de prueba; deben existir en el catálogo.
PERSONALITIES = ("Cariñosa", "Tranquila")
# Razas que usan las fichas de prueba, por especie.
BREEDS = (("Poodle Mix", "perro"), ("Común Naranja", "gato"))


class FakeStorage:
    """Almacenamiento en memoria: registra lo subido y lo eliminado."""

    BASE_URL = "https://storage.test/pet-photos/"

    def __init__(self) -> None:
        self.files: dict[str, bytes] = {}
        self.deleted: list[str] = []

    async def upload(self, path: str, content: bytes, content_type: str) -> str:
        self.files[path] = content
        return f"{self.BASE_URL}{path}"

    async def delete(self, public_url: str) -> None:
        self.deleted.append(public_url)


@pytest.fixture
def storage():
    return FakeStorage()


@pytest.fixture
async def client(storage, monkeypatch):
    """Cliente HTTP contra la app con una base SQLite en memoria vacía."""
    engine = create_async_engine(
        "sqlite+aiosqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    event.listen(
        engine.sync_engine, "connect", lambda conn, _: conn.execute("PRAGMA foreign_keys=ON")
    )
    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    await create_tables(engine)
    async with session_factory() as session:
        session.add_all(Personality(id=name, name=name) for name in PERSONALITIES)
        session.add_all(Breed(id=name, name=name, species=species) for name, species in BREEDS)
        await session.commit()

    async def override_get_db():
        async with session_factory() as session:
            yield session

    monkeypatch.setattr(settings, "ADMIN_REGISTRATION_KEY", REGISTRATION_KEY)
    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_file_storage] = lambda: storage
    transport = ASGITransport(app=app, raise_app_exceptions=False)
    async with AsyncClient(transport=transport, base_url="http://test") as http_client:
        yield http_client
    app.dependency_overrides.clear()
    await engine.dispose()


async def register_and_login(client, email: str, role: str, headers=None) -> dict[str, str]:
    """Registra un administrador (con la llave o con `headers`) y devuelve su sesión."""
    response = await client.post(
        f"{API}/auth/register-admin",
        json={"email": email, "fullName": "Admin de Prueba", "password": PASSWORD, "role": role},
        headers=headers or {"X-Admin-Registration-Key": REGISTRATION_KEY},
    )
    assert response.status_code == 201, response.text
    response = await client.post(f"{API}/auth/login", json={"email": email, "password": PASSWORD})
    assert response.status_code == 200, response.text
    return {"Authorization": f"Bearer {response.json()['data']['accessToken']}"}


@pytest.fixture
async def super_admin(client) -> dict[str, str]:
    return await register_and_login(client, "super@huellitas-test.org", "super_admin")


@pytest.fixture
async def adoption_admin(client, super_admin) -> dict[str, str]:
    return await register_and_login(
        client, "adopciones@huellitas-test.org", "adoption_admin", super_admin
    )
