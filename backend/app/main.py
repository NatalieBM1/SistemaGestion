from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.routers import (
    activos,
    admin,
    auth,
    catalogos,
    empresa,
    facturas,
    ordenes_servicio,
    remision_productos,
    remisiones,
    reportes,
    terceros,
    ubicaciones,
)
from app.routers.activos import empresas_router
from app.routers.admin import permisos_router

app = FastAPI(title="Sistema de Remisiones API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(catalogos.router)
app.include_router(terceros.router)
app.include_router(ubicaciones.router)
app.include_router(activos.router)
app.include_router(empresas_router)
app.include_router(admin.router)
app.include_router(permisos_router)
app.include_router(remisiones.router)
app.include_router(ordenes_servicio.router)
app.include_router(remision_productos.router)
app.include_router(facturas.router)
app.include_router(reportes.router)
app.include_router(empresa.router)


@app.get("/health")
def health_check():
    return {"status": "ok"}
