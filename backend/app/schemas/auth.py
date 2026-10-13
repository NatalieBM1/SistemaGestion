from pydantic import BaseModel


class UsuarioMe(BaseModel):
    id: int
    nombre: str
    email: str
    roles: list[str]
    permisos: list[str] = []


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
