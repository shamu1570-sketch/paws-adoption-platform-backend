from html import escape

from src.modules.contact_messages.model import ContactMessage
from src.modules.shelters.model import Shelter
from src.notifications.interfaces import EmailSender
from src.notifications.rendering import deliver, load_template

_TEMPLATE = load_template("contact_reply.html")
_REPLY_PREFIX = "Re: "
_LINE_BREAK = "<br />"


def _to_html(text: str) -> str:
    """Texto escrito por una persona: se escapa y se respetan sus saltos de línea."""
    return escape(text).replace("\n", _LINE_BREAK)


def _shelter_card(shelter: Shelter) -> str:
    """Datos oficiales del refugio que responde, al pie de la respuesta."""
    lines = [
        f'<div style="font-size:13px;font-weight:800;color:#0F172A;">{escape(shelter.name)}</div>',
        f"{escape(shelter.address)}, {escape(shelter.city)}",
        f"Tel. {escape(shelter.phone)} · {escape(shelter.email)}",
    ]
    if shelter.website:
        lines.append(escape(shelter.website))
    return (
        '<table role="presentation" width="100%" cellpadding="0" cellspacing="0" '
        'style="margin-top:16px;background-color:#FFF7ED;border:1px solid #FED7AA;'
        'border-radius:12px;"><tr><td style="padding:12px 16px;font-size:12px;'
        'line-height:1.6;color:#475569;">' + _LINE_BREAK.join(lines) + "</td></tr></table>"
    )


class ContactReplyNotifier:
    """Envía al remitente la respuesta de un administrador, citando su mensaje original."""

    def __init__(self, sender: EmailSender, app_name: str) -> None:
        self._sender = sender
        self._app_name = app_name

    async def send_reply(self, message: ContactMessage, body: str, admin_name: str) -> bool:
        """Devuelve True si el correo salió y False si no fue posible enviarlo."""
        subject = message.subject
        if not subject.lower().startswith(_REPLY_PREFIX.lower()):
            subject = f"{_REPLY_PREFIX}{subject}"
        received = message.created_at.strftime("%d/%m/%Y") if message.created_at else ""
        # Los mensajes dirigidos a un refugio se responden en su nombre y con sus datos.
        shelter = message.shelter
        if shelter is not None:
            team_line = (
                f'Respuesta enviada por <strong style="color:#0F172A;">{escape(shelter.name)}'
                f"</strong> a través de {escape(self._app_name)}"
            )
            signature = (
                f"Respuesta enviada por {shelter.name}\n{shelter.address}, {shelter.city}\n"
                f"Tel. {shelter.phone} · {shelter.email}"
            )
        else:
            team_line = f"Equipo de {escape(self._app_name)}"
            signature = self._app_name
        html = _TEMPLATE.substitute(
            subject=escape(subject),
            app_name=escape(self._app_name),
            recipient_name=escape(message.name),
            reply_body=_to_html(body),
            admin_name=escape(admin_name),
            team_line=team_line,
            shelter_card=_shelter_card(shelter) if shelter is not None else "",
            original_subject=escape(message.subject),
            original_date=escape(received),
            original_message=_to_html(message.message),
        )
        quoted = "\n".join(f"> {line}" for line in message.message.splitlines())
        text = (
            f"Hola {message.name},\n\n{body}\n\n"
            f"{admin_name}\n{signature}\n\n"
            f"--- Tu mensaje del {received} ({message.subject}) ---\n{quoted}\n"
        )
        return await deliver(self._sender, message.email, subject, html, text)
