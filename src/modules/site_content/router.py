from typing import Annotated

from fastapi import APIRouter, Depends

from src.api.deps import DbSession
from src.core.responses import ResponsePayload, success
from src.modules.auth.dependencies import CurrentAdmin, require_global_admin
from src.modules.site_content.repository import SiteContentRepository
from src.modules.site_content.schemas import ContentOut, ContentUpdate
from src.modules.site_content.service import SiteContentService

# Lectura pública: la usan las páginas de Inicio y la Guía de Adopción.
public_router = APIRouter(prefix="/content", tags=["Contenido del sitio"])
# Edición: administradores generales (los textos son de todo el sitio).
admin_router = APIRouter(
    prefix="/admin/content", tags=["Contenido del sitio"], dependencies=[require_global_admin]
)


def get_site_content_service(db: DbSession) -> SiteContentService:
    return SiteContentService(SiteContentRepository(db))


SiteContentServiceDep = Annotated[SiteContentService, Depends(get_site_content_service)]


@public_router.get("/{section}", response_model=ResponsePayload[ContentOut])
async def get_content(section: str, service: SiteContentServiceDep):
    content = await service.get_section(section)
    return success(content, "Contenido obtenido exitosamente")


@admin_router.put("/{section}", response_model=ResponsePayload[ContentOut])
async def update_content(
    section: str, payload: ContentUpdate, admin: CurrentAdmin, service: SiteContentServiceDep
):
    content = await service.update_section(section, payload, admin.id)
    return success(content, "Contenido actualizado. Los cambios ya están publicados en el sitio.")
