from html import escape
from urllib.parse import urlencode

from src.modules.auth.schemas import InvitationOut
from src.notifications.interfaces import EmailSender
from src.notifications.rendering import deliver, load_template

_TEMPLATE = load_template("admin_invitation.html")

_ROLE_LABELS = {
    "adoption_admin": "Administrador de Adopción",
    "super_admin": "Super Administrador",
}


def build_registration_url(frontend_url: str) -> str:
    """Enlace a la pantalla de registro del panel. La llave nunca viaja en la URL."""
    return f"{frontend_url.rstrip('/')}/?{urlencode({'registro': 'admin'})}"


class InvitationNotifier:
    """Envía al invitado su llave de registro de un solo uso."""

    def __init__(self, sender: EmailSender, frontend_url: str, app_name: str) -> None:
        self._sender = sender
        self._frontend_url = frontend_url
        self._app_name = app_name

    async def send_invitation(self, invitation: InvitationOut, invited_by: str) -> bool:
        """Devuelve True si el correo salió y False si no fue posible enviarlo."""
        to, access_key = invitation.email, invitation.access_key
        shelter_name = invitation.shelter_name
        role_label = _ROLE_LABELS.get(invitation.role, invitation.role)
        # Alcance de la cuenta: un refugio específico o todos (administrador general).
        scope_label = f"el refugio {shelter_name}" if shelter_name else "todos los refugios"
        expires = invitation.expires_at.strftime("%d/%m/%Y %H:%M UTC")
        subject = f"{self._app_name}: tu invitación como {role_label}"
        registration_url = build_registration_url(self._frontend_url)
        html = _TEMPLATE.substitute(
            subject=escape(subject),
            app_name=escape(self._app_name),
            role_label=escape(role_label),
            scope_label=escape(scope_label),
            invited_by=escape(invited_by),
            access_key=escape(access_key),
            email=escape(to),
            expires=escape(expires),
            registration_url=escape(registration_url, quote=True),
        )
        text = (
            f"Hola,\n\n{invited_by} te invitó a {self._app_name} como {role_label} "
            f"para gestionar {scope_label}.\n\n"
            f"Tu llave de registro: {access_key}\n\n"
            f"Regístrate en: {registration_url}\n"
            '(elige "Tengo una llave de acceso: registrarme").\n\n'
            f"- Es de un solo uso y solo funciona con este correo: {to}\n"
            f"- Vence el {expires}\n"
            "- No la compartas con nadie. Si no esperabas esta invitación, ignora este correo.\n"
        )
        return await deliver(self._sender, to, subject, html, text)
