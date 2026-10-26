import asyncio
import smtplib
import ssl
from email.message import EmailMessage
from email.utils import formataddr

from src.notifications.interfaces import EmailDeliveryError

# La respuesta de la API espera al envío para poder informar si el correo salió.
_TIMEOUT_SECONDS = 10


class GmailEmailSender:
    """Implementación de EmailSender por SMTP con STARTTLS (smtp.gmail.com:587)."""

    def __init__(self, host: str, port: int, username: str, password: str, from_name: str) -> None:
        self._host = host
        self._port = port
        self._username = username
        # Gmail muestra la contraseña de aplicación en grupos separados por espacios.
        self._password = password.replace(" ", "")
        self._from = formataddr((from_name, username))

    async def send(self, to: str, subject: str, html: str, text: str) -> None:
        message = EmailMessage()
        message["From"] = self._from
        message["To"] = to
        message["Subject"] = subject
        message.set_content(text)
        message.add_alternative(html, subtype="html")
        try:
            # smtplib es bloqueante: se ejecuta en un hilo para no detener el servidor.
            await asyncio.to_thread(self._deliver, message)
        except smtplib.SMTPAuthenticationError as error:
            raise EmailDeliveryError(
                "Gmail rechazó el usuario o la contraseña de aplicación "
                f"(código {error.smtp_code}). Revisa SMTP_USERNAME y SMTP_PASSWORD."
            ) from error
        except (smtplib.SMTPException, OSError) as error:
            raise EmailDeliveryError(str(error)) from error

    def _deliver(self, message: EmailMessage) -> None:
        with smtplib.SMTP(self._host, self._port, timeout=_TIMEOUT_SECONDS) as smtp:
            smtp.starttls(context=ssl.create_default_context())
            smtp.ehlo()
            # Se autentica con un único método (PLAIN). `smtp.login()` reintenta con otros y,
            # como Gmail corta la conexión tras el primer rechazo, oculta el error real (535)
            # tras un "Connection unexpectedly closed".
            smtp.user, smtp.password = self._username, self._password
            smtp.auth("PLAIN", smtp.auth_plain)
            smtp.send_message(message)


class DisabledEmailSender:
    """Se usa cuando faltan las credenciales SMTP: todo envío se reporta como fallido."""

    async def send(self, to: str, subject: str, html: str, text: str) -> None:
        raise EmailDeliveryError("SMTP_USERNAME y SMTP_PASSWORD no están configurados")
