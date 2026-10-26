"""Textos editables de la página de Donaciones (CMS).

Siembra los textos que hasta ahora estaban fijos en el frontend para que la página conserve su
contenido. Los datos bancarios no son textos del CMS: se configuran en el .env del frontend.

Revision ID: 0020
Revises: 0019
"""

from collections.abc import Sequence
from uuid import uuid4

import sqlalchemy as sa
from alembic import op

revision: str = "0020"
down_revision: str | Sequence[str] | None = "0019"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

SECTION = "donations"

INITIAL_CONTENT: dict[str, str] = {
    "header_badge": "Donaciones",
    "header_title": "Ayúdanos a mantener viva la plataforma de esperanza",
    "header_title_highlight": "plataforma de esperanza",
    "header_text": (
        "Huellitas de Amor es gratuita para los refugios y para quienes adoptan, y queremos que "
        "siempre sea así. Detrás de cada ficha publicada hay un trabajo técnico constante que "
        "sostenemos con aportes voluntarios como el tuyo."
    ),
    "why_title": "¿Por qué necesitamos tu ayuda?",
    "why_text": (
        "Mantener la plataforma en línea tiene costos mensuales. Cada aporte se destina a "
        "cubrirlos, con total transparencia, para que el sistema siga operando sin cobrar nada a "
        "refugios ni adoptantes."
    ),
    "cost_1_title": "Servidores",
    "cost_1_text": (
        "Mantienen la plataforma encendida las 24 horas para que refugios y adoptantes la usen "
        "cuando lo necesiten."
    ),
    "cost_2_title": "Dominio web",
    "cost_2_text": (
        "La dirección con la que nos encuentran y comparten las fichas de los peluditos."
    ),
    "cost_3_title": "Base de datos",
    "cost_3_text": (
        "Guarda de forma segura las fichas, las solicitudes de adopción y los mensajes de cada "
        "refugio."
    ),
    "cost_4_title": "Almacenamiento de imágenes",
    "cost_4_text": (
        "Aloja las fotos que hacen que alguien se enamore de un perrito o gatito a primera vista."
    ),
    "cost_5_title": "Mejora continua",
    "cost_5_text": (
        "Optimización, seguridad y nuevas funciones para que más animales encuentren un hogar "
        "más rápido."
    ),
    "payment_title": "Transferencia a Bancolombia",
    "payment_text": (
        "Puedes donar desde tu app bancaria, por transferencia o en cualquier corresponsal."
    ),
    "qr_title": "Escanea y dona en segundos",
    "qr_text": (
        "Abre la app de Bancolombia, elige la opción de pagar o transferir con QR y escanea el "
        "código."
    ),
    "thanks_title": "Gracias por ser parte de esta historia",
    "thanks_text": (
        "Tu generosidad no se queda en una pantalla: se convierte en una ficha que alguien "
        "encuentra, en una solicitud que llega a tiempo y en un perrito o gatito que por fin "
        "duerme en un hogar. Cada aporte, por pequeño que parezca, es un granito de arena que "
        "cambia vidas de verdad."
    ),
    "thanks_signature": "Con cariño, el equipo de Huellitas de Amor",
}


def upgrade() -> None:
    table = sa.table(
        "site_content",
        sa.column("id", sa.String),
        sa.column("section", sa.String),
        sa.column("key", sa.String),
        sa.column("value", sa.Text),
    )
    op.bulk_insert(
        table,
        [
            {"id": str(uuid4()), "section": SECTION, "key": key, "value": value}
            for key, value in INITIAL_CONTENT.items()
        ],
    )


def downgrade() -> None:
    op.execute(
        sa.text("DELETE FROM site_content WHERE section = :section").bindparams(section=SECTION)
    )
