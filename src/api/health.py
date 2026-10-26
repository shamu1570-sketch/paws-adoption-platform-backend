from fastapi import APIRouter
from sqlalchemy import text

from src.api.deps import DbSession
from src.core.responses import ResponsePayload, success

router = APIRouter(prefix="/health", tags=["Health"])


@router.get("", response_model=ResponsePayload[dict[str, str]])
async def health(db: DbSession):
    await db.execute(text("SELECT 1"))
    return success({"database": "up"}, "Servicio operativo")
