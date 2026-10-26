from src.core.exceptions import ConflictError
from src.core.schemas import RequestStatus

# Estados a los que puede pasar una solicitud (de adopción o de entrega) desde cada estado.
# Aprobado y rechazado son finales.
_ALLOWED_TRANSITIONS: dict[str, frozenset[str]] = {
    RequestStatus.PENDING: frozenset(
        {RequestStatus.IN_INTERVIEW, RequestStatus.APPROVED, RequestStatus.REJECTED}
    ),
    RequestStatus.IN_INTERVIEW: frozenset({RequestStatus.APPROVED, RequestStatus.REJECTED}),
}


def ensure_transition_allowed(current: str, new: str) -> None:
    """Lanza 409 si la solicitud no puede pasar de `current` a `new`."""
    if new not in _ALLOWED_TRANSITIONS.get(current, frozenset()):
        raise ConflictError(
            f"Una solicitud en estado '{current}' no puede pasar a '{new}'",
            f"Transition {current} -> {new} is not allowed.",
        )
