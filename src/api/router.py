from fastapi import APIRouter

from src.api import health
from src.modules.adoption_requests.router import router as adoption_requests_router
from src.modules.auth.router import admin_users_router
from src.modules.auth.router import router as auth_router
from src.modules.breeds.router import admin_router as breeds_admin_router
from src.modules.breeds.router import public_router as breeds_public_router
from src.modules.contact_messages.router import admin_router as contact_admin_router
from src.modules.contact_messages.router import public_router as contact_public_router
from src.modules.metrics.router import router as metrics_router
from src.modules.personalities.router import router as personalities_router
from src.modules.pets.router import router as pets_router
from src.modules.shelters.router import router as shelters_router
from src.modules.site_content.router import admin_router as content_admin_router
from src.modules.site_content.router import public_router as content_public_router
from src.modules.surrender_requests.router import router as surrender_requests_router
from src.modules.testimonials.router import router as testimonials_router

api_router = APIRouter()

api_router.include_router(health.router)
api_router.include_router(auth_router)
api_router.include_router(admin_users_router)
api_router.include_router(pets_router)
api_router.include_router(personalities_router)
api_router.include_router(breeds_public_router)
api_router.include_router(breeds_admin_router)
api_router.include_router(shelters_router)
api_router.include_router(adoption_requests_router)
api_router.include_router(surrender_requests_router)
api_router.include_router(testimonials_router)
api_router.include_router(metrics_router)
api_router.include_router(contact_public_router)
api_router.include_router(contact_admin_router)
api_router.include_router(content_public_router)
api_router.include_router(content_admin_router)
