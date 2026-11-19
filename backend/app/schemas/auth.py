from pydantic import BaseModel


class UsuarioMe(BaseModel):
    id: int
    nombre: str
    email: str
    roles: list[str]
    permisos: list[str] = []
    # Si es True la app solo deja cambiar la contraseña o cerrar sesión.
    debe_cambiar_password: bool = False


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    usuario: UsuarioMe


class RefreshRequest(BaseModel):
    refresh_token: str


class RefreshResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class ForgotPasswordRequest(BaseModel):
    email: str


class CambiarPasswordRequest(BaseModel):
    password_actual: str
    nueva_password: str


class ResetPasswordRequest(BaseModel):
    email: str
    codigo: str
    nueva_password: str
