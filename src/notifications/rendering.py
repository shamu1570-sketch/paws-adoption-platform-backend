"""Piezas comunes a todos los correos: carga de plantillas, filas de detalle y envío tolerante."""

import logging
from html import escape
from pathlib import Path
from string import Template
from urllib.parse import urlencode

from src.notifications.interfaces import EmailDeliveryError, EmailSender

logger = logging.getLogger(__name__)

_TEMPLATES_DIR = Path(__file__).with_name("templates")

# Pares (etiqueta, valor) que se muestran como tabla de resumen.
Details = tuple[tuple[str, str], ...]

_DETAIL_ROW = Template(
    "                  <tr>"
    '<td style="padding:10px 14px;color:#64748B;border-bottom:1px solid #F1F5F9;">${label}</td>'
    '<td style="padding:10px 14px;color:#0F172A;font-weight:700;text-align:right;'
    'border-bottom:1px solid #F1F5F9;">${value}</td>'
    "</tr>\n"
)


def load_template(file_name: str) -> Template:
    return Template(_TEMPLATES_DIR.joinpath(file_name).read_text(encoding="utf-8"))


def render_detail_rows(details: Details) -> str:
    """Filas HTML del resumen; los valores escritos por usuarios se escapan."""
    return "".join(
        _DETAIL_ROW.substitute(label=escape(label), value=escape(value)) for label, value in details
    )


def render_detail_lines(details: Details) -> str:
    """Versión en texto plano del resumen."""
    return "".join(f"{label}: {value}\n" for label, value in details)


def build_tracking_url(frontend_url: str, tracking_code: str) -> str:
    return f"{frontend_url.rstrip('/')}/?{urlencode({'seguimiento': tracking_code})}"


async def deliver(sender: EmailSender, to: str, subject: str, html: str, text: str) -> bool:
    """Envía el correo e indica si el proveedor lo aceptó; nunca propaga el fallo.

    Los correos son avisos: si el envío falla, la operación de negocio ya quedó registrada.
    El fallo se registra sin incluir datos personales.
    """
    try:
        await sender.send(to, subject, html, text)
    except EmailDeliveryError as error:
        logger.warning("No se pudo enviar un correo de notificación: %s", error)
        return False
    return True
