from typing import Protocol


class EmailDeliveryError(Exception):
    """El proveedor de correo rechazó el mensaje o no se pudo contactar."""


class EmailSender(Protocol):
    """Contrato de envío de correo; la lógica de negocio no conoce al proveedor (Gmail)."""

    async def send(self, to: str, subject: str, html: str, text: str) -> None:
        """Envía el mensaje o lanza EmailDeliveryError."""
        ...
