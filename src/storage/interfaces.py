from typing import Protocol


class FileStorage(Protocol):
    """Contrato de almacenamiento de archivos; la base de datos solo guarda la URL pública."""

    async def upload(self, path: str, content: bytes, content_type: str) -> str:
        """Sube el archivo y devuelve su URL pública."""
        ...

    async def delete(self, public_url: str) -> None:
        """Elimina el archivo si pertenece a este almacenamiento; en otro caso no hace nada."""
        ...
