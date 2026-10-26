# Prompt para Desarrollo del Backend - Sistema "Huellitas de Amor"

Actúa como un Desarrollador Backend Senior / Arquitecto de Software. Necesitamos construir un backend RESTful en Node.js (Express, NestJS, Spring Boot o similar) conectado a la base de datos PostgreSQL/MySQL estructurada en el archivo `schema.sql`.

---

## 1. Estándar Global de Respuesta (ResponsePayload)

**TODOS** los endpoints de la API deben retornar obligatoriamente el siguiente formato unificado de respuesta en formato JSON (`ResponsePayload`), garantizando consistencia en el consumo desde el frontend:

### Estructura TypeScript del ResponsePayload
```typescript
interface ResponsePayload<T> {
  statusCode: number;       // Código HTTP (200, 201, 400, 404, 500, etc.)
  status: string;           // Estado en texto ("OK", "CREATED", "BAD_REQUEST", "NOT_FOUND", "INTERNAL_SERVER_ERROR")
  message: string;          // Mensaje informativo legible para el cliente/usuario
  data: T | null;           // Objeto o lista de objetos retornados por la base de datos
  detailError: string | null; // Mensaje de error técnico detallado (solamente en caso de fallo)
}
```

### Ejemplos de Respuestas

#### Respuesta Exitosa de Consulta (HTTP 200 OK):
```json
{
  "statusCode": 200,
  "status": "OK",
  "message": "Mascotas obtenidas con éxito",
  "data": [
    {
      "id": "1",
      "name": "Toby",
      "type": "perro",
      "breed": "Golden Retriever Mix",
      "age": "4 meses",
      "ageCategory": "cachorro",
      "gender": "macho",
      "size": "mediano",
      "personality": ["Juguetón", "Sociable", "Inteligente"],
      "description": "Un cachorro sumamente alegre...",
      "story": "Toby fue encontrado junto a sus hermanitos...",
      "image": "https://images.unsplash.com/photo-1552053831-71594a27632d",
      "vaccinated": true,
      "dewormed": true,
      "sterilized": false,
      "healthStatus": "Excelente salud.",
      "adoptionStatus": "disponible",
      "shelterId": "s1",
      "shelterName": "Refugio San Francisco de Asís",
      "createdAt": "2026-07-01T10:00:00Z"
    }
  ],
  "detailError": null
}
```

#### Respuesta Exitosa de Creación (HTTP 201 CREATED):
```json
{
  "statusCode": 201,
  "status": "CREATED",
  "message": "Solicitud de adopción registrada con éxito",
  "data": {
    "id": "req_103",
    "petId": "1",
    "petName": "Toby",
    "status": "pendiente",
    "createdAt": "2026-07-28T15:00:00Z"
  },
  "detailError": null
}
```

#### Respuesta de Error por Recurso No Encontrado (HTTP 404 NOT_FOUND):
```json
{
  "statusCode": 404,
  "status": "NOT_FOUND",
  "message": "No se encontró la mascota con el ID especificado",
  "data": null,
  "detailError": "Pet with ID 9999 was not found in table 'pets'."
}
```

#### Respuesta de Error de Validación / Parámetros Incorrectos (HTTP 400 BAD_REQUEST):
```json
{
  "statusCode": 400,
  "status": "BAD_REQUEST",
  "message": "El campo 'userEmail' no cumple con un formato válido",
  "data": null,
  "detailError": "Validation failed: userEmail must be a valid email address"
}
```

---

## 2. Definición de Endpoints y Especificaciones REST

### 🐾 MASCOTAS (`/api/pets`)

#### 1. `GET /api/pets`
* **Descripción:** Obtiene el catálogo de mascotas disponibles con soporte para filtros opcionales por query params (`type`, `gender`, `size`, `ageCategory`, `adoptionStatus`, `shelterId`, `search`).
* **Query Params:** `?type=perro&size=mediano&shelterId=s1`
* **Respuesta Esperada:**
```json
{
  "statusCode": 200,
  "status": "OK",
  "message": "Catálogo de mascotas obtenido exitosamente",
  "data": [
    {
      "id": "1",
      "name": "Toby",
      "type": "perro",
      "breed": "Golden Retriever Mix",
      "age": "4 meses",
      "ageCategory": "cachorro",
      "gender": "macho",
      "size": "mediano",
      "personality": ["Juguetón", "Sociable"],
      "description": "Un cachorro sumamente alegre...",
      "story": "Toby fue encontrado junto a sus hermanitos...",
      "image": "https://...",
      "vaccinated": true,
      "dewormed": true,
      "sterilized": false,
      "healthStatus": "Excelente salud.",
      "adoptionStatus": "disponible",
      "shelterId": "s1",
      "shelterName": "Refugio San Francisco de Asís",
      "createdAt": "2026-07-01T10:00:00Z"
    }
  ],
  "detailError": null
}
```

#### 2. `GET /api/pets/:id`
* **Descripción:** Obtiene los detalles completos de una mascota específica.
* **Respuesta Esperada:**
```json
{
  "statusCode": 200,
  "status": "OK",
  "message": "Detalle de mascota obtenido exitosamente",
  "data": { "id": "1", "name": "Toby", "..." : "..." },
  "detailError": null
}
```

#### 3. `POST /api/pets`
* **Descripción:** Registra una nueva mascota en el sistema (panel de administración).
* **Body Request:**
```json
{
  "name": "Molly",
  "type": "perro",
  "breed": "Poodle Mix",
  "age": "2 años",
  "ageCategory": "joven",
  "gender": "hembra",
  "size": "pequeño",
  "personality": ["Cariñosa", "Tranquila"],
  "description": "Perrita dulce ideal para departamento.",
  "story": "Rescatada de la calle.",
  "image": "https://...",
  "vaccinated": true,
  "dewormed": true,
  "sterilized": true,
  "healthStatus": "Sana y llena de energía",
  "shelterId": "s1",
  "shelterName": "Refugio San Francisco de Asís"
}
```
* **Respuesta Esperada (HTTP 201):**
```json
{
  "statusCode": 201,
  "status": "CREATED",
  "message": "Mascota registrada exitosamente",
  "data": { "id": "generated-uuid-123", "name": "Molly", "adoptionStatus": "disponible" },
  "detailError": null
}
```

#### 4. `PUT /api/pets/:id`
* **Descripción:** Actualiza los datos de una mascota existente.
* **Respuesta Esperada:**
```json
{
  "statusCode": 200,
  "status": "OK",
  "message": "Ficha de la mascota actualizada exitosamente",
  "data": { "id": "1", "name": "Toby", "adoptionStatus": "en_proceso" },
  "detailError": null
}
```

#### 5. `DELETE /api/pets/:id`
* **Descripción:** Elimina la ficha de una mascota.
* **Respuesta Esperada:**
```json
{
  "statusCode": 200,
  "status": "OK",
  "message": "Mascota eliminada del sistema exitosamente",
  "data": { "id": "1", "deleted": true },
  "detailError": null
}
```

---

### 🏥 REFUGIOS (`/api/shelters`)

#### 1. `GET /api/shelters`
* **Descripción:** Obtiene la lista completa de refugios o santuarios asociados.
* **Respuesta Esperada:**
```json
{
  "statusCode": 200,
  "status": "OK",
  "message": "Refugios obtenidos exitosamente",
  "data": [
    {
      "id": "s1",
      "name": "Refugio San Francisco de Asís",
      "address": "Av. Las Palmas 450, Col. San Jerónimo",
      "city": "Ciudad de México",
      "phone": "+52 55 4123 9876",
      "email": "contacto@refugiosanfrancisco.org",
      "website": "https://refugiosanfrancisco.org",
      "capacity": 60,
      "currentPetCount": 28,
      "description": "Dedicados a la rehabilitación médica...",
      "image": "https://...",
      "verified": true,
      "createdAt": "2025-01-10T10:00:00Z"
    }
  ],
  "detailError": null
}
```

#### 2. `GET /api/shelters/:id`
* **Descripción:** Obtiene la ficha completa de un refugio por su ID.
* **Respuesta Esperada:**
```json
{
  "statusCode": 200,
  "status": "OK",
  "message": "Refugio encontrado exitosamente",
  "data": { "id": "s1", "name": "Refugio San Francisco de Asís" },
  "detailError": null
}
```

#### 3. `POST /api/shelters`
* **Descripción:** Registra un nuevo refugio en el sistema.
* **Respuesta Esperada (HTTP 201):**
```json
{
  "statusCode": 201,
  "status": "CREATED",
  "message": "Refugio registrado exitosamente",
  "data": { "id": "s4", "name": "Refugio Esperanza", "verified": true },
  "detailError": null
}
```

#### 4. `PUT /api/shelters/:id`
* **Descripción:** Actualiza los datos de un refugio.

#### 5. `DELETE /api/shelters/:id`
* **Descripción:** Elimina un refugio del sistema.

---

### 📋 SOLICITUDES DE ADOPCIÓN (`/api/adoption-requests`)

#### 1. `GET /api/adoption-requests`
* **Descripción:** Lista las solicitudes de adopción registradas (admite filtro por `shelterId` y `status`).
* **Respuesta Esperada:**
```json
{
  "statusCode": 200,
  "status": "OK",
  "message": "Solicitudes de adopción recuperadas exitosamente",
  "data": [
    {
      "id": "req_101",
      "petId": "1",
      "petName": "Toby",
      "petImage": "https://...",
      "shelterId": "s1",
      "userName": "María Fernández",
      "userEmail": "maria.f@gmail.com",
      "userPhone": "+52 55 1234 5678",
      "houseType": "casa",
      "hasOtherPets": true,
      "reason": "Buscamos un hermanito canino...",
      "status": "pendiente",
      "adminNotes": null,
      "createdAt": "2026-07-20T14:10:00Z"
    }
  ],
  "detailError": null
}
```

#### 2. `POST /api/adoption-requests`
* **Descripción:** Envía un formulario público de adopción para una mascota.
* **Body Request:**
```json
{
  "petId": "1",
  "petName": "Toby",
  "petImage": "https://...",
  "shelterId": "s1",
  "userName": "Carlos Ramírez",
  "userEmail": "carlos.ramirez@example.com",
  "userPhone": "+52 55 9988 7766",
  "houseType": "departamento",
  "hasOtherPets": false,
  "reason": "Quiero brindarle un hogar amoroso."
}
```
* **Respuesta Esperada (HTTP 201):**
```json
{
  "statusCode": 201,
  "status": "CREATED",
  "message": "Solicitud de adopción recibida. Nos pondremos en contacto pronto.",
  "data": { "id": "req_103", "status": "pendiente" },
  "detailError": null
}
```

#### 3. `PATCH /api/adoption-requests/:id/status`
* **Descripción:** Permite a un administrador aprobar o rechazar la solicitud de adopción e incluir observaciones.
* **Body Request:**
```json
{
  "status": "aprobado",
  "adminNotes": "Entrevista telefónica realizada. Cumple con todos los requisitos."
}
```
* **Respuesta Esperada:**
```json
{
  "statusCode": 200,
  "status": "OK",
  "message": "Estatus de la solicitud actualizado correctamente",
  "data": { "id": "req_101", "status": "aprobado", "adminNotes": "Entrevista..." },
  "detailError": null
}
```

---

### 📦 SOLICITUDES DE ENTREGA RESPONSABLE (`/api/surrender-requests`)

#### 1. `GET /api/surrender-requests`
* **Descripción:** Obtiene las solicitudes de personas que necesitan entregar una mascota a un refugio.
* **Respuesta Esperada:**
```json
{
  "statusCode": 200,
  "status": "OK",
  "message": "Solicitudes de entrega recuperadas con éxito",
  "data": [
    {
      "id": "surr_201",
      "petName": "Bruno",
      "petType": "perro",
      "petAge": "1 año",
      "shelterId": "s1",
      "shelterName": "Refugio San Francisco de Asís",
      "userName": "Rodrigo Mendoza",
      "userEmail": "rodrigo.mendoza@yahoo.com",
      "userPhone": "+52 55 8899 0011",
      "reason": "Cambio forzoso de residencia al extranjero...",
      "healthCondition": "Excelente salud, esterilizado y vacunado.",
      "status": "pendiente",
      "adminNotes": null,
      "createdAt": "2026-07-22T16:40:00Z"
    }
  ],
  "detailError": null
}
```

#### 2. `POST /api/surrender-requests`
* **Descripción:** Envía una solicitud pública de entrega de mascota a un refugio seleccionado.

#### 3. `PATCH /api/surrender-requests/:id/status`
* **Descripción:** Actualiza el estatus (`aprobado` | `rechazado`) con notas del administrador.

---

### ⭐ TESTIMONIOS (`/api/testimonials`)

#### 1. `GET /api/testimonials`
* **Descripción:** Obtiene las historias de éxito de mascotas adoptadas.
* **Respuesta Esperada:**
```json
{
  "statusCode": 200,
  "status": "OK",
  "message": "Testimonios obtenidos exitosamente",
  "data": [
    {
      "id": "t1",
      "petName": "Milo (antes Coco)",
      "petType": "perro",
      "ownerName": "Andrea & Carlos",
      "story": "Adoptar a Milo en Huellitas de Amor fue la mejor decisión...",
      "image": "https://...",
      "date": "2026-05-15"
    }
  ],
  "detailError": null
}
```

---

### 📊 MÉTRICAS DEL PANEL DE ADMINISTRACIÓN (`/api/admin/metrics`)

#### 1. `GET /api/admin/metrics`
* **Query Params Opcionales:** `?shelterId=s1` (si un manager solo tiene permiso sobre su propio refugio).
* **Respuesta Esperada:**
```json
{
  "statusCode": 200,
  "status": "OK",
  "message": "Métricas generales del sistema obtenidas exitosamente",
  "data": {
    "totalPets": 8,
    "availablePets": 8,
    "adoptedPets": 142,
    "pendingAdoptions": 1,
    "pendingSurrenders": 1,
    "activeShelters": 3
  },
  "detailError": null
}
```

---

## 3. Consideraciones Mapeo SQL <-> DTO (JSON)

Dado que la base de datos utiliza convención de columnas `snake_case` (ej. `age_category`, `adoption_status`, `shelter_id`), asegúrate de realizar la transformación a `camelCase` (`ageCategory`, `adoptionStatus`, `shelterId`) al construir los DTOs de respuesta JSON.

### Mapeo de Tipos de Datos
* `personality`: La columna `personality` en la base de datos se guarda como texto de un JSON Array (ej: `'["Juguetón", "Sociable"]'`). Debe deserializarse como un arreglo de strings `string[]` en el JSON devuelto.
* `vaccinated`, `dewormed`, `sterilized`, `verified`, `hasOtherPets`: Deben retornar siempre como valores booleanos nativos (`true`/`false`).

---

## 4. Requisitos de Seguridad y Manejo de Errores

1. **Captura Global de Excepciones:** Implementar un Middleware / Interceptor global de errores de modo que cualquier error no controlado (500) retorne siempre el formato `ResponsePayload`:
```json
{
  "statusCode": 500,
  "status": "INTERNAL_SERVER_ERROR",
  "message": "Ha ocurrido un error inesperado en el servidor",
  "data": null,
  "detailError": "Database connection timeout at line 42..."
}
```

2. **CORS:** Configurar encabezados CORS para permitir peticiones desde el dominio del cliente web.
3. **Validación de Entradas:** Validar que los campos requeridos en los endpoints `POST` y `PUT` contengan información válida antes de procesar la consulta en la base de datos.
