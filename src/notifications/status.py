from dataclasses import dataclass
from enum import StrEnum
from html import escape

from src.core.schemas import RequestStatus
from src.notifications.interfaces import EmailSender
from src.notifications.rendering import (
    Details,
    build_tracking_url,
    deliver,
    load_template,
    render_detail_lines,
    render_detail_rows,
)

_TEMPLATE = load_template("status_update.html")

_STEP_ITEM = '                  <li style="margin:0 0 6px;">{step}</li>\n'


class RequestKind(StrEnum):
    ADOPTION = "adoption"
    SURRENDER = "surrender"


@dataclass(frozen=True)
class StatusContent:
    """Textos y color de la plantilla para un estado concreto."""

    subject: str
    badge: str
    accent: str
    headline: str
    intro: str
    note_title: str
    next_steps: tuple[str, ...]


_GREEN = "#059669"
_INDIGO = "#4F46E5"
_SLATE = "#475569"

_CONTENT: dict[tuple[str, str], StatusContent] = {
    (RequestKind.ADOPTION, RequestStatus.APPROVED): StatusContent(
        subject="¡Tu solicitud de adopción fue aprobada!",
        badge="Solicitud aprobada",
        accent=_GREEN,
        headline="¡Felicidades! Tu solicitud fue aprobada",
        intro="nos alegra contarte que el refugio aprobó tu solicitud de adopción.",
        note_title="Mensaje del refugio",
        next_steps=(
            "El refugio te contactará para acordar la fecha de entrega de tu nueva mascota.",
            "Ten a la mano tu documento de identidad y un comprobante de domicilio.",
            "Prepara en casa un espacio seguro, agua, alimento y su cama.",
        ),
    ),
    (RequestKind.ADOPTION, RequestStatus.IN_INTERVIEW): StatusContent(
        subject="Tu solicitud de adopción avanzó a entrevista",
        badge="Citación a entrevista",
        accent=_INDIGO,
        headline="Tu solicitud avanzó a la fase de entrevista",
        intro="tu solicitud superó la revisión inicial y queremos conocerte mejor.",
        note_title="Detalles de la cita",
        next_steps=(
            "Revisa los detalles de la cita indicados arriba.",
            "Si no puedes asistir, responde al refugio para reprogramarla.",
            "Durante la entrevista conversaremos sobre tu hogar y tu rutina.",
        ),
    ),
    (RequestKind.ADOPTION, RequestStatus.REJECTED): StatusContent(
        subject="Novedades sobre tu solicitud de adopción",
        badge="Solicitud no aprobada",
        accent=_SLATE,
        headline="Tu solicitud no fue aprobada en esta ocasión",
        intro=(
            "agradecemos sinceramente tu interés en adoptar. Después de revisar tu "
            "solicitud, el refugio decidió no aprobarla por el motivo que te compartimos "
            "a continuación."
        ),
        note_title="Motivo de la decisión",
        next_steps=(
            "Esta decisión aplica solo a esta solicitud: puedes postularte a otra mascota.",
            "Si tienes dudas, escríbenos desde la sección de contacto del sitio.",
        ),
    ),
    (RequestKind.SURRENDER, RequestStatus.APPROVED): StatusContent(
        subject="Tu solicitud de entrega fue aceptada",
        badge="Entrega aceptada",
        accent=_GREEN,
        headline="El refugio aceptó recibir a tu mascota",
        intro="el refugio aceptó tu solicitud de entrega responsable.",
        note_title="Mensaje del refugio",
        next_steps=(
            "El refugio te contactará para acordar el día y la hora de la entrega.",
            "Lleva su carné de vacunas e historial médico, si los tienes.",
            "Puedes traer su cama, juguetes o alimento habitual para facilitar su adaptación.",
        ),
    ),
    (RequestKind.SURRENDER, RequestStatus.IN_INTERVIEW): StatusContent(
        subject="Tu solicitud de entrega avanzó a cita de evaluación",
        badge="Cita de evaluación",
        accent=_INDIGO,
        headline="Queremos evaluar tu caso en una cita",
        intro="tu solicitud de entrega pasó la revisión inicial y requiere una cita de evaluación.",
        note_title="Detalles de la cita",
        next_steps=(
            "Revisa los detalles de la cita indicados arriba.",
            "Si no puedes asistir, responde al refugio para reprogramarla.",
            "En la cita revisaremos el estado de salud y el comportamiento de tu mascota.",
        ),
    ),
    (RequestKind.SURRENDER, RequestStatus.REJECTED): StatusContent(
        subject="Novedades sobre tu solicitud de entrega",
        badge="Entrega no aceptada",
        accent=_SLATE,
        headline="El refugio no puede recibir a tu mascota por ahora",
        intro=(
            "lamentamos informarte que el refugio no pudo aceptar tu solicitud de entrega "
            "por el motivo que te compartimos a continuación."
        ),
        note_title="Motivo de la decisión",
        next_steps=(
            "Puedes enviar la solicitud a otro de los refugios aliados del sitio.",
            "Si tienes dudas, escríbenos desde la sección de contacto del sitio.",
        ),
    ),
}


@dataclass(frozen=True)
class StatusEmail:
    """Cambio de estado de una solicitud que debe comunicarse al solicitante."""

    kind: RequestKind
    status: str
    to: str
    recipient_name: str
    tracking_code: str
    # Nota obligatoria que el administrador escribió al cambiar el estado.
    admin_note: str
    details: Details


class StatusNotifier:
    """Avisa por correo al solicitante cada vez que un administrador cambia el estado."""

    def __init__(self, sender: EmailSender, frontend_url: str, app_name: str) -> None:
        self._sender = sender
        self._frontend_url = frontend_url
        self._app_name = app_name

    async def status_changed(self, email: StatusEmail) -> bool:
        """Devuelve True si el correo salió y False si no fue posible enviarlo."""
        content = _CONTENT.get((email.kind, email.status))
        if content is None:
            return False
        subject = f"{self._app_name}: {content.subject}"
        tracking_url = build_tracking_url(self._frontend_url, email.tracking_code)
        html = _TEMPLATE.substitute(
            subject=escape(subject),
            app_name=escape(self._app_name),
            accent=content.accent,
            badge=escape(content.badge),
            headline=escape(content.headline),
            intro=escape(content.intro),
            recipient_name=escape(email.recipient_name),
            note_title=escape(content.note_title),
            # La nota la escribe una persona: se escapa y se respetan sus saltos de línea.
            admin_note=escape(email.admin_note).replace("\n", "<br />"),
            next_steps="".join(_STEP_ITEM.format(step=escape(step)) for step in content.next_steps),
            details_rows=render_detail_rows(email.details),
            tracking_code=escape(email.tracking_code),
            tracking_url=escape(tracking_url, quote=True),
        )
        steps = "".join(f"- {step}\n" for step in content.next_steps)
        text = (
            f"Hola {email.recipient_name}, {content.intro}\n\n"
            f"{content.note_title}:\n{email.admin_note}\n\n"
            f"Siguientes pasos:\n{steps}\n"
            f"Código de seguimiento: {email.tracking_code}\n"
            f"{render_detail_lines(email.details)}\n"
            f"Consulta el estado en: {tracking_url}\n"
        )
        return await deliver(self._sender, email.to, subject, html, text)
