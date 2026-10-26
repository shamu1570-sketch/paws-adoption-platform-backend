import re
from enum import StrEnum
from typing import Annotated, ClassVar, Literal

from pydantic import (
    AfterValidator,
    BaseModel,
    BeforeValidator,
    ConfigDict,
    EmailStr,
    StringConstraints,
    ValidationInfo,
    field_validator,
)
from pydantic.alias_generators import to_camel
from pydantic_core import PydanticCustomError

# Tipo de error de validación cuyo texto ya está redactado para mostrarse al usuario.
USER_MESSAGE_ERROR = "user_message"


class CamelModel(BaseModel):
    """Base de los DTOs: columnas snake_case <-> JSON camelCase."""

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        from_attributes=True,
        use_enum_values=True,
    )


class PartialUpdateModel(CamelModel):
    """Base de los DTOs de actualización parcial: solo se modifican los campos enviados.

    Los campos se declaran opcionales para poder omitirlos, pero enviar `null`
    explícitamente solo es válido en los listados en `nullable_fields`.
    """

    nullable_fields: ClassVar[frozenset[str]] = frozenset()

    @field_validator("*", mode="before")
    @classmethod
    def reject_explicit_null(cls, value: object, info: ValidationInfo) -> object:
        if value is None and info.field_name not in cls.nullable_fields:
            raise PydanticCustomError(
                USER_MESSAGE_ERROR, f"El campo '{info.field_name}' no puede quedar vacío"
            )
        return value


def _blank_to_none(value: object) -> object:
    if isinstance(value, str) and not value.strip():
        return None
    return value


def _normalize_phone(value: object) -> object:
    """Quita los separadores habituales (espacios, guiones, paréntesis, puntos)."""
    if isinstance(value, str):
        return re.sub(r"[\s().-]", "", value)
    return value


def bounded_text(max_length: int, min_length: int = 1) -> type[str]:
    """Texto obligatorio, sin espacios sobrantes y con longitud acotada."""
    return Annotated[
        str,
        StringConstraints(strip_whitespace=True, min_length=min_length, max_length=max_length),
    ]


def optional_text(max_length: int) -> type[str | None]:
    """Texto opcional acotado; una cadena vacía se interpreta como ausencia de valor."""
    return Annotated[
        Annotated[str, StringConstraints(max_length=max_length)] | None,
        BeforeValidator(_blank_to_none),
    ]


RequiredStr = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]
OptionalStr = Annotated[str | None, BeforeValidator(_blank_to_none)]

# Longitudes máximas alineadas con las columnas de la base de datos.
IdStr = bounded_text(36)
Text50 = bounded_text(50)
Text100 = bounded_text(100)
Text150 = bounded_text(150)
Text300 = bounded_text(300)
UrlStr = bounded_text(1000)
LongText = bounded_text(2000)
# Motivos y observaciones que se muestran completos en la interfaz.
MessageText = bounded_text(1000)
OptionalMessage = optional_text(1000)
# Nota que el administrador debe escribir al cambiar el estado de una solicitud.
AdminNote = bounded_text(1000, min_length=5)
Website = optional_text(255)
Email = Annotated[EmailStr, StringConstraints(max_length=150)]

# Nombres (personas y mascotas): solo letras, con acentos y ñ, separadas por un único espacio.
PLAIN_NAME_PATTERN = r"^[^\W\d_]+(?: [^\W\d_]+)*$"
NAME_MAX_LENGTH = 50
PersonName = Annotated[
    str,
    StringConstraints(
        strip_whitespace=True,
        min_length=2,
        max_length=NAME_MAX_LENGTH,
        pattern=PLAIN_NAME_PATTERN,
    ),
]


def _letters_and_spaces(message: str):
    """Validador con mensaje propio: solo letras (con acentos y ñ) y espacios sencillos."""

    def check(value: str) -> str:
        if not re.fullmatch(r"[^\W\d_]+(?: [^\W\d_]+)*", value):
            raise PydanticCustomError(USER_MESSAGE_ERROR, message)
        return value

    return check


# Nombre de un refugio u organización: misma regla que los nombres, con un mensaje propio.
ShelterName = Annotated[
    str,
    StringConstraints(strip_whitespace=True, min_length=3, max_length=150),
    AfterValidator(
        _letters_and_spaces("El nombre del refugio solo puede contener letras y espacios")
    ),
]
# Teléfono: solo dígitos, con "+" opcional al inicio para el indicativo del país.
Phone = Annotated[
    str,
    BeforeValidator(_normalize_phone),
    StringConstraints(pattern=r"^\+?[0-9]{7,15}$"),
]
# Código público de seguimiento, ej: ADOP-2026-K7M2QX9D (no distingue mayúsculas).
TRACKING_CODE_PATTERN = r"(?i)^(ADOP|ENTR)-[0-9]{4}-[A-Z2-9]{8}$"

PetType = Literal["perro", "gato"]


class RequestStatus(StrEnum):
    PENDING = "pendiente"
    IN_INTERVIEW = "en_entrevista"
    APPROVED = "aprobado"
    REJECTED = "rechazado"


class RequestFilters(CamelModel):
    """Filtros por query string comunes a las solicitudes de adopción y de entrega."""

    shelter_id: str | None = None
    status: RequestStatus | None = None


TrackingCode = Annotated[
    str, StringConstraints(strip_whitespace=True, to_upper=True, pattern=TRACKING_CODE_PATTERN)
]


class TrackingLookup(CamelModel):
    """Consulta pública del estado de una solicitud.

    Exige el código y el correo con que se registró: el código solo no basta, así nadie
    que lo vea por encima del hombro o en un dispositivo compartido puede consultarla.
    """

    tracking_code: TrackingCode
    email: Email


class StatusUpdate(CamelModel):
    """Cambio de estado de una solicitud de adopción o de entrega.

    La nota es obligatoria: explica la decisión y se envía por correo al solicitante.
    """

    status: Literal[RequestStatus.IN_INTERVIEW, RequestStatus.APPROVED, RequestStatus.REJECTED]
    admin_notes: AdminNote


# Mensajes de respuesta al cambiar el estado de una solicitud, según saliera o no el correo.
STATUS_NOTIFIED = "Estatus actualizado. Se notificó al solicitante por correo."
STATUS_NOT_NOTIFIED = (
    "Estatus actualizado, pero no fue posible enviar el correo al solicitante. "
    "Contáctalo por teléfono."
)


class DeletedOut(CamelModel):
    id: str
    deleted: bool
