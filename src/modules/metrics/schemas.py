from datetime import datetime
from enum import StrEnum

from src.core.schemas import CamelModel


class MetricsOut(CamelModel):
    total_pets: int
    available_pets: int
    adopted_pets: int
    pending_adoptions: int
    # Solicitudes de adopción en revisión: pendientes o en entrevista.
    in_review_adoptions: int
    pending_surrenders: int
    unread_messages: int
    active_shelters: int


class TimelinePeriod(StrEnum):
    MONTHLY = "monthly"
    YEARLY = "yearly"


class TimelinePoint(CamelModel):
    """Un mes o un año de la gráfica de adopciones."""

    label: str
    period_start: datetime
    # Solicitudes de adopción recibidas en el periodo.
    received: int
    # Solicitudes aprobadas (adopciones concretadas) en el periodo.
    approved: int


class AlertItem(CamelModel):
    id: str
    title: str
    subtitle: str
    created_at: datetime | None


class AlertGroup(CamelModel):
    count: int
    # Los más antiguos primero: son los que más urge atender.
    items: list[AlertItem]


class AlertsOut(CamelModel):
    # Solicitudes de adopción pendientes desde hace más de 48 horas.
    stale_adoptions: AlertGroup
    # Mensajes de contacto que aún no tienen ninguna respuesta.
    unanswered_messages: AlertGroup
    pending_surrenders: AlertGroup


class DashboardOut(CamelModel):
    kpis: MetricsOut
    period: TimelinePeriod
    timeline: list[TimelinePoint]
    alerts: AlertsOut
