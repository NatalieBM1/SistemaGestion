from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

ROOT_ENV_FILE = Path(__file__).resolve().parents[3] / ".env"


class Settings(BaseSettings):
    # "production" (por defecto, lo más seguro) o "development". En
    # desarrollo se ven /docs, /redoc y /openapi.json y no se manda HSTS.
    # El .env local debe tener APP_ENV=development.
    app_env: str = "production"
    database_url: str
    secret_key: str
    # Administrador inicial (solo en producción; ver seed_auth.py): correo y
    # contraseña desde variables de entorno. Se crea una sola vez, con cambio
    # de contraseña obligatorio al primer ingreso. En desarrollo no se usan:
    # los usuarios salen de app/scripts/setup_usuarios.py.
    admin_initial_email: str | None = None
    admin_initial_password: str | None = None
    # Orígenes permitidos para CORS (frontend Vite en desarrollo). En producción
    # se debe fijar CORS_ORIGINS con el/los dominios reales, separados por coma.
    cors_origins: str = "http://localhost:5173,http://127.0.0.1:5173"
    # No existe una tabla dedicada para los datos de la propia empresa: el
    # histórico la trae importada como un Tercero más (razón social + NIT
    # propios), así que la identificamos por su NIT en vez de duplicar el
    # registro en una tabla nueva. Ver routers/empresa.py.
    empresa_nit: str = "900721501"
    # Texto de la resolución de habilitación que aparece en el recibo impreso
    # (hoja "Imprimir" del Excel original, fila "Resoluciones" de la hoja
    # "Empresa"). No existe un campo para esto en Tercero, así que vive en
    # configuración; se puede ajustar con EMPRESA_RESOLUCION_HABILITACION sin
    # tocar código. El texto de responsabilidad de IVA sí tiene campo propio:
    # usa Tercero.regimen (ver routers/empresa.py).
    empresa_resolucion_habilitacion: str = "Res. Habilitación 154 de Octubre 20/2014"

    # ── Correo saliente (recuperación de contraseña) ──────────────────────────
    # Configuración SMTP para enviar códigos de verificación.
    # En desarrollo puede usarse una cuenta Gmail con contraseña de aplicación,
    # o un servicio transaccional (Brevo, SendGrid, etc.).
    # Si no se configuran, el endpoint de forgot-password devuelve error 503.
    smtp_host: str = ""
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_password: str = ""
    smtp_from_name: str = "Transportes Guerreros"
    smtp_from_email: str = ""
    # Tiempo de vida del código de recuperación en minutos
    reset_token_expire_minutes: int = 15

    # ── Límite de intentos (login y recuperación de contraseña) ──────────────
    # Ver app/core/rate_limit.py. "memory://" guarda los contadores en el
    # propio proceso; para varios workers/instancias usar un Redis
    # (ej. "redis://host:6379/1", requiere el paquete redis).
    rate_limit_enabled: bool = True
    rate_limit_storage_uri: str = "memory://"

    # ── Pool de conexiones a Postgres (ver core/database.py) ──────────────────
    db_pool_size: int = 3
    db_max_overflow: int = 7

    model_config = SettingsConfigDict(env_file=ROOT_ENV_FILE, extra="ignore")

    @property
    def es_produccion(self) -> bool:
        return self.app_env.strip().lower() != "development"

    @property
    def cors_origins_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


settings = Settings()
