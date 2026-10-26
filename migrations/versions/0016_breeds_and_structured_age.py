"""Catálogo de razas por especie y edad estructurada (cantidad + unidad) de las mascotas.

- Crea `breeds` con RLS y lo siembra con razas comunes más las que ya usan las fichas,
  para que ninguna mascota quede con una raza fuera del catálogo.
- Agrega `pets.age_value` y `pets.age_unit`, los completa a partir del texto libre de
  `pets.age` y recalcula `age` y `age_category` con las reglas de etapa de vida.

Revision ID: 0016
Revises: 0015
"""

import re
from collections.abc import Sequence
from uuid import uuid4

import sqlalchemy as sa
from alembic import op

revision: str = "0016"
down_revision: str | Sequence[str] | None = "0015"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

TABLE = "breeds"
CLIENT_ROLES = ["anon", "authenticated"]

DEFAULT_BREEDS = {
    "perro": [
        "Criollo / Mestizo",
        "Labrador Retriever",
        "Golden Retriever",
        "Pastor Alemán",
        "Bulldog Francés",
        "Beagle",
        "Poodle",
        "Chihuahua",
        "Schnauzer",
        "Pitbull",
        "Shih Tzu",
        "Yorkshire Terrier",
        "Husky Siberiano",
        "Border Collie",
    ],
    "gato": [
        "Criollo / Mestizo",
        "Siamés",
        "Persa",
        "Angora",
        "Maine Coon",
        "Bengalí",
        "Sphynx",
        "Británico de Pelo Corto",
    ],
}

MONTHS_PER_YEAR = 12
MAX_MONTHS = 24
# Límite superior (en meses, inclusive) de cada etapa; lo que pasa de 84 meses es senior.
STAGES = ((11, "cachorro"), (36, "joven"), (84, "adulto"))

# Edad aproximada por etapa, solo para textos que no se puedan interpretar.
_STAGE_FALLBACK = {"cachorro": (6, "meses"), "joven": (2, "años"), "adulto": (5, "años")}
_AGE_TEXT = re.compile(r"(\d+(?:[.,]\d+)?)\s*(a[ñn]o|mes)", re.IGNORECASE)


def _parse_age(text: str, category: str) -> tuple[int, str]:
    match = _AGE_TEXT.search(text or "")
    if match is None:
        return _STAGE_FALLBACK.get(category, (9, "años"))
    amount = float(match.group(1).replace(",", "."))
    months = amount if match.group(2).lower() == "mes" else amount * MONTHS_PER_YEAR
    months = max(1, round(months))
    if months % MONTHS_PER_YEAR == 0:
        return months // MONTHS_PER_YEAR, "años"
    # "1.5 años" -> 18 meses; más de 24 meses se redondea a años completos.
    if months <= MAX_MONTHS:
        return months, "meses"
    return months // MONTHS_PER_YEAR, "años"


def _life_stage(value: int, unit: str) -> str:
    months = value * MONTHS_PER_YEAR if unit == "años" else value
    for limit, stage in STAGES:
        if months <= limit:
            return stage
    return "senior"


def _age_label(value: int, unit: str) -> str:
    if value == 1:
        return "1 año" if unit == "años" else "1 mes"
    return f"{value} {unit}"


def upgrade() -> None:
    bind = op.get_bind()
    breeds = op.create_table(
        TABLE,
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("name", sa.String(length=60), nullable=False),
        sa.Column("species", sa.String(length=20), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("species", "name", name="uq_breeds_species_name"),
    )
    op.create_index(op.f("ix_breeds_species"), TABLE, ["species"])
    _deny_client_access(TABLE)

    catalog = {species: list(names) for species, names in DEFAULT_BREEDS.items()}
    for species, breed in bind.execute(sa.text("select distinct type, breed from pets")):
        known = {name.lower() for name in catalog.setdefault(species, [])}
        if breed and breed.lower() not in known:
            catalog[species].append(breed)
    op.bulk_insert(
        breeds,
        [
            {"id": str(uuid4()), "name": name, "species": species}
            for species, names in catalog.items()
            for name in names
        ],
    )

    op.add_column("pets", sa.Column("age_value", sa.Integer(), nullable=True))
    op.add_column("pets", sa.Column("age_unit", sa.String(length=10), nullable=True))
    pets = bind.execute(sa.text("select id, age, age_category from pets")).all()
    for pet_id, age, category in pets:
        value, unit = _parse_age(age, category)
        bind.execute(
            sa.text(
                "update pets set age_value = :value, age_unit = :unit, age = :label, "
                "age_category = :stage where id = :id"
            ),
            {
                "value": value,
                "unit": unit,
                "label": _age_label(value, unit),
                "stage": _life_stage(value, unit),
                "id": pet_id,
            },
        )
    op.alter_column("pets", "age_value", nullable=False)
    op.alter_column("pets", "age_unit", nullable=False)


def _deny_client_access(table: str) -> None:
    """Cierra la tabla a la API de datos de Supabase (roles anon y authenticated).

    La lectura pública se sirve por `GET /api/v1/breeds` y la escritura por
    `/api/v1/admin/breeds`, que exige sesión de administrador.
    """
    bind = op.get_bind()
    if bind.dialect.name != "postgresql":
        return
    op.execute(f"ALTER TABLE public.{table} ENABLE ROW LEVEL SECURITY")
    rows = bind.execute(
        sa.text("select rolname from pg_roles where rolname = any(:roles)"),
        {"roles": CLIENT_ROLES},
    )
    roles = ", ".join(row[0] for row in rows)
    if roles:
        op.execute(f"REVOKE ALL ON TABLE public.{table} FROM {roles}")
        op.execute(
            f"CREATE POLICY deny_client_access ON public.{table} AS RESTRICTIVE "
            f"FOR ALL TO {roles} USING (false) WITH CHECK (false)"
        )


def downgrade() -> None:
    # `age` conserva el texto ("2 años"), así que la ficha sigue mostrando la edad.
    op.drop_column("pets", "age_unit")
    op.drop_column("pets", "age_value")
    op.drop_index(op.f("ix_breeds_species"), table_name=TABLE)
    op.drop_table(TABLE)
