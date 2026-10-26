from collections import Counter
from datetime import UTC, datetime, timedelta

from src.core.schemas import RequestStatus
from src.modules.auth.access import as_utc
from src.modules.metrics.interfaces import MetricsRepositoryPort
from src.modules.metrics.schemas import (
    AlertGroup,
    AlertItem,
    AlertsOut,
    DashboardOut,
    MetricsOut,
    TimelinePeriod,
    TimelinePoint,
)
from src.modules.pets.schemas import AdoptionStatus

# Una solicitud de adopción sin atender por más de este tiempo se marca como alerta.
STALE_ADOPTION_HOURS = 48
ALERT_ITEMS = 5
MONTHS_SHOWN = 12
YEARS_SHOWN = 5
_MONTH_NAMES = ("ene", "feb", "mar", "abr", "may", "jun", "jul", "ago", "sep", "oct", "nov", "dic")


def _periods(period: TimelinePeriod, now: datetime) -> list[datetime]:
    """Inicio de cada mes (últimos 12) o año (últimos 5), del más antiguo al actual."""
    if period == TimelinePeriod.YEARLY:
        return [
            datetime(now.year - back, 1, 1, tzinfo=UTC) for back in range(YEARS_SHOWN - 1, -1, -1)
        ]
    starts = []
    for back in range(MONTHS_SHOWN - 1, -1, -1):
        year, month = divmod(now.year * 12 + now.month - 1 - back, 12)
        starts.append(datetime(year, month + 1, 1, tzinfo=UTC))
    return starts


def _bucket(moment: datetime, period: TimelinePeriod) -> tuple[int, int]:
    moment = as_utc(moment)
    return (moment.year, 1) if period == TimelinePeriod.YEARLY else (moment.year, moment.month)


def _label(start: datetime, period: TimelinePeriod) -> str:
    if period == TimelinePeriod.YEARLY:
        return str(start.year)
    return f"{_MONTH_NAMES[start.month - 1]} {start.year}"


class MetricsService:
    def __init__(self, metrics: MetricsRepositoryPort) -> None:
        self._metrics = metrics

    async def get_metrics(self, shelter_id: str | None = None) -> MetricsOut:
        """Calcula los KPIs del panel; con `shelter_id` se limitan a ese refugio."""
        return MetricsOut(
            total_pets=await self._metrics.count_pets(shelter_id),
            available_pets=await self._metrics.count_pets(shelter_id, AdoptionStatus.AVAILABLE),
            adopted_pets=await self._metrics.count_pets(shelter_id, AdoptionStatus.ADOPTED),
            pending_adoptions=await self._metrics.count_adoption_requests(
                shelter_id, RequestStatus.PENDING
            ),
            in_review_adoptions=await self._metrics.count_adoption_requests(
                shelter_id, RequestStatus.PENDING, RequestStatus.IN_INTERVIEW
            ),
            pending_surrenders=await self._metrics.count_surrender_requests(
                shelter_id, RequestStatus.PENDING
            ),
            unread_messages=await self._metrics.count_unread_messages(shelter_id),
            active_shelters=await self._metrics.count_shelters(shelter_id),
        )

    async def get_dashboard(
        self, shelter_id: str | None, period: TimelinePeriod = TimelinePeriod.MONTHLY
    ) -> DashboardOut:
        now = datetime.now(UTC)
        return DashboardOut(
            kpis=await self.get_metrics(shelter_id),
            period=period,
            timeline=await self._timeline(shelter_id, period, now),
            alerts=await self._alerts(shelter_id, now),
        )

    async def _timeline(
        self, shelter_id: str | None, period: TimelinePeriod, now: datetime
    ) -> list[TimelinePoint]:
        starts = _periods(period, now)
        received, approved = await self._metrics.adoption_dates(shelter_id, starts[0])
        received_by = Counter(_bucket(moment, period) for moment in received)
        approved_by = Counter(_bucket(moment, period) for moment in approved)
        return [
            TimelinePoint(
                label=_label(start, period),
                period_start=start,
                received=received_by[_bucket(start, period)],
                approved=approved_by[_bucket(start, period)],
            )
            for start in starts
        ]

    async def _alerts(self, shelter_id: str | None, now: datetime) -> AlertsOut:
        stale_before = now - timedelta(hours=STALE_ADOPTION_HOURS)
        stale_count, stale = await self._metrics.stale_adoptions(
            shelter_id, stale_before, ALERT_ITEMS
        )
        message_count, messages = await self._metrics.unanswered_messages(shelter_id, ALERT_ITEMS)
        surrender_count, surrenders = await self._metrics.pending_surrenders(
            shelter_id, ALERT_ITEMS
        )
        return AlertsOut(
            stale_adoptions=AlertGroup(
                count=stale_count,
                items=[
                    AlertItem(
                        id=req.id,
                        title=f"{req.user_name} quiere adoptar a {req.pet_name}",
                        subtitle=req.tracking_code,
                        created_at=req.created_at,
                    )
                    for req in stale
                ],
            ),
            unanswered_messages=AlertGroup(
                count=message_count,
                items=[
                    AlertItem(
                        id=msg.id,
                        title=msg.subject,
                        subtitle=f"{msg.name} · {msg.shelter_name or 'Consulta general'}",
                        created_at=msg.created_at,
                    )
                    for msg in messages
                ],
            ),
            pending_surrenders=AlertGroup(
                count=surrender_count,
                items=[
                    AlertItem(
                        id=req.id,
                        title=f"Entrega de {req.pet_name} ({req.pet_type})",
                        subtitle=f"{req.user_name} · {req.shelter_name}",
                        created_at=req.created_at,
                    )
                    for req in surrenders
                ],
            ),
        )
