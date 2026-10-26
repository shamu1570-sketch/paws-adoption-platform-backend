from dataclasses import dataclass
from html import escape

from src.notifications.interfaces import EmailSender
from src.notifications.rendering import (
    Details,
    build_tracking_url,
    deliver,
    load_template,
    render_detail_lines,
    render_detail_rows,
)

_TEMPLATE = load_template("tracking_code.html")


@dataclass(frozen=True)
class TrackingEmail:
    """Datos de una solicitud recién recibida a la que se le asignó un código."""

    to: str
    recipient_name: str
    tracking_code: str
    details: Details


class TrackingNotifier:
    """Envía por correo el código de seguimiento de las solicitudes recién recibidas.

    Cada método devuelve True si el correo salió y False si no fue posible enviarlo.
    """

    def __init__(self, sender: EmailSender, frontend_url: str, app_name: str) -> None:
        self._sender = sender
        self._frontend_url = frontend_url
        self._app_name = app_name

    async def adoption_received(self, email: TrackingEmail) -> bool:
        return await self._send(
            email,
            headline="¡Recibimos tu solicitud de adopción!",
            intro=(
                "gracias por querer darle un hogar a una de nuestras huellitas. "
                "El equipo del refugio revisará tu solicitud y te contactará pronto."
            ),
        )

    async def surrender_received(self, email: TrackingEmail) -> bool:
        return await self._send(
            email,
            headline="Recibimos tu solicitud de entrega responsable",
            intro=(
                "gracias por buscar un lugar seguro para tu mascota. "
                "El refugio evaluará la solicitud y te contactará para coordinar "
                "los siguientes pasos."
            ),
        )

    async def _send(self, email: TrackingEmail, headline: str, intro: str) -> bool:
        subject = f"{self._app_name}: tu código de seguimiento {email.tracking_code}"
        tracking_url = build_tracking_url(self._frontend_url, email.tracking_code)
        html = _TEMPLATE.substitute(
            subject=escape(subject),
            app_name=escape(self._app_name),
            headline=escape(headline),
            intro=escape(intro),
            recipient_name=escape(email.recipient_name),
            details_rows=render_detail_rows(email.details),
            tracking_code=escape(email.tracking_code),
            tracking_url=escape(tracking_url, quote=True),
        )
        text = (
            f"Hola {email.recipient_name}, {intro}\n\n"
            f"Tu código de seguimiento: {email.tracking_code}\n"
            f"{render_detail_lines(email.details)}\n"
            f"Consulta el estado en: {tracking_url}\n"
        )
        return await deliver(self._sender, email.to, subject, html, text)
