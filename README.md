# 🐾 Paws Adoption Platform Backend

Backend de la plataforma **Huellitas de Amor**, una aplicación web que conecta refugios de animales con personas interesadas en adoptar o entregar mascotas en adopción.

Expone una API REST para gestionar mascotas, refugios, solicitudes de adopción, solicitudes de entrega responsable, testimonios y métricas del panel de administración. El contrato completo está en [docs/prompt-backend.md](docs/prompt-backend.md).

## Contenido

1. [Tecnologías](#-tecnologías)
2. [Requisitos previos](#-requisitos-previos)
3. [Instalación paso a paso](#-instalación-paso-a-paso)
4. [Ejecutar el proyecto](#️-ejecutar-el-proyecto)
5. [Migraciones (Alembic)](#️-migraciones-alembic)
5. [Variables de entorno](#-variables-de-entorno)
6. [Endpoints](#-endpoints)
7. [Pruebas y calidad de código](#-pruebas-y-calidad-de-código)
8. [Estructura del proyecto](#-estructura-del-proyecto)
9. [Cómo agregar un módulo nuevo](#-cómo-agregar-un-módulo-nuevo)
10. [Flujo de trabajo con Git](#-flujo-de-trabajo-con-git)
11. [Comandos de referencia](#-comandos-de-referencia)

---

## 📋 Tecnologías

| Tecnología | Versión | Uso |
| --- | --- | --- |
| Python | 3.13.2 | Lenguaje |
| FastAPI | 0.116.1 | Framework web |
| Uvicorn | 0.35.0 | Servidor ASGI |
| SQLAlchemy (async) | 2.0.43 | ORM |
| AsyncPG | 0.30.0 | Driver de PostgreSQL |
| Pydantic / Pydantic Settings | 2.11.7 / 2.10.1 | Validación y configuración |
| Alembic | 1.16.4 | Migraciones versionadas del esquema |
| PyJWT + Passlib/Bcrypt | 2.10.1 / 1.7.4 | Sesiones y contraseñas de administradores |
| Supabase (PostgreSQL + Storage) | — | Base de datos y fotografías de mascotas |
| uv | — | Gestión de Python, entorno virtual y dependencias |
| Pytest + pytest-cov | — | Pruebas y cobertura |
| Ruff | — | Linter y formateador |

---

## ✅ Requisitos previos

Instala estas tres herramientas antes de comenzar:

| Herramienta | Para qué | Verificar instalación |
| --- | --- | --- |
| [Git](https://git-scm.com/) | Clonar el repositorio | `git --version` |
| [uv](https://docs.astral.sh/uv/getting-started/installation/) | Instalar Python y las dependencias | `uv --version` |
| Proyecto en [Supabase](https://supabase.com/) | Base de datos PostgreSQL y Storage | — |

> No necesitas instalar Python manualmente: `uv` descarga la versión exacta que usa el proyecto.

---

## 🚀 Instalación paso a paso

Ejecuta los pasos en orden. Solo se hacen una vez por máquina.

### Paso 1 · Clonar el repositorio

```bash
git clone <URL_DEL_REPOSITORIO>
cd paws-adoption-platform-backend
```

### Paso 2 · Instalar Python 3.13.2

```bash
uv python install 3.13.2
```

La versión queda fijada por el archivo `.python-version`, no hay que configurarla.

### Paso 3 · Instalar las dependencias

```bash
uv sync
```

Este comando crea el entorno virtual `.venv` e instala las dependencias del proyecto y las de desarrollo, con las versiones exactas de `uv.lock`.

### Paso 4 · Crear el archivo `.env`

Copia la plantilla:

```powershell
# PowerShell
Copy-Item .env.example .env
```

```bash
# Git Bash / Linux / macOS
cp .env.example .env
```

Completa en `.env` estos valores (el resto funciona tal cual en local):

| Variable | De dónde sale |
| --- | --- |
| `DATABASE_URL` | Supabase → **Connect** → *Session pooler*. Cambia el prefijo a `postgresql+asyncpg://`, pon tu contraseña y agrega `?ssl=require` al final |
| `SUPABASE_URL` y `SUPABASE_SERVICE_ROLE_KEY` | Supabase → **Project Settings → API** (llave `service_role`) |
| `JWT_SECRET_KEY` | Genérala: `python -c "import secrets; print(secrets.token_urlsafe(48))"` |
| `ADMIN_REGISTRATION_KEY` | Cualquier valor secreto; sirve para registrar al primer administrador |

> ⚠️ Nunca subas `.env` a Git: contiene credenciales. La `service_role` da acceso total al proyecto de Supabase y solo debe vivir en el backend.

### Paso 5 · Crear el esquema con las migraciones

```bash
uv run alembic upgrade head
```

Crea todas las tablas y el bucket público `pet-photos` en Supabase Storage. No inserta datos: la base arranca vacía y todo se carga desde la aplicación.

> Si la base **ya tiene** las tablas originales (creadas con `schema.sql`), márcalas primero como aplicadas y luego migra: `uv run alembic stamp 0001` y después `uv run alembic upgrade head`.

### Paso 6 · Registrar el primer administrador

Con el servidor levantado (siguiente sección), abre el frontend → **Panel Admin** → *Tengo una llave de acceso: registrarme* y escribe la llave de `ADMIN_REGISTRATION_KEY`: la primera cuenta se crea como **Super Administrador** y esa llave deja de servir.

Para sumar a más personas, el super administrador genera en **Configuración** una llave de acceso de un solo uso para el correo de esa persona (vence a las 72 horas) y se la entrega; cada persona crea su propia cuenta con ella, usando ese mismo correo, desde la misma pantalla de registro.

---

## ▶️ Ejecutar el proyecto

### Levantar el servidor

```bash
uv run uvicorn src.main:app --reload
```

`--reload` reinicia el servidor al guardar cambios; úsalo solo en desarrollo.

### Comprobar que funciona

| Qué | URL |
| --- | --- |
| Estado del servicio y de la base de datos | http://127.0.0.1:8000/api/v1/health |
| Documentación interactiva (Swagger UI) | http://127.0.0.1:8000/docs |
| Documentación ReDoc | http://127.0.0.1:8000/redoc |

Si `/api/v1/health` responde `"status": "OK"`, la API y la conexión a la base de datos están listas.

### Conectar el frontend

El frontend (`paws-adoption-platform-frontend`) corre en `http://localhost:3000` y lee la URL de la API de su variable `VITE_API_URL` (`http://localhost:8000/api/v1`). Si lo sirves desde otro origen, agrégalo a `CORS_ORIGINS` en el `.env` del backend.

### Problemas frecuentes

| Síntoma | Causa y solución |
| --- | --- |
| `Field required` para `DATABASE_URL` o `JWT_SECRET_KEY` al arrancar | Falta el archivo `.env` o la variable. Repite el paso 4. |
| `password authentication failed` | La contraseña de `DATABASE_URL` no es la de la base de datos de Supabase. |
| `no tenant identifier provided` | El usuario de `DATABASE_URL` debe ser `postgres.<ref-del-proyecto>` y el prefijo no debe estar duplicado. |
| `relation "admins" does not exist` | Faltan migraciones por aplicar: `uv run alembic upgrade head`. |
| 503 "El almacenamiento de fotografías no está configurado" | Faltan `SUPABASE_URL` o `SUPABASE_SERVICE_ROLE_KEY`. |
| El frontend recibe 404 en todo | El frontend apunta a otro prefijo, o el backend no se reinició tras cambiar `.env`. |
| El navegador bloquea las peticiones por CORS | El origen del frontend no está en `CORS_ORIGINS`. |

---

## 🗃️ Migraciones (Alembic)

El esquema de la base de datos se versiona en `migrations/versions/`. Cada cambio en un `model.py` va acompañado de una migración.

| Comando | Función |
| --- | --- |
| `uv run alembic upgrade head` | Aplica las migraciones pendientes |
| `uv run alembic revision --autogenerate -m "descripcion"` | Genera una migración comparando los modelos con la base |
| `uv run alembic check` | Indica si hay cambios en los modelos sin migración |
| `uv run alembic current` / `uv run alembic history` | Versión aplicada / historial |
| `uv run alembic downgrade -1` | Revierte la última migración |

Flujo para cambiar el esquema: edita el `model.py`, genera la migración con `--autogenerate`, **revisa el archivo generado** y aplícalo con `upgrade head`. La autogeneración ignora las tablas que no pertenecen a los modelos (por ejemplo las internas de Supabase), así que nunca propone borrarlas.

### Supabase local con Docker (opcional)

Supabase tiene soporte oficial para contenedores a través de su CLI. Con Docker Desktop y la [Supabase CLI](https://supabase.com/docs/guides/cli) instalados:

```bash
supabase start      # PostgreSQL, Auth, PostgREST, Storage y Studio en contenedores
supabase status     # URLs y llaves locales
```

La configuración está en [supabase/config.toml](supabase/config.toml) (incluye el bucket `pet-photos`). Para usarlo, cambia en `.env` `DATABASE_URL` y `SUPABASE_URL` por los valores locales comentados en `.env.example`, pon la `service_role key` que imprime `supabase status` y ejecuta `uv run alembic upgrade head`.

---

## 🔐 Variables de entorno

Se definen en `.env` y se cargan en [src/core/config.py](src/core/config.py).

| Variable | Obligatoria | Valor por defecto | Descripción |
| --- | --- | --- | --- |
| `DATABASE_URL` | Sí | — | Conexión a PostgreSQL: `postgresql+asyncpg://USUARIO:PASSWORD@HOST:PUERTO/BASE` |
| `JWT_SECRET_KEY` | Sí | — | Secreto con el que se firman los tokens de sesión |
| `SUPABASE_URL` | Para subir fotos | — | URL del proyecto de Supabase |
| `SUPABASE_SERVICE_ROLE_KEY` | Para subir fotos | — | Llave secreta `service_role` |
| `SUPABASE_STORAGE_BUCKET` | No | `pet-photos` | Bucket público de fotografías |
| `MAX_PHOTO_SIZE_MB` | No | `5` | Tamaño máximo por fotografía |
| `ADMIN_REGISTRATION_KEY` | No | — | Llave para el alta inicial: registra al primer super administrador y deja de funcionar en cuanto existe uno |
| `ADMIN_INVITATION_EXPIRE_HOURS` | No | `72` | Vigencia de las llaves de acceso de un solo uso |
| `SMTP_USERNAME` | Para enviar correos | — | Cuenta de Gmail que envía los códigos de seguimiento |
| `SMTP_PASSWORD` | Para enviar correos | — | Contraseña de aplicación de esa cuenta (no la contraseña normal) |
| `SMTP_HOST`, `SMTP_PORT` | No | `smtp.gmail.com`, `587` | Servidor SMTP |
| `EMAIL_FROM_NAME` | No | `Huellitas de Amor` | Nombre visible del remitente |
| `FRONTEND_URL` | No | `http://localhost:3000` | URL del frontend para el enlace de seguimiento del correo |
| `JWT_ALGORITHM` | No | `HS256` | Algoritmo de firma |
| `JWT_ACCESS_TOKEN_EXPIRE_MINUTES` | No | `60` | Duración de la sesión |
| `API_PREFIX` | No | `/api/v1` | Prefijo de todos los endpoints |
| `CORS_ORIGINS` | No | `http://localhost:3000,http://127.0.0.1:3000` | Orígenes del frontend permitidos, separados por coma |
| `APP_NAME`, `APP_ENV` | No | `Huellitas de Amor`, `development` | Nombre y entorno |
| `DEBUG` | No | `false` | Con `true`, los errores 500 incluyen el detalle técnico en `detailError`. Usar `false` en producción |

---

## 🌐 Endpoints

Todos cuelgan del prefijo `/api/v1` y responden con el mismo formato (`ResponsePayload`):

```json
{
  "statusCode": 200,
  "status": "OK",
  "message": "Catálogo de mascotas obtenido exitosamente",
  "data": [],
  "detailError": null
}
```

En los errores (`400`, `401`, `403`, `404`, `409`, `500`, `503`) `data` es `null` y `detailError` trae el detalle técnico.

**Acceso:** 🌐 público · 🔒 administrador autenticado (`Authorization: Bearer <token>`) · 👑 solo `super_admin`.

| Recurso | Método y ruta | Acceso | Descripción |
| --- | --- | --- | --- |
| Autenticación | `POST /auth/register-admin` | 👑 o llave | Registra un administrador. Requiere sesión de `super_admin` o la cabecera `X-Admin-Registration-Key` con una llave de acceso de un solo uso (o la llave inicial, para el primer super administrador) |
| | `POST /auth/invitations` | 👑 | Genera una llave de un solo uso atada al `email` del invitado (rol `adoption_admin` por defecto) y se la envía por correo con la plantilla [admin_invitation.html](src/notifications/templates/admin_invitation.html). `emailSent` indica si el correo salió |
| | `POST /auth/login` | 🌐 | Devuelve el token JWT y los datos del administrador |
| | `GET /auth/me` | 🔒 | Administrador de la sesión actual |
| Mascotas | `GET /pets` | 🌐 | Solo las publicadas. Filtros: `type`, `gender`, `size`, `ageCategory`, `adoptionStatus`, `shelterId`, `search`, `vaccinated`, `dewormed`, `sterilized`. Con `includeHidden=true` (🔒) incluye las ocultas |
| | `GET /pets/{id}` | 🌐 | Detalle de una mascota; una oculta responde 404 salvo para administradores |
| | `POST /pets` | 🔒 | Registrar mascota. `multipart/form-data` con los campos y de 1 a 4 archivos `photos` (se convierten a WebP). `isVisible` decide si se publica; `surrenderRequestId` la enlaza a una entrega aprobada |
| | `PATCH /pets/{id}` | 🔒 | Actualización parcial: solo los campos enviados. `photos` agrega fotos y `removePhotos` quita URLs actuales; el total debe quedar entre 1 y 4 |
| | `DELETE /pets/{id}` | 🔒 | Eliminar la mascota y todas sus fotografías |
| Personalidades | `GET /personalities` | 🌐 | Catálogo de rasgos |
| | `POST /personalities` | 🔒 | Agregar un rasgo (solo letras y espacios, 3 a 40 caracteres) |
| | `DELETE /personalities/{id}` | 🔒 | Eliminar un rasgo; 409 si alguna mascota lo tiene asignado |
| Refugios | `GET /shelters`, `GET /shelters/{id}` | 🌐 | Lista y detalle |
| | `POST /shelters`, `PUT /shelters/{id}` | 🔒 | Registrar y actualizar |
| | `DELETE /shelters/{id}` | 👑 | Eliminar |
| Adopciones | `POST /adoptions` | 🌐 | Enviar solicitud de adopción. Devuelve el `trackingCode` y lo envía por correo |
| | `POST /adoptions/track` | 🌐 | Seguimiento: estado y última nota del refugio. Exige `trackingCode` y el `email` de la solicitud |
| | `GET /adoptions` | 🔒 | Lista con filtros `shelterId` y `status` |
| | `PATCH /adoptions/{id}/status` | 🔒 | Pasar a `en_entrevista`, `aprobado` o `rechazado`. `adminNotes` es obligatorio (5 a 1000 caracteres) y se envía por correo al solicitante |
| Entregas | `POST /surrender-requests` | 🌐 | Enviar solicitud de entrega. Devuelve el `trackingCode` y lo envía por correo |
| | `POST /surrender-requests/track` | 🌐 | Seguimiento: estado y última nota del refugio. Exige `trackingCode` y el `email` de la solicitud |
| | `GET /surrender-requests` | 🔒 | Lista con filtros `shelterId` y `status` |
| | `PATCH /surrender-requests/{id}/status` | 🔒 | Pasar a `en_entrevista` (cita de evaluación), `aprobado` o `rechazado`. `adminNotes` es obligatorio y se envía por correo |
| Testimonios | `GET /testimonials` | 🌐 | Historias de éxito |
| Métricas | `GET /admin/metrics` | 🔒 | KPIs del panel; `shelterId` opcional |
| Contacto | `POST /contact` | 🌐 | Recibe el formulario de "Contáctanos" (`name`, `email`, `subject`, `message`) |
| | `GET /admin/messages` | 🔒 | Bandeja de entrada paginada (`page`, `pageSize`) con filtro `isRead`; incluye el total de no leídos |
| | `GET /admin/messages/{id}` | 🔒 | Detalle del mensaje con sus respuestas; lo marca como leído |
| | `POST /admin/messages/{id}/reply` | 🔒 | Envía la respuesta por correo al remitente y la guarda en el hilo. Si el correo no sale responde 503 y no guarda nada |
| Salud | `GET /health` | 🌐 | Estado del servicio |

### Reglas de negocio

- **Visibilidad:** `pets.is_visible` controla si la ficha aparece en el catálogo público; es independiente del estado de adopción.
- **Entregas:** aprobar una entrega no publica nada. Desde una entrega aprobada el administrador registra a la mascota recibida (`POST /pets` con `surrenderRequestId`); la ficha y su enlace con la entrega se guardan en una sola transacción y nace oculta hasta que se publique.
- **Adopciones:** `pendiente → en_entrevista → aprobado | rechazado` (los dos últimos son finales). En la misma transacción la mascota pasa a `en_proceso` al entrar a entrevista y a `adoptado` al aprobar; si se rechaza y no hay otra entrevista en curso vuelve a `disponible`. Una mascota adoptada no admite más solicitudes ni aprobaciones.
- **Notas obligatorias y avisos:** todo cambio de estado de una solicitud (adopción o entrega) exige una nota del administrador; sin ella la API responde 400. Tras guardar el cambio se envía al solicitante un correo con el nuevo estado, la nota y los siguientes pasos, usando la plantilla [status_update.html](src/notifications/templates/status_update.html); los textos de cada estado están en [status.py](src/notifications/status.py).
- **Código de seguimiento:** se genera al recibir la solicitud y se envía por correo con la plantilla [tracking_code.html](src/notifications/templates/tracking_code.html). El envío ocurre después de responder: si el correo falla, la solicitud queda registrada igual.

### Correo con Gmail

1. Activa la verificación en dos pasos en la cuenta de Gmail que enviará los correos.
2. Crea una contraseña de aplicación en https://myaccount.google.com/apppasswords.
3. Pon la cuenta en `SMTP_USERNAME` y la contraseña de 16 caracteres en `SMTP_PASSWORD`, y reinicia el backend.

Sin esas dos variables no se envían correos; el código se sigue mostrando en pantalla.

Las fotografías (hasta 4 por mascota) se validan con Pillow, se corrigen de orientación, se reducen a un máximo de 1600 px, pierden sus metadatos EXIF y se convierten a WebP antes de subirse a Supabase Storage desde el backend (JPG, PNG o WEBP); la base de datos solo guarda la URL pública en `pets.image`.

> Este README describe la API vigente. [docs/prompt-backend.md](docs/prompt-backend.md) es el contrato original y difiere en el prefijo (`/api`), la autenticación, la subida de fotos y la ruta `/adoption-requests`.

---

## 🧪 Pruebas y calidad de código

### Pruebas

Las pruebas no necesitan PostgreSQL ni Supabase: usan una base SQLite en memoria vacía y un almacenamiento simulado.

```bash
uv run pytest
```

Con reporte de cobertura (genera `coverage.xml`, que consume SonarQube):

```bash
uv run pytest --cov --cov-report=term-missing --cov-report=xml
```

### Linter y formato

```bash
uv run ruff check .          # revisar
uv run ruff check . --fix    # corregir lo que se pueda automáticamente
uv run ruff format .         # formatear
```

### SonarQube

El análisis se configura en [sonar-project.properties](sonar-project.properties) (`src` como código fuente, `test` como pruebas). Para ejecutarlo:

```bash
uv run pytest --cov --cov-report=xml
sonar-scanner -Dsonar.host.url=<URL_DE_SONARQUBE> -Dsonar.token=<TOKEN>
```

Ajusta `sonar.projectKey` al identificador del proyecto en tu servidor.

Convenciones que el código sigue para mantener limpio el análisis:

- **Sin credenciales en el código:** `DATABASE_URL` no tiene valor por defecto; todo secreto vive en `.env`.
- **Sin literales duplicados:** estados, rutas y mensajes repetidos se definen una vez (`RequestStatus`, `AdoptionStatus`, constantes de módulo).
- **Sin lógica duplicada:** las operaciones comunes de persistencia están en [src/database/repository.py](src/database/repository.py) y los DTO base en [src/core/schemas.py](src/core/schemas.py).
- **Funciones pequeñas:** complejidad ciclomática máxima de 10 (regla `C90` de Ruff) y pocos parámetros; los filtros de consulta viajan en un único objeto.
- **Tipos consistentes:** ninguna variable recibe un valor que contradiga su anotación.
- **Errores 500 sin fuga de información:** el detalle técnico solo se expone con `DEBUG=true`.
- **CORS restringido:** solo los orígenes, métodos y cabeceras declarados.

---

## 📁 Estructura del proyecto

El código se organiza **por módulo de dominio: una carpeta por cada tabla** de la base de datos. Cada carpeta contiene todo lo necesario para esa tabla.

```text
paws-adoption-platform-backend/
├── alembic.ini                    # Configuración de Alembic
├── migrations/
│   ├── env.py                     # Conecta Alembic con DATABASE_URL y los modelos
│   └── versions/                  # Una migración por cambio de esquema
├── supabase/
│   └── config.toml                # Supabase local en Docker (CLI)
├── docs/
│   └── prompt-backend.md          # Contrato original de la API
├── src/
│   ├── main.py                    # Crea la app: CORS, manejo de errores y rutas
│   ├── api/
│   │   ├── router.py              # Registra los routers de todos los módulos
│   │   ├── deps.py                # Dependencia de sesión de base de datos
│   │   └── health.py              # GET /health
│   ├── core/                      # Piezas transversales, sin lógica de negocio
│   │   ├── config.py              # Variables de entorno
│   │   ├── exceptions.py          # Errores de negocio y manejadores globales
│   │   ├── responses.py           # Formato ResponsePayload
│   │   ├── schemas.py             # DTO base (camelCase), tipos y enums compartidos
│   │   ├── security.py            # Hash de contraseñas (bcrypt) y tokens JWT
│   │   └── ids.py                 # Generación de identificadores
│   ├── database/
│   │   ├── connection.py          # Motor, sesiones y Base declarativa
│   │   ├── repository.py          # Repositorio base con operaciones comunes
│   │   ├── types.py               # Tipos de columna propios (lista JSON)
│   │   └── init_db.py             # Registro de modelos (lo usan Alembic y las pruebas)
│   ├── notifications/             # Correo saliente
│   │   ├── interfaces.py          # Contrato EmailSender
│   │   ├── gmail.py               # Implementación SMTP para Gmail
│   │   ├── tracking.py            # Correo con el código de seguimiento al recibir una solicitud
│   │   ├── status.py              # Correo de cada cambio de estado (entrevista, aprobada, rechazada)
│   │   ├── contact.py             # Correo con la respuesta a un mensaje de contacto
│   │   ├── rendering.py           # Carga de plantillas y envío tolerante a fallos
│   │   └── templates/             # Plantillas HTML de los correos
│   ├── storage/                   # Almacenamiento de archivos y optimización de imágenes (images.py)
│   │   ├── interfaces.py          # Contrato FileStorage
│   │   ├── supabase.py            # Implementación sobre Supabase Storage
│   │   └── dependencies.py        # Elige la implementación según la configuración
│   └── modules/                   # Un paquete por tabla / dominio
│       ├── auth/                  # Tablas admins y admin_invitations: registro, login y permisos
│       ├── pets/                  # Tabla pets (incluye la subida de fotos)
│       ├── shelters/              # Tabla shelters
│       ├── adoption_requests/     # Tabla adoption_requests
│       ├── surrender_requests/    # Tabla surrender_requests
│       ├── testimonials/          # Tabla testimonials
│       ├── contact_messages/      # Tablas contact_messages y contact_message_replies: bandeja y respuestas
│       ├── personalities/         # Tabla personalities: catálogo de rasgos de las mascotas
│       └── metrics/               # KPIs calculados (no tiene tabla propia)
├── test/
│   ├── conftest.py                # Cliente HTTP con base SQLite en memoria
│   ├── unit/                      # Servicios con repositorios en memoria
│   └── integration/               # Endpoints completos
├── .env.example
├── pyproject.toml                 # Dependencias y configuración de Ruff, Pytest y cobertura
├── sonar-project.properties
└── uv.lock
```

### Archivos de cada módulo

| Archivo | Responsabilidad |
| --- | --- |
| `model.py` | Tabla (modelo SQLAlchemy) |
| `schemas.py` | DTO de entrada y salida, validación (Pydantic) |
| `interfaces.py` | Contratos (`Protocol`) que el servicio necesita de la persistencia y de otros dominios |
| `repository.py` | Consultas a la base de datos; implementa el contrato |
| `service.py` | Reglas de negocio; recibe sus dependencias por constructor |
| `dependencies.py` | Cableado con `Depends`: sesión → repositorios → servicio |
| `router.py` | Endpoints HTTP: recibe, delega al servicio y responde |

### Flujo de una petición

```text
Cliente → router.py → service.py → interfaces.py ← repository.py → PostgreSQL
```

El router no contiene lógica de negocio y el servicio no escribe consultas SQL: depende de contratos, por lo que la base de datos y el Storage se pueden sustituir por implementaciones en memoria.

---

## 🧩 Cómo agregar un módulo nuevo

Para exponer el CRUD de una tabla nueva (por ejemplo `donations`):

1. Crea la carpeta `src/modules/donations/` con un `__init__.py` vacío.
2. Agrega `model.py`, `schemas.py`, `interfaces.py`, `repository.py`, `service.py`, `dependencies.py` y `router.py` tomando como referencia `src/modules/shelters/`.
3. Registra el router en [src/api/router.py](src/api/router.py) y el modelo en `MODELS` de [src/database/init_db.py](src/database/init_db.py).
4. Genera y aplica la migración: `uv run alembic revision --autogenerate -m "tabla donations"` y `uv run alembic upgrade head`.
5. En esa misma migración, cierra la tabla a la API de datos de Supabase igual que en [0005_rls_and_created_at_indexes.py](migrations/versions/0005_rls_and_created_at_indexes.py): `ENABLE ROW LEVEL SECURITY`, `REVOKE ALL ... FROM anon, authenticated` y la política `deny_client_access`. Si no, Supabase reportará "RLS Disabled in Public".
6. Protege los endpoints de administración con `dependencies=[require_admin]` y ejecuta `uv run ruff check .`.

---

## 🌿 Flujo de trabajo con Git

```bash
git pull origin develop                         # 1. Actualizar
git checkout -b feature/nombre-funcionalidad    # 2. Crear rama
uv run ruff check . && uv run pytest            # 3. Validar antes de subir
git add <archivos>
git commit -m "feat: descripción del cambio"    # 4. Commit
git push origin feature/nombre-funcionalidad    # 5. Subir y abrir un Pull Request
```

**Se versionan:** `src/`, `test/`, `docs/`, `migrations/`, `alembic.ini`, `supabase/config.toml`, `pyproject.toml`, `uv.lock`, `.python-version`, `.env.example`, `sonar-project.properties`, `.gitignore`, `README.md`.

**No se versionan** (ya están en `.gitignore`): `.env`, `.venv/`, `__pycache__/`, `.pytest_cache/`, `.ruff_cache/`, `.coverage`, `coverage.xml`.

---

## 📌 Comandos de referencia

| Comando | Función |
| --- | --- |
| `uv sync` | Instalar dependencias |
| `uv run alembic upgrade head` | Aplicar las migraciones pendientes |
| `uv run alembic revision --autogenerate -m "..."` | Generar una migración desde los modelos |
| `uv run uvicorn src.main:app --reload` | Levantar el servidor en desarrollo |
| `uv run pytest` | Ejecutar las pruebas |
| `uv run pytest --cov --cov-report=xml` | Pruebas con cobertura para SonarQube |
| `uv run ruff check .` | Revisar el código |
| `uv run ruff format .` | Formatear el código |
| `uv add <paquete>` | Agregar una dependencia |
| `uv add --dev <paquete>` | Agregar una dependencia de desarrollo |
