"""Entorno de Alembic: conecta con la base de `DATABASE_URL` y compara contra los modelos."""

import asyncio
from logging.config import fileConfig

from alembic import context
from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import create_async_engine

from src.core.config import settings
from src.database.connection import Base
from src.database.init_db import MODELS  # noqa: F401  (registra todos los modelos en Base.metadata)

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def include_object(_obj, name, type_, reflected, compare_to) -> bool:
    """Ignora las tablas que existen en la base pero no pertenecen a los modelos de la API.

    Así `--autogenerate` nunca propone borrar tablas ajenas (por ejemplo las de Supabase).
    """
    return not (type_ == "table" and reflected and compare_to is None)


def run_migrations_offline() -> None:
    """Genera el SQL sin conectarse: `alembic upgrade head --sql`."""
    context.configure(
        url=settings.DATABASE_URL,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        include_object=include_object,
    )
    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        include_object=include_object,
        compare_type=True,
    )
    with context.begin_transaction():
        context.run_migrations()


async def run_migrations_online() -> None:
    engine = create_async_engine(settings.DATABASE_URL, poolclass=pool.NullPool)
    async with engine.connect() as connection:
        await connection.run_sync(do_run_migrations)
    await engine.dispose()


if context.is_offline_mode():
    run_migrations_offline()
else:
    asyncio.run(run_migrations_online())
