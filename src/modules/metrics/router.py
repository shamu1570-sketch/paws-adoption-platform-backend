from typing import Annotated

from fastapi import APIRouter, Depends, Query

from src.api.deps import DbSession
from src.core.responses import ResponsePayload, success
from src.modules.auth.dependencies import AdminScopeDep
from src.modules.metrics.repository import MetricsRepository
from src.modules.metrics.schemas import DashboardOut, MetricsOut, TimelinePeriod
from src.modules.metrics.service import MetricsService

router = APIRouter(prefix="/admin/metrics", tags=["Métricas"])

# Un administrador de refugio siempre ve sus datos; los generales pueden filtrar por refugio.
ShelterFilter = Annotated[str | None, Query(alias="shelterId")]


def get_metrics_service(db: DbSession) -> MetricsService:
    return MetricsService(MetricsRepository(db))


MetricsServiceDep = Annotated[MetricsService, Depends(get_metrics_service)]


@router.get("", response_model=ResponsePayload[MetricsOut])
async def get_metrics(
    service: MetricsServiceDep, scope: AdminScopeDep, shelter_id: ShelterFilter = None
):
    metrics = await service.get_metrics(scope.restrict(shelter_id))
    return success(metrics, "Métricas generales del sistema obtenidas exitosamente")


@router.get("/dashboard", response_model=ResponsePayload[DashboardOut])
async def get_dashboard(
    service: MetricsServiceDep,
    scope: AdminScopeDep,
    shelter_id: ShelterFilter = None,
    period: TimelinePeriod = TimelinePeriod.MONTHLY,
):
    """KPIs, gráfica de adopciones (mensual o anual) y alertas prioritarias del panel."""
    dashboard = await service.get_dashboard(scope.restrict(shelter_id), period)
    return success(dashboard, "Resumen del panel obtenido exitosamente")
