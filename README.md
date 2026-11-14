# Sistema de Remisiones — Transportes Guerreros & Guerreros S.A.S.

Sistema de gestión de remisiones y facturación para empresas de transporte de carga.  
Backend en **FastAPI + PostgreSQL**, frontend en **React + Vite + TypeScript**.

---

## Requisitos

| Herramienta | Versión mínima |
|---|---|
| Python | 3.12 |
| Node.js | 20 LTS |
| Docker Desktop | cualquier versión reciente |
| Docker Compose | v2 |

---

## Correr en local

### 1. Variables de entorno

```bash
cp .env.example .env
# Edita .env con tus valores reales (ver descripción en docs/configuracion.md)
```

### 2. Levantar la base de datos y Redis

```bash
docker compose up -d
```

### 3. Backend

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate        # Windows
# source .venv/bin/activate   # Linux / macOS
pip install -r requirements.txt
alembic upgrade head
python -m app.seed_auth       # crea roles, permisos y usuario admin inicial
uvicorn app.main:app --reload --port 8000
```

### 4. Frontend

```bash
cd frontend
npm install
npm run dev
```

Abre `http://localhost:5173`.

---

## Variables de entorno

Todas las variables que lee la aplicación están documentadas en `.env.example`  
con descripción y valor de ejemplo. Detalle ampliado en `docs/configuracion.md`.

| Variable | Obligatoria | Descripción corta |
|---|---|---|
| `DATABASE_URL` | ✅ | URL de conexión a PostgreSQL |
| `SECRET_KEY` | ✅ | Clave HS256 para firmar JWT (≥ 32 chars aleatorios) |
| `ADMIN_INITIAL_PASSWORD` | ✅ | Contraseña del administrador inicial |
| `APP_ENV` | — | `development` (default) o `production` |
| `CORS_ORIGINS` | — | Orígenes del frontend, separados por coma |
| `SMTP_HOST` / `SMTP_USER` / `SMTP_PASSWORD` | — | Correo saliente para recuperación de contraseña |
| `EMPRESA_NIT` | — | NIT propio de la empresa |

---

## Correr las pruebas

```bash
cd backend
pytest tests/ -v
```

---

## Despliegue

El repositorio incluye `render.yaml` con la definición de los tres servicios  
(API, frontend estático, base de datos). Ver instrucciones completas en  
`docs/configuracion.md`.

---

## Stack

| Capa | Tecnología |
|---|---|
| Backend | FastAPI, SQLModel, Alembic, PostgreSQL |
| Frontend | React 19, Vite, TypeScript, Zustand, TanStack Query |
| Autenticación | JWT (python-jose), bcrypt |
| Despliegue | Render (render.yaml incluido) |

---

© 2026 Natalie Benavides M. Todos los derechos reservados.
