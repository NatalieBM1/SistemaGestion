from pydantic import BaseModel


class EmpresaRead(BaseModel):
    nombre: str
    nit: str
    direccion: str
    telefono: str | None = None
    email: str | None = None
    ciudad: str | None = None
    responsabilidad_iva: str
    resolucion_habilitacion: str
