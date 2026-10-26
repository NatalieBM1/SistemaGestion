from pydantic import BaseModel


class EmpresaRead(BaseModel):
    nombre: str
    nit: str
    direccion: str | None = None
    telefono: str | None = None
    email: str | None = None
    ciudad: str | None = None
    responsabilidad_iva: str | None = None
    resolucion_habilitacion: str
