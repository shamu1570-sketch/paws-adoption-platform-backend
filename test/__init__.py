import os

# La app exige estas variables al importarse; las pruebas usan su propia base SQLite en memoria.
os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite://")
os.environ.setdefault("JWT_SECRET_KEY", "test-only-secret-key-with-at-least-32-bytes")
