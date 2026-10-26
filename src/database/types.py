import json

from sqlalchemy import Text
from sqlalchemy.types import TypeDecorator


class JSONList(TypeDecorator):
    """Lista de strings guardada como texto JSON (ej: '["Juguetón", "Sociable"]')."""

    impl = Text
    cache_ok = True

    def process_bind_param(self, value, dialect):
        return json.dumps(value or [], ensure_ascii=False)

    def process_result_value(self, value, dialect):
        if not value:
            return []
        try:
            parsed = json.loads(value)
        except ValueError:
            return [item.strip() for item in value.split(",") if item.strip()]
        return parsed if isinstance(parsed, list) else [str(parsed)]
