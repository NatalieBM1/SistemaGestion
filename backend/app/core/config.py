from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

ROOT_ENV_FILE = Path(__file__).resolve().parents[3] / ".env"


class Settings(BaseSettings):
    database_url: str
    redis_url: str | None = None
    secret_key: str
    # Contraseña del usuario administrador inicial (solo la usa seed_auth.py,
    # una vez, para crear la cuenta si no existe). Sin valor por defecto a
    # propósito: hay que fijar ADMIN_INITIAL_PASSWORD en el .env antes de
    # correr el seed. Cámbiala desde la app apenas entres la primera vez.
    admin_initial_password: str
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

    model_config = SettingsConfigDict(env_file=ROOT_ENV_FILE, extra="ignore")

    @property
    def cors_origins_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


settings = Settings()
