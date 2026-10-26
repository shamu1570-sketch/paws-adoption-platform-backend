from typing import Annotated

from fastapi import Depends

from src.core.config import settings
from src.storage.interfaces import FileStorage
from src.storage.supabase import SupabaseStorage, UnconfiguredStorage


def get_file_storage() -> FileStorage:
    if settings.SUPABASE_URL and settings.SUPABASE_SERVICE_ROLE_KEY:
        return SupabaseStorage(
            settings.SUPABASE_URL,
            settings.SUPABASE_SERVICE_ROLE_KEY,
            settings.SUPABASE_STORAGE_BUCKET,
        )
    return UnconfiguredStorage()


FileStorageDep = Annotated[FileStorage, Depends(get_file_storage)]
