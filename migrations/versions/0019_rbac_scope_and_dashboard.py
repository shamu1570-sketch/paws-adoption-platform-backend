"""Alcance por refugio (RBAC), vigencia de acceso, mensajes por refugio y analíticas.

- admins: `is_global`, `shelter_id` y ventana de acceso (`access_starts_at`/`access_expires_at`).
  Los administradores existentes quedan como generales para no perder acceso.
- admin_invitations: alcance que recibirá la cuenta al registrarse.
- contact_messages: motivo (`topic`), refugio destinatario y mascota de interés.
- adoption_requests: `status_changed_at` (fecha de la decisión) para la gráfica de adopciones;
  en las solicitudes ya resueltas se usa su fecha de creación como aproximación.

Revision ID: 0019
Revises: 0018
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0019"
down_revision: str | Sequence[str] | None = "0018"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

ID_LENGTH = 36
# (tabla, columna, tabla referida, acción al borrar)
FOREIGN_KEYS = (
    ("admins", "shelter_id", "shelters", "SET NULL"),
    ("admin_invitations", "shelter_id", "shelters", "CASCADE"),
    ("contact_messages", "shelter_id", "shelters", "SET NULL"),
    ("contact_messages", "pet_id", "pets", "SET NULL"),
)
INDEXES = (
    ("admins", "shelter_id"),
    ("admin_invitations", "shelter_id"),
    ("contact_messages", "shelter_id"),
    ("adoption_requests", "status_changed_at"),
)


def _fk_name(table: str, column: str, referred: str) -> str:
    return f"fk_{table}_{column}_{referred}"


def upgrade() -> None:
    op.add_column(
        "admins", sa.Column("is_global", sa.Boolean(), server_default=sa.false(), nullable=False)
    )
    op.add_column("admins", sa.Column("shelter_id", sa.String(length=ID_LENGTH), nullable=True))
    op.add_column("admins", sa.Column("access_starts_at", sa.DateTime(timezone=True)))
    op.add_column("admins", sa.Column("access_expires_at", sa.DateTime(timezone=True)))
    op.execute("UPDATE admins SET is_global = true")

    op.add_column(
        "admin_invitations",
        sa.Column("is_global", sa.Boolean(), server_default=sa.false(), nullable=False),
    )
    op.add_column(
        "admin_invitations", sa.Column("shelter_id", sa.String(length=ID_LENGTH), nullable=True)
    )
    # Las llaves pendientes se emitieron cuando todos los administradores eran generales.
    op.execute("UPDATE admin_invitations SET is_global = true")

    op.add_column(
        "contact_messages",
        sa.Column("topic", sa.String(length=20), server_default="general", nullable=False),
    )
    op.add_column(
        "contact_messages", sa.Column("shelter_id", sa.String(length=ID_LENGTH), nullable=True)
    )
    op.add_column(
        "contact_messages", sa.Column("pet_id", sa.String(length=ID_LENGTH), nullable=True)
    )
    op.add_column("contact_messages", sa.Column("pet_name", sa.String(length=50), nullable=True))

    op.add_column("adoption_requests", sa.Column("status_changed_at", sa.DateTime(timezone=True)))
    op.execute(
        "UPDATE adoption_requests SET status_changed_at = created_at WHERE status <> 'pendiente'"
    )

    for table, column, referred, ondelete in FOREIGN_KEYS:
        op.create_foreign_key(
            _fk_name(table, column, referred), table, referred, [column], ["id"], ondelete=ondelete
        )
    for table, column in INDEXES:
        op.create_index(op.f(f"ix_{table}_{column}"), table, [column])


def downgrade() -> None:
    for table, column in INDEXES:
        op.drop_index(op.f(f"ix_{table}_{column}"), table_name=table)
    for table, column, referred, _ in FOREIGN_KEYS:
        op.drop_constraint(_fk_name(table, column, referred), table, type_="foreignkey")
    op.drop_column("adoption_requests", "status_changed_at")
    for column in ("pet_name", "pet_id", "shelter_id", "topic"):
        op.drop_column("contact_messages", column)
    for column in ("shelter_id", "is_global"):
        op.drop_column("admin_invitations", column)
    for column in ("access_expires_at", "access_starts_at", "shelter_id", "is_global"):
        op.drop_column("admins", column)
