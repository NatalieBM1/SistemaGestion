# Configuración — variables de entorno

El backend lee su configuración de `.env` en la raíz del repo (ver
`backend/app/core/config.py`). Para empezar: `cp .env.example .env` y
reemplaza los valores de ejemplo. **Nunca versiones `.env`**; en Render las
variables se cargan en el panel del servicio (Environment).

Los ejemplos de esta tabla son ilustrativos, no credenciales reales.

## Backend (`.env` en la raíz)

| Variable | Obligatoria | Ejemplo | Para qué sirve |
|---|---|---|---|
| `DATABASE_URL` | Sí | `postgresql://remisiones:CAMBIAR_ESTA_CLAVE@localhost:5432/remisiones` | Conexión a PostgreSQL. |
| `SECRET_KEY` | Sí | `CAMBIAR_ESTA_CLAVE_POR_UNA_ALEATORIA_DE_48_CARACTERES` | Firma de los JWT y de los códigos de recuperación. Mínimo 32 caracteres aleatorios. Cambiarla cierra todas las sesiones. |
| `ADMIN_INITIAL_PASSWORD` | Sí | `CAMBIAR_ESTA_CLAVE` | Contraseña del administrador que crea `seed_auth.py` si no existe. Cambiarla desde la app al primer ingreso. |
| `APP_ENV` | No (por defecto `production`) | `development` | `development` muestra `/docs` y no envía HSTS. Cualquier otro valor se trata como producción. |
| `CORS_ORIGINS` | No (por defecto `http://localhost:5173,http://127.0.0.1:5173`) | `https://mi-frontend.onrender.com` | Orígenes del frontend permitidos, separados por coma. |
| `DB_POOL_SIZE` | No (3) | `3` | Conexiones fijas del pool. |
| `DB_MAX_OVERFLOW` | No (7) | `7` | Conexiones extra en picos. `workers × instancias × (pool + overflow)` no debe pasar de 25 en Render free. |
| `EMPRESA_NIT` | No (`900721501`) | `900000000` | NIT con el que se identifica a la propia empresa entre los terceros (datos del recibo). |
| `EMPRESA_RESOLUCION_HABILITACION` | No | `Res. Habilitación 000 de Enero 1/2000` | Texto de la resolución que sale en el recibo impreso. |
| `SMTP_HOST` | No* | `smtp.gmail.com` | Servidor de correo saliente. |
| `SMTP_PORT` | No (587) | `587` | Puerto SMTP (STARTTLS). |
| `SMTP_USER` | No* | `correo-del-sistema@ejemplo.com` | Usuario SMTP. |
| `SMTP_PASSWORD` | No* | `CAMBIAR_ESTA_CLAVE` | Contraseña SMTP. Con Gmail, una "contraseña de aplicación" (requiere verificación en dos pasos). |
| `SMTP_FROM_NAME` | No (`Transportes Guerreros`) | `Nombre de la empresa` | Nombre del remitente. |
| `SMTP_FROM_EMAIL` | No (usa `SMTP_USER`) | `correo-del-sistema@ejemplo.com` | Dirección del remitente. |
| `RESET_TOKEN_EXPIRE_MINUTES` | No (15) | `15` | Validez del código de recuperación de contraseña. |
| `RATE_LIMIT_ENABLED` | No (`true`) | `true` | Activa el límite de intentos en login y recuperación. |
| `RATE_LIMIT_STORAGE_URI` | No (`memory://`) | `memory://` | Dónde se cuentan los intentos. `memory://` sirve con un solo proceso; con varias instancias, un Redis (`redis://host:6379/1`, requiere el paquete `redis`). |

\* `SMTP_HOST`, `SMTP_USER` y `SMTP_PASSWORD` son opcionales para arrancar,
pero sin ellas "Olvidé mi contraseña" responde 503 (no disponible).

## Solo para `docker-compose.yml` (Postgres local)

| Variable | Obligatoria | Ejemplo | Para qué sirve |
|---|---|---|---|
| `DB_USER` | No | `remisiones` | Usuario que crea el contenedor de Postgres la primera vez. |
| `DB_PASSWORD` | **Sí** (para `docker compose`) | `CAMBIAR_ESTA_CLAVE` | Contraseña de ese usuario. Debe coincidir con la de `DATABASE_URL`. Sin ella `docker compose` se detiene con un mensaje (no hay contraseña por defecto). |
| `DB_NAME` | No | `remisiones` | Nombre de la base. |

## Frontend (`frontend/.env`)

| Variable | Obligatoria | Ejemplo | Para qué sirve |
|---|---|---|---|
| `VITE_API_URL` | No (`http://localhost:8000`) | `https://mi-api.onrender.com` | URL del backend. Se fija al compilar (`npm run build`). |

## Render

Las mismas variables del backend van en el servicio de la API (Environment).
`render.yaml` ya define `APP_ENV=production` y `CORS_ORIGINS`; `SECRET_KEY`
se genera ahí; `ADMIN_INITIAL_PASSWORD` y las `SMTP_*` se cargan a mano.
