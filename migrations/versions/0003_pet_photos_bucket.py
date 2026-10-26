"""Bucket público de Supabase Storage para las fotografías de mascotas.

Solo aplica en bases de Supabase (esquema `storage`); en cualquier otro PostgreSQL o en
SQLite no hace nada. En el entorno local lo crea además supabase/config.toml.

Revision ID: 0003
Revises: 0002
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0003"
down_revision: str | Sequence[str] | None = "0002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

BUCKET = "pet-photos"
MAX_FILE_SIZE_BYTES = 5 * 1024 * 1024
ALLOWED_MIME_TYPES = ["image/jpeg", "image/png", "image/webp"]


def _has_supabase_storage() -> bool:
    bind = op.get_bind()
    return bind.dialect.name == "postgresql" and sa.inspect(bind).has_table(
        "buckets", schema="storage"
    )


def upgrade() -> None:
    if not _has_supabase_storage():
        return
    # Sin políticas de escritura: solo el backend (service role) sube y borra archivos.
    statement = sa.text(
        """
        insert into storage.buckets (id, name, public, file_size_limit, allowed_mime_types)
        values (:bucket, :bucket, true, :max_size, :mime_types)
        on conflict (id) do update
        set public = excluded.public,
            file_size_limit = excluded.file_size_limit,
            allowed_mime_types = excluded.allowed_mime_types
        """
    ).bindparams(sa.bindparam("mime_types", type_=sa.ARRAY(sa.Text())))
    op.execute(
        statement.bindparams(
            bucket=BUCKET, max_size=MAX_FILE_SIZE_BYTES, mime_types=ALLOWED_MIME_TYPES
        )
    )


def downgrade() -> None:
    """No se elimina el bucket: borrarlo destruiría las fotografías ya subidas."""
