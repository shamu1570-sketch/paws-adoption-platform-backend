import pytest

from src.core.config import settings
from test.conftest import API, JPG, PASSWORD, PNG, REGISTRATION_KEY, FakeStorage

PAYLOAD_KEYS = {"statusCode", "status", "message", "data", "detailError"}

SHELTER = {
    "name": "Refugio Esperanza",
    "address": "Calle 1",
    "city": "Puebla",
    "phone": "+52 22 0000 0000",
    "email": "hola@esperanza.org",
    "website": "",
    "capacity": "20",
    "description": "Refugio de prueba.",
    "verified": "true",
}

PET_FORM = {
    "name": "Molly",
    "type": "perro",
    "breed": "Poodle Mix",
    "ageValue": "2",
    "ageUnit": "años",
    "gender": "hembra",
    "size": "pequeño",
    "personality": ["Cariñosa", "Tranquila"],
    "description": "Perrita dulce ideal para departamento.",
    "story": "Rescatada de la calle.",
    "vaccinated": "true",
    "dewormed": "true",
    "sterilized": "false",
    "healthStatus": "Sana y llena de energía",
}

ADOPTION = {
    "userName": "Carlos Ramírez",
    "userEmail": "carlos.ramirez@example.com",
    "userPhone": "+52 55 9988 7766",
    "houseType": "departamento",
    "hasOtherPets": False,
    "reason": "Quiero brindarle un hogar amoroso.",
}

SURRENDER = {
    "petName": "Bubu",
    "petType": "gato",
    "petAgeValue": 3,
    "petAgeUnit": "años",
    "userName": "Ana Ruiz",
    "userEmail": "ana@example.com",
    "userPhone": "+52 55 1111 2222",
    "reason": "Alergia severa.",
    "healthCondition": "Sano.",
}

# Toda decisión sobre una solicitud exige una nota del administrador.
NOTE = {"adminNotes": "Nota de prueba para el solicitante."}


def assert_payload(response, status_code, status):
    body = response.json()
    assert response.status_code == status_code, body
    assert set(body) == PAYLOAD_KEYS
    assert body["statusCode"] == status_code
    assert body["status"] == status
    if status_code < 400:
        assert body["detailError"] is None
    else:
        assert body["data"] is None
        assert body["detailError"]
    return body["data"]


async def create_shelter(client, headers, **overrides):
    response = await client.post(
        f"{API}/shelters", data={**SHELTER, **overrides}, files={"photos": PNG}, headers=headers
    )
    return assert_payload(response, 201, "CREATED")


async def create_pet(client, headers, **overrides):
    response = await client.post(
        f"{API}/pets", data={**PET_FORM, **overrides}, files={"photos": PNG}, headers=headers
    )
    return assert_payload(response, 201, "CREATED")


# ---------------------------------------------------------------- autenticación


async def test_database_starts_empty(client):
    for resource in ("pets", "shelters", "testimonials"):
        assert assert_payload(await client.get(f"{API}/{resource}"), 200, "OK") == []


async def test_register_admin_requires_key_or_super_admin(client, super_admin, adoption_admin):
    new_admin = {"email": "nuevo@huellitas-test.org", "fullName": "Nuevo", "password": PASSWORD}
    url = f"{API}/auth/register-admin"

    assert_payload(await client.post(url, json=new_admin), 403, "FORBIDDEN")
    wrong_key = {"X-Admin-Registration-Key": "incorrecta"}
    assert_payload(await client.post(url, json=new_admin, headers=wrong_key), 403, "FORBIDDEN")
    assert_payload(await client.post(url, json=new_admin, headers=adoption_admin), 403, "FORBIDDEN")

    created = assert_payload(
        await client.post(url, json=new_admin, headers=super_admin), 201, "CREATED"
    )
    assert created["role"] == "adoption_admin" and created["isActive"] is True
    assert "password" not in created and "passwordHash" not in created

    assert_payload(await client.post(url, json=new_admin, headers=super_admin), 409, "CONFLICT")


async def test_register_admin_validation(client):
    headers = {"X-Admin-Registration-Key": REGISTRATION_KEY}
    url = f"{API}/auth/register-admin"
    valid = {"email": "a@huellitas-test.org", "fullName": "A", "password": PASSWORD}
    for invalid in ({"password": "corta"}, {"email": "no-es-correo"}, {"role": "root"}):
        response = await client.post(url, json={**valid, **invalid}, headers=headers)
        assert_payload(response, 400, "BAD_REQUEST")


async def test_login_and_session(client, super_admin):
    credentials = {"email": "SUPER@huellitas-test.org", "password": PASSWORD}
    token = assert_payload(await client.post(f"{API}/auth/login", json=credentials), 200, "OK")
    assert token["tokenType"] == "bearer" and token["expiresIn"] > 0
    assert token["admin"]["email"] == "super@huellitas-test.org"
    assert token["admin"]["role"] == "super_admin"

    me = assert_payload(await client.get(f"{API}/auth/me", headers=super_admin), 200, "OK")
    assert me["email"] == "super@huellitas-test.org"

    for wrong in ({"password": "otra-clave"}, {"email": "nadie@huellitas-test.org"}):
        response = await client.post(f"{API}/auth/login", json={**credentials, **wrong})
        assert_payload(response, 401, "UNAUTHORIZED")
        assert response.json()["message"] == "Correo o contraseña incorrectos"

    assert_payload(await client.get(f"{API}/auth/me"), 401, "UNAUTHORIZED")
    bad_token = {"Authorization": "Bearer no.es.un-jwt"}
    assert_payload(await client.get(f"{API}/auth/me", headers=bad_token), 401, "UNAUTHORIZED")


@pytest.mark.parametrize(
    ("method", "path"),
    [
        ("POST", "/pets"),
        ("PATCH", "/pets/x"),
        ("DELETE", "/pets/x"),
        ("POST", "/shelters"),
        ("PATCH", "/shelters/x"),
        ("DELETE", "/shelters/x"),
        ("GET", "/adoptions"),
        ("PATCH", "/adoptions/x/status"),
        ("GET", "/surrender-requests"),
        ("PATCH", "/surrender-requests/x/status"),
        ("GET", "/admin/metrics"),
    ],
)
async def test_admin_endpoints_reject_anonymous_requests(client, method, path):
    assert_payload(await client.request(method, f"{API}{path}"), 401, "UNAUTHORIZED")


# --------------------------------------------------------------------- mascotas


async def test_create_pet_uploads_photo_and_stores_public_url(client, adoption_admin, storage):
    shelter = await create_shelter(client, adoption_admin)
    pet = await create_pet(client, adoption_admin, shelterId=shelter["id"])

    assert pet["image"].startswith(FakeStorage.BASE_URL + f"pets/{pet['id']}/")
    assert pet["image"].endswith(".webp") and pet["photos"] == [pet["image"]]
    stored = [data for path, data in storage.files.items() if path.startswith("pets/")]
    assert len(stored) == 1 and stored[0][:4] == b"RIFF" and stored[0][8:12] == b"WEBP"
    assert pet["personality"] == ["Cariñosa", "Tranquila"]
    assert pet["vaccinated"] is True and pet["sterilized"] is False
    assert pet["adoptionStatus"] == "disponible"
    assert pet["shelterName"] == "Refugio Esperanza"
    assert pet["ageCategory"] == "joven" and pet["createdAt"]

    listed = assert_payload(await client.get(f"{API}/pets"), 200, "OK")
    assert [item["id"] for item in listed] == [pet["id"]]
    assert assert_payload(await client.get(f"{API}/pets/{pet['id']}"), 200, "OK") == pet


async def test_create_pet_validation(client, adoption_admin, storage):
    url = f"{API}/pets"
    response = await client.post(url, data=PET_FORM, headers=adoption_admin)
    assert_payload(response, 400, "BAD_REQUEST")
    assert "'photos'" in response.json()["message"]

    pdf = {"photos": ("doc.pdf", b"%PDF", "application/pdf")}
    response = await client.post(url, data=PET_FORM, files=pdf, headers=adoption_admin)
    assert_payload(response, 400, "BAD_REQUEST")

    empty = {"photos": ("vacia.png", b"", "image/png")}
    response = await client.post(url, data=PET_FORM, files=empty, headers=adoption_admin)
    assert_payload(response, 400, "BAD_REQUEST")

    for invalid in ({"size": "enorme"}, {"name": "  "}, {"shelterId": "no-existe"}):
        response = await client.post(
            url, data={**PET_FORM, **invalid}, files={"photos": PNG}, headers=adoption_admin
        )
        assert_payload(response, 400, "BAD_REQUEST")
    assert storage.files == {}


async def test_photo_size_limit(client, adoption_admin, monkeypatch):
    monkeypatch.setattr(settings, "MAX_PHOTO_SIZE_MB", 0)
    response = await client.post(
        f"{API}/pets", data=PET_FORM, files={"photos": PNG}, headers=adoption_admin
    )
    assert_payload(response, 400, "BAD_REQUEST")


async def test_update_pet_fields_and_photo(client, adoption_admin, storage):
    pet = await create_pet(client, adoption_admin)
    url = f"{API}/pets/{pet['id']}"

    updated = assert_payload(
        await client.patch(url, data={"adoptionStatus": "en_proceso"}, headers=adoption_admin),
        200,
        "OK",
    )
    assert updated["adoptionStatus"] == "en_proceso"
    assert updated["name"] == "Molly" and updated["image"] == pet["image"]
    assert updated["personality"] == ["Cariñosa", "Tranquila"]
    assert storage.deleted == []

    replace = {"name": "Molly Bella", "removePhotos": pet["image"]}
    updated = assert_payload(
        await client.patch(url, data=replace, files={"photos": JPG}, headers=adoption_admin),
        200,
        "OK",
    )
    assert updated["name"] == "Molly Bella"
    assert updated["image"] != pet["image"] and updated["image"].endswith(".webp")
    assert storage.deleted == [pet["image"]]

    response = await client.patch(url, data={"type": "loro"}, headers=adoption_admin)
    assert_payload(response, 400, "BAD_REQUEST")
    response = await client.patch(f"{API}/pets/no-existe", data={}, headers=adoption_admin)
    assert_payload(response, 404, "NOT_FOUND")


async def test_delete_pet_removes_photo(client, adoption_admin, storage):
    pet = await create_pet(client, adoption_admin)
    url = f"{API}/pets/{pet['id']}"
    deleted = assert_payload(await client.delete(url, headers=adoption_admin), 200, "OK")
    assert deleted == {"id": pet["id"], "deleted": True}
    assert storage.deleted == [pet["image"]]
    assert_payload(await client.get(url), 404, "NOT_FOUND")
    assert_payload(await client.delete(url, headers=adoption_admin), 404, "NOT_FOUND")


async def test_list_pets_filters(client, adoption_admin):
    shelter = await create_shelter(client, adoption_admin)
    await create_pet(client, adoption_admin, shelterId=shelter["id"])
    await create_pet(client, adoption_admin, name="Simba", type="gato", breed="Común Naranja")

    async def names(query):
        data = assert_payload(await client.get(f"{API}/pets?{query}"), 200, "OK")
        return sorted(pet["name"] for pet in data)

    assert await names("type=gato") == ["Simba"]
    assert await names(f"shelterId={shelter['id']}") == ["Molly"]
    assert await names("search=naranja") == ["Simba"]
    assert await names("ageCategory=joven&gender=hembra") == ["Molly", "Simba"]
    assert await names("adoptionStatus=adoptado") == []
    assert_payload(await client.get(f"{API}/pets?size=enorme"), 400, "BAD_REQUEST")


# --------------------------------------------------------------------- refugios


async def test_shelter_crud_and_roles(client, super_admin, adoption_admin):
    shelter = await create_shelter(client, adoption_admin)
    assert shelter["website"] is None and shelter["currentPetCount"] == 0
    url = f"{API}/shelters/{shelter['id']}"
    assert assert_payload(await client.get(url), 200, "OK") == shelter
    assert_payload(await client.get(f"{API}/shelters/no-existe"), 404, "NOT_FOUND")

    bad_email = {**SHELTER, "email": "no-es-email"}
    response = await client.post(
        f"{API}/shelters", data=bad_email, files={"photos": PNG}, headers=adoption_admin
    )
    assert_payload(response, 400, "BAD_REQUEST")
    response = await client.patch(url, data={"name": "#1"}, headers=adoption_admin)
    assert_payload(response, 400, "BAD_REQUEST")

    pet = await create_pet(client, adoption_admin, shelterId=shelter["id"])
    renamed = {"name": "Refugio Renombrado"}
    response = await client.patch(url, data=renamed, headers=adoption_admin)
    updated = assert_payload(response, 200, "OK")
    assert updated["name"] == "Refugio Renombrado" and updated["city"] == "Puebla"
    pet = assert_payload(await client.get(f"{API}/pets/{pet['id']}"), 200, "OK")
    assert pet["shelterName"] == "Refugio Renombrado"

    assert_payload(await client.delete(url, headers=adoption_admin), 403, "FORBIDDEN")
    deleted = assert_payload(await client.delete(url, headers=super_admin), 200, "OK")
    assert deleted == {"id": shelter["id"], "deleted": True}
    pet = assert_payload(await client.get(f"{API}/pets/{pet['id']}"), 200, "OK")
    assert pet["shelterId"] is None


# ------------------------------------------------------------------ solicitudes


async def test_adoption_flow(client, adoption_admin):
    shelter = await create_shelter(client, adoption_admin)
    pet = await create_pet(client, adoption_admin, shelterId=shelter["id"])
    url = f"{API}/adoptions"

    created = assert_payload(
        await client.post(url, json={**ADOPTION, "petId": pet["id"]}), 201, "CREATED"
    )
    assert created["status"] == "pendiente"
    assert created["petName"] == "Molly" and created["petImage"] == pet["image"]
    assert created["shelterId"] == shelter["id"]

    assert_payload(
        await client.post(url, json={**ADOPTION, "petId": "no-existe"}), 404, "NOT_FOUND"
    )
    invalid = {**ADOPTION, "petId": pet["id"], "userEmail": "malo"}
    response = await client.post(url, json=invalid)
    assert_payload(response, 400, "BAD_REQUEST")
    assert response.json()["message"] == "El campo 'userEmail' no cumple con un formato válido"

    lookup = {"trackingCode": created["trackingCode"].lower(), "email": ADOPTION["userEmail"]}
    tracking = assert_payload(await client.post(f"{url}/track", json=lookup), 200, "OK")
    assert tracking["status"] == "pendiente" and tracking["petName"] == "Molly"
    assert "userEmail" not in tracking and tracking["adminNotes"] is None
    wrong_email = {**lookup, "email": "otra@ejemplo.org"}
    assert_payload(await client.post(f"{url}/track", json=wrong_email), 404, "NOT_FOUND")

    listed = assert_payload(await client.get(url, headers=adoption_admin), 200, "OK")
    assert [request["id"] for request in listed] == [created["id"]]
    assert listed[0]["userEmail"] == ADOPTION["userEmail"]

    decision = {"status": "aprobado", "adminNotes": "Cumple requisitos."}
    status_url = f"{url}/{created['id']}/status"
    updated = assert_payload(
        await client.patch(status_url, json=decision, headers=adoption_admin), 200, "OK"
    )
    assert updated["status"] == "aprobado" and updated["adminNotes"] == "Cumple requisitos."

    response = await client.patch(status_url, json={"status": "quizas"}, headers=adoption_admin)
    assert_payload(response, 400, "BAD_REQUEST")
    response = await client.patch(
        f"{url}/no-existe/status", json={**NOTE, "status": "rechazado"}, headers=adoption_admin
    )
    assert_payload(response, 404, "NOT_FOUND")

    query = f"?shelterId={shelter['id']}&status=aprobado"
    assert (
        len(assert_payload(await client.get(url + query, headers=adoption_admin), 200, "OK")) == 1
    )
    pending = await client.get(f"{url}?status=pendiente", headers=adoption_admin)
    assert assert_payload(pending, 200, "OK") == []


async def test_surrender_flow(client, adoption_admin):
    shelter = await create_shelter(client, adoption_admin)
    url = f"{API}/surrender-requests"

    created = assert_payload(
        await client.post(url, json={**SURRENDER, "shelterId": shelter["id"]}), 201, "CREATED"
    )
    assert created["status"] == "pendiente" and created["shelterName"] == "Refugio Esperanza"

    assert_payload(await client.post(url, json={**SURRENDER, "shelterId": ""}), 400, "BAD_REQUEST")
    assert_payload(await client.post(url, json={**SURRENDER, "shelterId": "x"}), 404, "NOT_FOUND")

    listed = assert_payload(await client.get(url, headers=adoption_admin), 200, "OK")
    assert [request["id"] for request in listed] == [created["id"]]

    updated = assert_payload(
        await client.patch(
            f"{url}/{created['id']}/status",
            json={**NOTE, "status": "rechazado"},
            headers=adoption_admin,
        ),
        200,
        "OK",
    )
    assert updated["status"] == "rechazado" and updated["adminNotes"] == NOTE["adminNotes"]
    response = await client.patch(
        f"{url}/no-existe/status", json={**NOTE, "status": "aprobado"}, headers=adoption_admin
    )
    assert_payload(response, 404, "NOT_FOUND")


# --------------------------------------------------------------------- métricas


async def test_metrics(client, adoption_admin):
    shelter = await create_shelter(client, adoption_admin)
    other = await create_shelter(client, adoption_admin, name="Otro Refugio")
    pet = await create_pet(client, adoption_admin, shelterId=shelter["id"])
    adopted = await create_pet(client, adoption_admin, shelterId=other["id"])
    await client.patch(
        f"{API}/pets/{adopted['id']}", data={"adoptionStatus": "adoptado"}, headers=adoption_admin
    )
    await client.post(f"{API}/adoptions", json={**ADOPTION, "petId": pet["id"]})
    await client.post(f"{API}/surrender-requests", json={**SURRENDER, "shelterId": other["id"]})

    url = f"{API}/admin/metrics"
    assert assert_payload(await client.get(url, headers=adoption_admin), 200, "OK") == {
        "totalPets": 2,
        "availablePets": 1,
        "adoptedPets": 1,
        "pendingAdoptions": 1,
        "inReviewAdoptions": 1,
        "pendingSurrenders": 1,
        "unreadMessages": 0,
        "activeShelters": 2,
    }
    scoped = await client.get(f"{url}?shelterId={shelter['id']}", headers=adoption_admin)
    assert assert_payload(scoped, 200, "OK") == {
        "totalPets": 1,
        "availablePets": 1,
        "adoptedPets": 0,
        "pendingAdoptions": 1,
        "inReviewAdoptions": 1,
        "pendingSurrenders": 0,
        "unreadMessages": 0,
        "activeShelters": 1,
    }


# ---------------------------------------------------------------------- errores


async def test_http_errors_use_response_payload(client):
    assert_payload(await client.get(f"{API}/no-existe"), 404, "NOT_FOUND")
    assert_payload(await client.post(f"{API}/testimonials"), 405, "METHOD_NOT_ALLOWED")


@pytest.mark.parametrize(
    ("debug", "detail"),
    [(True, "RuntimeError: Database connection timeout"), (False, "RuntimeError")],
)
async def test_unexpected_errors_use_response_payload(client, monkeypatch, debug, detail):
    async def boom(_self):
        raise RuntimeError("Database connection timeout")

    monkeypatch.setattr(
        "src.modules.testimonials.service.TestimonialService.list_testimonials", boom
    )
    monkeypatch.setattr(settings, "DEBUG", debug)
    body = (await client.get(f"{API}/testimonials")).json()
    assert body == {
        "statusCode": 500,
        "status": "INTERNAL_SERVER_ERROR",
        "message": "Ha ocurrido un error inesperado en el servidor",
        "data": None,
        "detailError": detail,
    }


async def test_health_root_and_cors(client):
    assert assert_payload(await client.get(f"{API}/health"), 200, "OK") == {"database": "up"}
    assert (await client.get("/")).status_code == 200
    response = await client.options(
        f"{API}/pets",
        headers={
            "Origin": "http://localhost:3000",
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "authorization",
        },
    )
    assert response.headers["access-control-allow-origin"] == "http://localhost:3000"
