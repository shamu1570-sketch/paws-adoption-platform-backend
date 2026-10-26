"""Textos editables del sitio: secciones y claves permitidas, con su longitud máxima.

Es el contrato con el frontend (src/content/siteContentFields.ts): una clave nueva se agrega
en ambos lados y con su texto inicial en una migración.
"""

from enum import StrEnum

SHORT_TEXT = 150
LONG_TEXT = 1000
KEY_MAX_LENGTH = 80


class ContentSection(StrEnum):
    HOME = "home"
    ADOPTION_GUIDE = "adoption_guide"
    DONATIONS = "donations"


def _numbered(template: str, count: int) -> list[str]:
    return [template.format(n) for n in range(1, count + 1)]


def _limits(short: list[str], long: list[str]) -> dict[str, int]:
    return {key: SHORT_TEXT for key in short} | {key: LONG_TEXT for key in long}


SECTION_FIELDS: dict[ContentSection, dict[str, int]] = {
    ContentSection.HOME: _limits(
        short=[
            "hero_badge",
            "hero_title",
            "hero_title_highlight",
            "hero_fact_title",
            "featured_badge",
            "featured_title",
            *_numbered("trust_{}_title", 3),
            "about_badge",
            "about_title",
            "about_title_highlight",
            *_numbered("reason_{}_badge", 6),
            *_numbered("reason_{}_title", 6),
            "callout_title",
            "callout_footer",
        ],
        long=[
            "hero_subtitle",
            "hero_fact_text",
            *_numbered("trust_{}_text", 3),
            "about_subtitle",
            *_numbered("reason_{}_text", 6),
            "callout_text",
        ],
    ),
    ContentSection.ADOPTION_GUIDE: _limits(
        short=[
            "header_badge",
            "header_title",
            *_numbered("article_{}_category", 3),
            *_numbered("article_{}_title", 3),
            "banner_badge",
            "banner_title",
        ],
        long=[
            "header_subtitle",
            *_numbered("article_{}_text", 3),
            # Una recomendación por línea.
            *_numbered("article_{}_tips", 3),
            "banner_text",
        ],
    ),
    ContentSection.DONATIONS: _limits(
        short=[
            "header_badge",
            "header_title",
            "header_title_highlight",
            "why_title",
            *_numbered("cost_{}_title", 5),
            "payment_title",
            "qr_title",
            "thanks_title",
            "thanks_signature",
        ],
        long=[
            "header_text",
            "why_text",
            *_numbered("cost_{}_text", 5),
            "payment_text",
            "qr_text",
            "thanks_text",
        ],
    ),
}


def is_optional(key: str) -> bool:
    """Las frases resaltadas dentro de un título pueden quedar vacías."""
    return key.endswith("_highlight")


def is_tag(key: str) -> bool:
    """Etiquetas y categorías: textos cortos que se muestran como píldoras sobre los títulos."""
    return key.endswith(("_badge", "_category"))
