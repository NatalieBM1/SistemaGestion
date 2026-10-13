from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select

from app.core.config import settings
from app.core.database import get_session
from app.core.deps import require_permission
from app.models.tercero import Tercero
from app.models.ubicacion import Municipio
from app.schemas.empresa import EmpresaRead

router = APIRouter(prefix="/api/empresa", tags=["empresa"])


@router.get(
    "",
    response_model=EmpresaRead,
    dependencies=[Depends(require_permission("remisiones.leer"))],
)
def obtener_empresa(session: Session = Depends(get_session)):
    """No existe una tabla dedicada para los datos de la propia empresa: el
    histórico la trae importada como un Tercero más (identificado por su
    NIT, settings.empresa_nit). Si ese registro no existe, 404 — nunca se
    inventan datos de reemplazo."""
    tercero = session.exec(
        select(Tercero).where(Tercero.identificacion == settings.empresa_nit)
    ).first()
    if tercero is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=(
                f"No se encontró el registro de la empresa (NIT {settings.empresa_nit}) "
                "entre los terceros."
            ),
        )
    municipio = session.get(Municipio, tercero.municipio_id) if tercero.municipio_id else None
    return EmpresaRead(
        nombre=tercero.nombre,
        nit=tercero.identificacion,
        direccion=tercero.direccion,
        telefono=tercero.telefono or None,
        email=tercero.email or None,
        ciudad=municipio.nombre if municipio else None,
        responsabilidad_iva=tercero.regimen,
        resolucion_habilitacion=settings.empresa_resolucion_habilitacion,
    )
