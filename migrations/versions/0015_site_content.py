"""Textos editables del sitio (CMS): Inicio y Guía de Adopción.

Siembra los textos que hasta ahora estaban fijos en el frontend para que las páginas
conserven su contenido.

Revision ID: 0015
Revises: 0014
"""

from collections.abc import Sequence
from uuid import uuid4

import sqlalchemy as sa
from alembic import op

revision: str = "0015"
down_revision: str | Sequence[str] | None = "0014"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

TABLE = "site_content"
CLIENT_ROLES = ["anon", "authenticated"]
ID_LENGTH = 36

INITIAL_CONTENT: dict[str, dict[str, str]] = {
    "home": {
        "hero_badge": "Adopción Responsable en 2036",
        "hero_title": "Encuentra a tu compañero de vida",
        "hero_title_highlight": "compañero de vida",
        "hero_subtitle": (
            "En Huellitas de Amor, unimos corazones. Creemos que cada perro y gato merece un "
            "hogar seguro y feliz. Descubre mascotas disponibles para adopción y dales una "
            "segunda oportunidad."
        ),
        "hero_fact_title": "El superpoder de un peludo 🐾",
        "hero_fact_text": (
            "¿Sabías que un perro o un gato puede entender tu estado de ánimo con solo mirarte? "
            "Adoptar a un compañero no solo les da un hogar seguro, sino que llena tus días de "
            "alegría sincera, risas inesperadas y un amor tan puro que no necesita palabras."
        ),
        "featured_badge": "Mascota de la semana",
        "featured_title": "Esperando un Hogar Amoroso",
        "trust_1_title": "Refugios Verificados",
        "trust_1_text": (
            "Validamos personalmente las instalaciones y protocolos médicos de cada asociación "
            "registrada."
        ),
        "trust_2_title": "Red de Albergues",
        "trust_2_text": (
            "Conectamos más de 85 refugios a nivel nacional para facilitar adopciones responsables."
        ),
        "trust_3_title": "Acompañamiento Continuo",
        "trust_3_text": (
            "Brindamos asesoría veterinaria y de adaptación durante los primeros meses en su "
            "nuevo hogar."
        ),
        "about_badge": "Adopción vs Compra",
        "about_title": "¿Por qué es mejor adoptar que comprar?",
        "about_title_highlight": "mejor adoptar",
        "about_subtitle": (
            "Tomar la decisión de dar la bienvenida a una mascota es emocionante. Elegir la "
            "adopción responsable es un acto transformador que cambia vidas y deja una huella "
            "imborrable de bondad en el mundo."
        ),
        "reason_1_badge": "Héroe sin capa",
        "reason_1_title": "Salvas una vida real",
        "reason_1_text": (
            "Cada año, millones de perros y gatos sanos y sociables son abandonados. Al adoptar, "
            "estás rescatando directamente a un ser maravilloso y dándole el hogar seguro que "
            "tanto anhela."
        ),
        "reason_2_badge": "Consumo Consciente",
        "reason_2_title": "Dices NO al comercio cruel",
        "reason_2_text": (
            "Muchos animales vendidos provienen de criaderos clandestinos o 'fábricas de "
            "cachorros' donde las madres viven explotadas en condiciones deplorables. Adoptar "
            "rompe ese ciclo de explotación."
        ),
        "reason_3_badge": "Amor Genuino",
        "reason_3_title": "Recibes un agradecimiento eterno",
        "reason_3_text": (
            "Los animales adoptados parecen comprender que se les ha dado una segunda "
            "oportunidad. El vínculo y la lealtad que desarrollan con su nueva familia es "
            "extraordinario y conmovedor."
        ),
        "reason_4_badge": "Únicos & Fuertes",
        "reason_4_title": "Mascotas únicas, fuertes y sociables",
        "reason_4_text": (
            "Las mascotas mestizas o criollas tienen una diversidad genética que suele hacerlas "
            "más resistentes a enfermedades hereditarias. Además, la mayoría de los refugios ya "
            "conocen el carácter de cada peludo."
        ),
        "reason_5_badge": "Efecto Multiplicador",
        "reason_5_title": "Apoyas a toda la comunidad",
        "reason_5_text": (
            "Al adoptar una mascota de nuestro catálogo o un refugio local, liberas espacio y "
            "recursos para que otra mascota en peligro pueda ser rescatada y cuidada hasta "
            "encontrar su propio hogar."
        ),
        "reason_6_badge": "Amigos de Verdad",
        "reason_6_title": "Felicidad pura sin etiquetas",
        "reason_6_text": (
            "Un amigo de cuatro patas no necesita un certificado de raza para llenar tu casa de "
            "risas, juegos y compañía. El amor puro e incondicional no se compra, se comparte."
        ),
        "callout_title": "Cada segundo cuenta para ellos",
        "callout_text": (
            "Cuando compras una mascota de vitrina o de criadero, estás apoyando un negocio "
            "comercial lucrativo. Cuando adoptas, abres las puertas a un ser que de otra manera "
            "no conocería el calor de una cama suave, una caricia sincera o un plato lleno de "
            "comida. No dejes que el prejuicio te guíe: los animales adoptados son los "
            "compañeros más leales e increíbles que podrás conocer."
        ),
        "callout_footer": "¡Cambia un destino hoy mismo!",
    },
    "adoption_guide": {
        "header_badge": "Guía de Tenencia Responsable",
        "header_title": "Aprende a Cuidar de tu Compañero",
        "header_subtitle": (
            "Adoptar es un compromiso de amor para toda la vida. Te brindamos consejos prácticos "
            "respaldados por médicos veterinarios para garantizar una convivencia feliz."
        ),
        "article_1_category": "Salud",
        "article_1_title": "Cuidados Médicos y Esquema de Vacunación",
        "article_1_text": (
            "Conoce la importancia de mantener las vacunas sextuples y desparasitaciones al día. "
            "La medicina preventiva evita enfermedades complejas y garantiza una vida larga."
        ),
        "article_1_tips": (
            "Desparasitación interna cada 3 a 6 meses.\n"
            "Vacuna rabia anual obligatoria.\n"
            "Visitas periódicas al veterinario 2 veces al año."
        ),
        "article_2_category": "Adaptación",
        "article_2_title": "Preparación de la Casa para tu Nuevo Peludito",
        "article_2_text": (
            "Los primeros días en un nuevo hogar generan ansiedad normal. Prepara su espacio con "
            "cama limpia, agua fresca y juguetes para morder o arañar."
        ),
        "article_2_tips": (
            "Instala mallas protectoras en balcones si tienes gatos.\n"
            "Guarda productos de limpieza e insecticidas bajo llave.\n"
            "Asigna una zona tranquila y silenciosa para sus comidas."
        ),
        "article_3_category": "Nutrición",
        "article_3_title": "Alimentación Según la Etapa de Vida",
        "article_3_text": (
            "Cada etapa (cachorro, joven, adulto o senior) requiere requerimientos calóricos e "
            "ingredientes distintos para un desarrollo óptimo."
        ),
        "article_3_tips": (
            "Evita alimentos altamente tóxicos como chocolate, cebolla y uvas.\n"
            "Manten acceso continuo a agua limpia y fresca.\n"
            "Respeta las porciones recomendadas por tu veterinario."
        ),
        "banner_badge": "Antes de Adoptar",
        "banner_title": "¿Estás listo para dar este gran paso?",
        "banner_text": (
            "Asegúrate de contar con la aprobación de toda tu familia, estabilidad para cubrir "
            "sus gastos de alimentación y salud, y sobre todo tiempo para brindarle amor y "
            "paseos."
        ),
    },
}


def upgrade() -> None:
    table = op.create_table(
        TABLE,
        sa.Column("id", sa.String(length=ID_LENGTH), nullable=False),
        sa.Column("section", sa.String(length=50), nullable=False),
        sa.Column("key", sa.String(length=80), nullable=False),
        sa.Column("value", sa.Text(), nullable=False),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column("updated_by", sa.String(length=ID_LENGTH), nullable=True),
        sa.ForeignKeyConstraint(["updated_by"], ["admins.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("section", "key", name="uq_site_content_section_key"),
    )
    op.create_index(op.f("ix_site_content_section"), TABLE, ["section"])
    _deny_client_access(TABLE)
    op.bulk_insert(
        table,
        [
            {"id": str(uuid4()), "section": section, "key": key, "value": value}
            for section, values in INITIAL_CONTENT.items()
            for key, value in values.items()
        ],
    )


def _deny_client_access(table: str) -> None:
    """Cierra la tabla a la API de datos de Supabase (roles anon y authenticated).

    La lectura pública se sirve por `GET /api/v1/content/{section}` y la escritura por
    `PUT /api/v1/admin/content/{section}`, que exige sesión de administrador.
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
    op.drop_index(op.f("ix_site_content_section"), table_name=TABLE)
    op.drop_table(TABLE)
