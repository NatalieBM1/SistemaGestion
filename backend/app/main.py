from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from slowapi.errors import RateLimitExceeded

from app.core.config import settings
from app.core.http_seguridad import CabecerasSeguridadMiddleware, LimiteCuerpoMiddleware
from app.core.rate_limit import (
    LimiteExcedido,
    limiter,
    manejar_limite_excedido,
    manejar_rate_limit_excedido,
)
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

# En producción no se publica la documentación ni el esquema de la API.
_docs = (
    {"docs_url": None, "redoc_url": None, "openapi_url": None} if settings.es_produccion else {}
)
app = FastAPI(title="Sistema de Remisiones API", **_docs)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, manejar_rate_limit_excedido)
app.add_exception_handler(LimiteExcedido, manejar_limite_excedido)

# Orden: el último que se agrega queda más afuera.
# 1) Límite de tamaño, por DENTRO de CORS: su 413 lleva las cabeceras CORS
#    y el navegador deja que el frontend lea el mensaje.
app.add_middleware(LimiteCuerpoMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    # Solo lo que usa el frontend (axios: get/post/put/patch/delete, con
    # Authorization y Content-Type JSON / form / multipart).
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type"],
    # Para que el frontend (otro dominio) pueda leer Retry-After de un 429.
    expose_headers=["Retry-After"],
)
# 2) Cabeceras de seguridad, lo más afuera: salen en todas las respuestas,
#    incluidas las de CORS (preflight) y los 413/429.
app.add_middleware(CabecerasSeguridadMiddleware, produccion=settings.es_produccion)

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
