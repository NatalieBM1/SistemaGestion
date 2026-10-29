# Sistema de Remisiones — Transportes Guerrero

Sistema de gestión de remisiones y facturación para empresas de transporte de carga. Backend en FastAPI + PostgreSQL, frontend en React + Vite.

---

## Stack

| Capa | Tecnología |
|---|---|
| Backend | FastAPI, SQLModel, Alembic, PostgreSQL |
| Frontend | React 19, Vite, TypeScript, Zustand, React Query |
| Autenticación | JWT (python-jose) |
| Despliegue | Render (render.yaml incluido) |

---

## Despliegue en Render

El repo incluye `render.yaml` que define tres servicios:

- **`sistemagestion-api`** — Web Service (Docker, FastAPI)
- **`sistemagestion-web`** — Static Site (React build)
- **`sistemagestion-db`** — PostgreSQL (plan free)

### Paso 1 — Conectar el repo

1. Entra a [render.com](https://render.com) → **New** → **Blueprint**.
2. Conecta este repo. Render detecta el `render.yaml` y crea los tres servicios.
3. Antes de hacer el primer deploy, ve al servicio `sistemagestion-api` → **Environment** y agrega manualmente:
   - `ADMIN_INITIAL_PASSWORD` — contraseña que tendrá el usuario administrador

### Paso 2 — Restaurar la base de datos con los datos reales

La base de datos viene vacía al crear el servicio en Render. El dump con los datos de la empresa está en:

```
backend/app/data_import/backups/remisiones_prod.sql
```

Para restaurarlo necesitas la **External Database URL** de Render:
1. En el dashboard de Render → servicio `sistemagestion-db` → **Info** → copia el valor de **External Database URL**.
2. Desde tu máquina local (con `psql` instalado), ejecuta:

```bash
psql "PEGA_AQUI_LA_EXTERNAL_DATABASE_URL" -f backend/app/data_import/backups/remisiones_prod.sql
```

> El dump incluye las migraciones aplicadas, todos los catálogos, terceros, remisiones históricas y facturas.
> El script de startup del backend (`alembic upgrade head` + `seed_auth.py`) es seguro de correr sobre una base ya cargada — Alembic detecta que las migraciones ya están aplicadas y `seed_auth.py` no toca la cuenta admin si ya existe.

### Paso 3 — Actualizar las URLs entre servicios

Una vez que Render asigne las URLs a los servicios (terminan en `.onrender.com`), actualiza:

- En `sistemagestion-api` → env var `CORS_ORIGINS` → pon la URL del frontend
- En `sistemagestion-web` → env var `VITE_API_URL` → pon la URL del backend

> Esto también se puede hacer antes del deploy editando `render.yaml` directamente con las URLs definitivas.

### Paso 4 — Entrar

Usuario administrador: `admin@transportesguerrero.com` + la contraseña que pusiste en `ADMIN_INITIAL_PASSWORD`.

> **Plan gratuito de Render:** los servicios inactivos se suspenden tras 15 min sin tráfico. El primer request tras inactividad puede tardar ~30 s mientras el servicio se reactiva.

---

## Desarrollo local

### Requisitos

- Docker y Docker Compose
- Python 3.12+
- Node 20+

### 1. Variables de entorno

```bash
cp .env.example .env
cp frontend/.env.example frontend/.env
```

Edita `.env` con tus valores.

### 2. Base de datos

```bash
docker compose up -d
```

Levanta Postgres en `5432`.

### 3. Backend

```bash
cd backend
python -m venv .venv

# Windows:
.venv\Scripts\activate
# macOS/Linux:
source .venv/bin/activate

pip install -r requirements.txt
python -m alembic upgrade head
python -m app.seed_auth
uvicorn app.main:app --reload
```

API en `http://localhost:8000` — docs en `http://localhost:8000/docs`.

### 4. Frontend

```bash
cd frontend
npm install
npm run dev
```

App en `http://localhost:5173`.

---

## Variables de entorno

### Backend (`.env` en la raíz)

| Variable | Descripción |
|---|---|
| `DATABASE_URL` | Conexión a PostgreSQL |
| `SECRET_KEY` | Clave de firma JWT — valor largo y aleatorio |
| `ADMIN_INITIAL_PASSWORD` | Contraseña del admin inicial (solo usada por `seed_auth.py` la primera vez) |
| `CORS_ORIGINS` | Orígenes permitidos, separados por coma |

### Frontend (`frontend/.env`)

| Variable | Descripción |
|---|---|
| `VITE_API_URL` | URL base del backend |

---

## Módulos del sistema

- **Remisiones** — crear, editar, copiar, imprimir
- **Facturación** — facturar total/parcial, anular, facturación masiva por Excel
- **Terceros** — clientes, conductores, proveedores
- **Catálogos** — productos, formas de pago, tipos de servicio, unidades, prefijos
- **Ubicaciones** — departamentos y municipios (DANE Colombia)
- **Activos** — vehículos y camas bajas
- **Reportes** — exportación a Excel
- **Administración** — usuarios y roles con permisos granulares
