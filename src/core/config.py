from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    APP_NAME: str = "Huellitas de Amor"
    APP_ENV: str = "development"
    DEBUG: bool = False

    API_PREFIX: str = "/api/v1"

    # Sin valor por defecto: las credenciales nunca se escriben en el código.
    DATABASE_URL: str

    # Orígenes permitidos separados por coma. Ej: http://localhost:3000,https://midominio.com
    CORS_ORIGINS: str = "http://localhost:3000,http://127.0.0.1:3000"

    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    # Llave para el alta inicial: registra al primer super_admin y deja de funcionar
    # en cuanto existe uno. Los demás se registran con llaves de un solo uso que él genera.
    ADMIN_REGISTRATION_KEY: str | None = None
    ADMIN_INVITATION_EXPIRE_HOURS: int = 72

    # Supabase Storage (fotos de mascotas). La service role key es secreta:
    # solo la usa el backend y nunca debe llegar al frontend.
    SUPABASE_URL: str | None = None
    SUPABASE_SERVICE_ROLE_KEY: str | None = None
    SUPABASE_STORAGE_BUCKET: str = "pet-photos"
    MAX_PHOTO_SIZE_MB: int = 5

    # Correo saliente por Gmail (SMTP). SMTP_PASSWORD es una "contraseña de aplicación",
    # no la contraseña de la cuenta. Sin usuario o contraseña no se envían correos.
    SMTP_HOST: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USERNAME: str | None = None
    SMTP_PASSWORD: str | None = None
    EMAIL_FROM_NAME: str = "Huellitas de Amor"
    # URL pública del frontend; se usa en los enlaces de seguimiento de los correos.
    FRONTEND_URL: str = "http://localhost:3000"

    @property
    def cors_origins(self) -> list[str]:
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
