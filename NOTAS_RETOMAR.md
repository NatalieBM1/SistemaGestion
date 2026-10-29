# Notas para retomar

## 2026-10-28 (tarde) — Identificación de usuarios + hallazgo ODS

Sin commits ni ramas. Sin modificar datos históricos (no se reasignó el
creador de ninguna remisión).

### 1) `usuarios.identificacion` (opcional)
- Modelo `Usuario.identificacion` (VARCHAR 30, NULL). Migración
  **`c41f7b2e9d10`** (idempotente; verificada desde vacía — 7
  migraciones —, re-aplicada con la columna existente, downgrade/upgrade
  y `alembic check` sin diferencias). Existentes quedan en NULL.
- Schemas admin: se recorta, vacío → NULL, solo `[0-9A-Za-z.-]`, máx. 30
  (422 si no). Se puede borrar enviando vacío. Editarla NO sube
  `token_version` (no cierra sesiones).
- Administración → Usuarios: campo "Identificación (cédula)" opcional en
  el formulario (crear/editar).
- Reportes: "ID del usuario" / "ID usuario" (creador) e "ID usuario
  factura" (quien facturó) usan `identificacion`; si no hay, la celda va
  **vacía** (antes salía el id interno, p. ej. "1"). Las 1.000
  históricas siguen con creador = Administrador del Sistema; si se le
  carga la cédula a ese usuario, saldrá en todas ellas.
- Pruebas: `tests/test_identificacion_usuario.py` (11: API en SQLite,
  reportes en el clon con rollback, y que el creador de las remisiones
  no cambia). pytest 134/134, tsc y build OK.
- ⚠️ **Base local real NO migrada** (sigue en `a3c9e1f04b72`): correr
  `alembic upgrade head` antes de reiniciar el backend local, si no el
  login falla (columna inexistente). Solo agrega la columna vacía.
- Docker Desktop estaba detenido; lo arranqué para las pruebas con
  Postgres (el contenedor `sistemagestion-db` volvió solo, datos
  intactos: 1.000 / 91 / 1.613).

### 2) ODS — hallazgo (no se cargó nada)
- Único origen: columna **`ODS`** de la hoja "Registros" de
  `Remisiones_v7_-Final_TGG.xlsm`. Los archivos de `formatos/` solo traen
  el encabezado "ODS" (sin datos). Los informes del "programa anterior"
  traen la misma columna con los mismos valores.
- Cobertura: **94 de 13.478 remisiones (0,70%)**; 95 de 17.615 filas.
  En las **1.000 importadas: 0 (0%)** — la última ODS real es del
  2025-05-14 y la ventana importada va del 2026-05-14 al 2026-08-25. El
  100% vacío del reporte es correcto, no un dato perdido.
- Valores: 3 códigos, por cliente:
  OS01 → JAC DE LAS VEREDAS BIRMANIA Y LA CONCEPCION (22, feb-2024) y
  JUNTA DE ACCION COMUNAL VEREDA BIRMANIA (5, feb-2024);
  OS02 → SOLARTE NACIONAL DE CONSTRUCCIONES SAS (49, jul–sep 2024);
  OS03 → JOINT SOLUCIONES INTEGRALES SAS (17, mar–may 2025).
  Más "15" en la fila de prueba G-PRUEBA (excluida siempre).
- Propuesta (pendiente de OK): no hace falta cargar nada para las 1.000
  actuales. Si se amplía la importación histórica: crear 3 órdenes de
  servicio y enlazar esas 94 remisiones. Bloqueos a resolver antes:
  (a) `ordenes_servicio.valor_tope` y `saldo_disponible` son obligatorios
  y el Excel no los trae — el cliente debe darlos (no se inventan) o
  hacerlos opcionales con migración; (b) OS01 aparece con dos clientes
  (probablemente la misma JAC registrada dos veces como tercero) y
  `numero` es único con un solo `cliente_id` → confirmar si es el mismo
  cliente. Hasta entonces, el importador sigue guardando la ODS como
  nota "[ODS histórico: …]" en Observaciones.

### Pasos para Render
- **Migración nueva `c41f7b2e9d10`**: se aplica sola al arrancar
  (`alembic upgrade head` del Dockerfile). Sin variables nuevas; mismo
  comando de arranque.
- `.gitignore`: `backups/diferencias_valor_total_remisiones.csv`.

---

## 2026-10-28 (sesión "Orden, filas por página y reportes — verificación y ajustes")

Bloques A, B y C + cierre, sin commits ni ramas. Detalle en
`INFORME_CAMBIOS_CLIENTE.md` ("Sesión 5"). Gran parte ya existía de la
sesión del 25-10; aquí se verificó y se corrigió lo que faltaba.

- **A — orden**: `components/ui/ThOrdenable.tsx` (extraído de `Table`),
  `ordenarEnCliente` en `hooks/useOrdenamiento.ts` (Intl.Collator es-CO
  numeric; vacíos al final). Backend: `core/ordenamiento.py`
  (`clausulas_orden` con desempate por id + NULLS LAST;
  `texto_como_numero`). Agregado: Ubicaciones (ahora tablas, `Table
  compacta`), detalle de factura (+ modal), Roles; columnas calculadas
  ordenables por subconsulta (valor total de remisiones =
  `remision_service.subconsulta_valor_total`, remisiones/valor de
  facturas, tipos/municipio de terceros, empresa de activos, roles de
  usuarios). Número de factura por partes numéricas. Departamentos no
  tenía ORDER BY. No ordenables a propósito: casillas, Acciones,
  "Pendiente" del modal (se calcula por fila con otra consulta).
- **B — filas por página**: ya estaba en todas; faltaban estados en
  Ubicaciones (skeleton), Roles y detalle de factura (error/vacío).
- **C — reportes**: encabezados ya eran exactos. Corregido: IDs de
  usuario como texto, horas `hh:mm`, dinero entero sin `.0`. Importador
  (`importar_registros.py`): alias "Hola salida" (antes se perdía la hora
  de salida al reimportar), estados con guion bajo, identificación sin
  `int()` (ceros a la izquierda), `columnas_no_reconocidas`. La "ida y
  vuelta" anterior no comparaba nada (omitía las 1.000 por existentes);
  la nueva borra y reimporta dentro de una transacción revertida y
  compara campo por campo: 1000/1000 remisiones, 1225/1225 líneas.
- **Corrección importante**: la columna "Valor total" del listado de
  Remisiones SÍ existe; desde la unificación de la 6.1 muestra el valor
  sin ×viajes en las 282 multiviaje (antes inflado).
- Verificación Playwright (frontend en :5180 + backend en :8010 sobre el
  clon, nunca la base real ni tus servidores en :8000/:5173): Bloque A
  62/62, Bloque B 99/99. Capturas `capturas/bloqueA_*`, `bloqueB_*`.
  Scripts en el scratchpad de la sesión (no versionados).
- Cierre: pytest 123/123, tsc y build OK, `alembic upgrade head` desde
  vacía (6 migraciones) + `alembic check` sin diferencias. Base real:
  27 tablas con datos idénticos al backup previo; `usuarios` idéntica en
  sus columnas originales. Clon `remisiones_prueba` rehecho limpio.

### Pendiente (para decidir)
- (Resuelto en la tarde: campo `identificacion`, sin reasignar
  históricas; ODS analizada. Ver sección de arriba.)
- "Usuario" / "ID del usuario" en reportes: las 1.000 históricas dicen
  "Administrador del Sistema" / "1"; el nombre real está solo en
  Observaciones y no hay cédula de usuarios. Propuesta: campo de
  identificación en usuarios + reasignar el creador real de las
  históricas a partir de esa nota (requiere OK, toca datos).
- ODS 100% vacía (sin órdenes de servicio cargadas): definir de qué
  columna del Excel original sale.
- Reiniciar tus servidores locales (:8000) para tomar el código nuevo.
- Pasos para Render: **sin cambios** respecto de la sesión anterior (no
  hay migraciones ni variables nuevas en esta sesión).

---

## 2026-10-27 (sesión "Seguridad del login" — Partes 1 a 6)

Sin commits ni ramas. Detalle por parte en `INFORME_CAMBIOS_CLIENTE.md`
("Sesión 4"). Backups previos en `backups/` (pg_dump -Fc, restaurar con
`pg_restore`): `remisiones_antes_parte1_*.dump` y
`remisiones_antes_parte2_*.dump` y `remisiones_antes_migracion_local_*.dump`.
Base real: datos idénticos al backup de antes de empezar (1.000
remisiones / 91 facturas / 1.613 terceros). **Ya migrada** a
`a3c9e1f04b72` (pedido explícito, con backup previo; solo agrega las 2
columnas en 0).

### Seguimiento (mismo día, tras aprobar las Partes 1–6)
- **P6.1 unificada** con la regla del cliente: valor total = suma de
  (material + flete + camabaja), **SIN** × numero_viajes. Única
  definición en `remision_service.calcular_valor_total`;
  `facturacion_service.calcular_valor_total_remision` la llama;
  `serializar_remisiones` replica la regla en SQL (prueba de que coinciden).
  Verificado sobre el clon, antes vs después: facturación 0 cambios
  (valor total, facturado, saldo, estado) en las 1.000; ninguna de las
  718 facturadas/parciales cambió; reportes Excel general (1.227 filas)
  y facturadas (719) idénticos celda por celda. Solo cambia
  `valor_total` de la API de remisiones en las 282 multiviaje (ahora =
  facturación). **Corrección (2026-10-28):** sí se muestra, en la columna
  "Valor total" del listado de Remisiones — antes inflado ×viajes, ahora
  el valor correcto. Los reportes conservan su
  propio `_totales_remision` (desglose material/flete/camabaja, misma
  regla).
- **Redis**: contenedor eliminado (`docker compose up -d
  --remove-orphans`; compose recreó el contenedor de Postgres, datos
  intactos en el volumen).
- **Prueba manual** por HTTP con uvicorn real (flags de Render) contra
  el clon: login (bien/mal), /me, cabeceras, /docs en desarrollo,
  forgot-password idéntico exista o no, código incorrecto/correcto,
  token viejo → 401, contraseña nueva, importación de Excel de NIT
  (1 fila OK + 1 error por fila), CSV renombrado → 422, `.csv` → 415.
  Todo OK. **El envío real de correo falló**: `SMTP_USER` /
  `SMTP_FROM_EMAIL` del `.env` siguen con el valor de ejemplo
  (`tucorreo@gmail.com`) → `SMTPServerDisconnected`. Falta poner una
  cuenta real (Gmail + contraseña de aplicación) para probar la
  recepción. El clon se rehízo limpio después de la prueba.
- `.env` local lleva `APP_ENV=development` (si falta, la app se
  comporta como producción: sin /docs y con HSTS).

### Pruebas
- `cd backend && .venv/Scripts/python -m pytest` — 81 pruebas.
- Las que necesitan Postgres con datos usan `TEST_DATABASE_URL`, un
  **clon** de la base (`remisiones_prueba`). Sin la variable se saltan;
  si apunta a la base real, fallan a propósito. Recrear el clon:
  `docker exec sistemagestion-db psql -U remisiones -d postgres -c "DROP DATABASE IF EXISTS remisiones_prueba" -c "CREATE DATABASE remisiones_prueba"`,
  luego `pg_restore -d remisiones_prueba --no-owner < backups/<último>.dump`
  (vía `docker exec -i`) y `DATABASE_URL=<url del clon> alembic upgrade head`.
- Las de API usan SQLite en memoria (`conftest.client_api`); ninguna
  manda correos reales (fixture `correos`).

### Resumen por parte
- **P2** `token_version` en el JWT (`"ver"`, sin claim = 0) validado en
  `deps.get_current_user` y `/refresh`; sube con reset, cambio de
  contraseña por admin, desactivación y `setup_usuarios.py`. Código de
  recuperación = HMAC-SHA256 (`security.hash_codigo_recuperacion`) +
  `hmac.compare_digest`, 15 min, un uso, tope 5 fallos
  (`MAX_INTENTOS_CODIGO`). `forgot-password` idéntico exista o no el
  correo; correo en `BackgroundTasks`. Migración `a3c9e1f04b72`.
- **P3** `core/http_seguridad.py` (cabeceras + corte por Content-Length
  de multipart, por DENTRO de CORS para que el 413 sea legible),
  `core/uploads.py` (.xlsx, 10 MB por bloques, firma PK + zip íntegro +
  `xl/workbook.xml`). `APP_ENV` controla /docs y HSTS. CORS recortado.
  Cabeceras del frontend en `render.yaml` (`headers`).
- **P4** `remision_service.serializar_remisiones`: listado en 3 queries
  (antes 118 con 20 filas / 571 con 100), respuesta idéntica (376.650
  campos). Pool 3+7 con `pre_ping` (`DB_POOL_SIZE`, `DB_MAX_OVERFLOW`):
  1 worker × 1 instancia × 10 = 10 ≤ 25.
- **P5** Redis fuera (config, .env, README, docker-compose; contenedor
  ya eliminado). `ADMIN_PERMISO` solo en `admin_service.py`. Login sin
  el `/me` extra.
- **P6.1** Unificado (ver "Seguimiento" arriba). La lista de las 282
  que diferían antes queda en `backups/diferencias_valor_total_remisiones.csv`.
- **P6.2** Criterio único: UTC naive (`core/fechas.ahora_utc`), igual a
  las columnas `timestamp without time zone`. Ningún dato cambiado.

### Pasos para Render (Partes 1–6)
1. **Comando de arranque** (ya está en `backend/Dockerfile`):
   `alembic upgrade head && python -m app.seed_auth && uvicorn app.main:app --host 0.0.0.0 --port 8000 --proxy-headers --forwarded-allow-ips='*'`
   Si el panel tiene un "Docker Command" propio, debe ser este.
2. **Migraciones**: se aplican solas al arrancar. Entran
   `a3c9e1f04b72` (reset_intentos, token_version) y, si aún no se
   aplicaron, `213a424fce90` (prefijos, sesión 2) y `89a56447c6d0`
   (reset_token). Idempotentes; usuarios existentes quedan en 0 y no
   pierden la sesión.
3. **Variables de entorno de la API**:
   - `APP_ENV=production` — ya en `render.yaml`; si el servicio no se
     maneja con el blueprint, agregarla a mano (sin ella también queda
     en producción, que es el valor por defecto).
   - `SMTP_HOST`, `SMTP_USER`, `SMTP_PASSWORD` (+ `SMTP_FROM_*`): sin
     ellas "olvidé mi contraseña" responde 503 a todos.
   - Opcionales: `DB_POOL_SIZE` (3), `DB_MAX_OVERFLOW` (7),
     `RATE_LIMIT_ENABLED` (true), `RATE_LIMIT_STORAGE_URI` (memory://).
   - `REDIS_URL`: ya no se usa; si está definida, se puede borrar.
4. **Frontend (sitio estático)**: cabeceras en `render.yaml`
   (`headers`). Si el sitio no se creó desde el blueprint: Settings →
   Headers, path `/*`, con los mismos 6 valores.
5. **Después de desplegar**: comprobar que `/docs` da 404, que el login
   funciona y que las cabeceras salen (`curl -I`).

### Pendiente
- Poner credenciales SMTP reales (local y Render) y probar la recepción
  del código de recuperación.
- Verificar en Render qué llega en `X-Forwarded-For` (riesgo de IP
  falseable con `--forwarded-allow-ips='*'`, ver P1 abajo).
- Para la siguiente fase (NO hecho, a propósito):
  - Tokens en `localStorage` → cookies httpOnly + CSP.
  - Lista negra de tokens con Redis (hoy `token_version` cubre los
    casos de reset/cambio/desactivación, no el logout individual).
  - Índices trigram (`pg_trgm`) para las búsquedas `ILIKE '%…%'`.
  - Auditoría en catálogos y al cambiar la contraseña de un usuario
    desde Administración.

### Parte 1 (rate limiting) — detalle

- slowapi en `app/core/rate_limit.py`. Login 20/min por IP y 5/min por correo (ajustado
  tras aprobar la Parte 1), pedir código 3/h,
  usar código 10/15 min (`verify-reset-code` se eliminó en la Parte 2).
  Doble clave: IP (decorador) + correo normalizado
  (`limitar_por_correo`, usa `limiter.limiter.hit` directo porque el
  correo viene en el cuerpo y el key_func de slowapi solo ve el request).
- IP real: uvicorn con `--proxy-headers --forwarded-allow-ips='*'`
  (Dockerfile). Ojo: con `'*'` uvicorn toma la **primera** IP de
  X-Forwarded-For; si el proxy de Render *agrega* en vez de reemplazar,
  un cliente podría falsear su IP. Por eso importa el límite por correo
  (no depende de la IP). Si se quiere blindar más, verificar en Render
  qué llega en X-Forwarded-For y tomar la IP desde la derecha.
- Contadores en memoria del proceso: correcto con 1 proceso uvicorn
  (como hoy). Con varios workers/instancias → `RATE_LIMIT_STORAGE_URI`
  a Redis + paquete `redis`.
- Riesgo conocido: el límite por correo permite que un tercero bloquee
  temporalmente (≤1 min en login, ≤1 h en pedir código) a un usuario
  concreto. Es el costo de impedir la rotación de IPs.
- Una oficina con muchos usuarios detrás de una misma IP pública
  comparte el cupo de 20 logins/min por IP (`LIMITE_LOGIN_IP`); el de
  correo (`LIMITE_LOGIN_CORREO`) sigue en 5/min.
- Pruebas: `tests/conftest.py` crea `client_api` con SQLite en memoria
  (solo tablas de usuarios/roles/permisos) y envuelve la app en el
  `ProxyHeadersMiddleware` de uvicorn para simular X-Forwarded-For.
  `httpx` agregado a requirements (lo necesita TestClient).

Los pasos para Render de toda la sesión están arriba, en "Pasos para
Render (Partes 1–6)".

---

## 2026-10-25 (sesión "Columnas ordenables, filas por página, reportes exactos")

Trabajo hecho en 3 bloques + cierre, sin commits ni ramas. Detalle
completo en `INFORME_CAMBIOS_CLIENTE.md` (sección "Sesión 3").

- **Bloque A — columnas ordenables**: hook `useOrdenamiento` +
  encabezados clicables (`<button>` dentro de `<th>`, flecha azul,
  `aria-sort`, accesible por teclado) centralizados en `Table.tsx`.
  Aplicado a Remisiones, los 7 catálogos (`CatalogoCRUD.tsx`),
  Facturación, Terceros, Activos, Administración → Usuarios y
  Administración → Roles (esta última ordena en cliente porque carga
  todos los roles de una vez, no está paginada). En Ubicaciones no se
  agregaron encabezados ordenables porque esa pantalla no es una tabla
  de columnas sino dos listas de nombres (maestro-detalle
  departamento/municipio) — si se quiere ahí también, hay que
  rediseñar esa vista primero.
  Orden en backend con lista blanca de columnas por router
  (`COLUMNAS_ORDENABLES_*` en cada archivo de `routers/`, o automático
  para los catálogos genéricos vía `simple_crud.py`). Columnas
  calculadas (ej. "Remisiones" y "Valor total facturado" en Facturación,
  que se arman en Python por factura) **no son ordenables** porque
  exigirían traer todas las filas antes de paginar — se dejó así a
  propósito, no es un olvido.
  Número de remisión ordena por prefijo + consecutivo numérico (no como
  texto), reutilizando la lógica ya existente de Remisiones.
- **Bloque B — filas por página**: mismo selector de Remisiones
  (`SelectorFilasPorPagina`, 10/25/50/100) reutilizado en Catálogos,
  Facturación, Terceros, Activos y Administración → Usuarios, con el
  conteo "1–25 de 1.000". En Ubicaciones se agregó paginación real a
  los dos paneles (departamentos y municipios), que antes no la tenían.
  Se recuerda la elección por lista en `localStorage`
  (`filas-por-pagina:<lista>`), con fallo silencioso si no hay
  almacenamiento. Estado de error-con-"Reintentar" agregado a todas las
  listas tocadas (antes solo lo tenía Remisiones).
- **Bloque C — reportes exactos**: se revirtió "Hora salida" a **"Hola
  salida"** (el typo del Excel original del cliente) — en una sesión
  anterior yo lo había "corregido", esta instrucción lo deja explícito:
  el typo se conserva. Prueba pytest que compara encabezados carácter
  por carácter contra la hoja de referencia (falla si cambia cualquier
  nombre u orden) y verifica tipos de dato por columna (texto/fecha con
  formato yyyy-mm-dd/número). Prueba de ida y vuelta: reporte generado →
  reimportado con el importador existente en una base clonada
  (`roundtrip_test`, nunca la real) → **1000/1000 remisiones
  coincidieron**, un solo error preexistente y ya conocido
  (GTS-6467, línea sin producto). Los dos archivos de ejemplo
  (`ejemplo_generado_reporte_general.xlsx` / `_facturadas.xlsx`) se
  regeneraron con el encabezado correcto.
  Columnas que hoy salen vacías por falta de dato, y de dónde vendrían:
  - `ID del conductor`, `Valor de comisión`, `Valor de costo`, `Unidad
    de medida`, `Id Producto`: **casi nunca están vacías en realidad**
    (99.9% con dato) — la suposición de que faltan seguido no se
    confirmó con los datos reales; solo falta en la fila con error ya
    conocida.
  - `ODS` (orden de servicio): 100% vacía — el `orden_servicio_id`
    quedó NULL en toda la importación histórica (ambigüedad ya
    documentada en una sesión anterior).
  - `Proyecto`/`Tramo`: vacías en las 1000 remisiones actuales porque
    existen proyectos en el catálogo, pero están asociados a remisiones
    más antiguas que no entran en esta ventana — no es un dato que
    falte en el sistema, es que no aplica a esta muestra.
  - `Kilometros`, `Cama Baja`, `Hora llegada`, `Hola salida`, `Remision
    AGRESUR`: vacías de forma parcial, reflejando que el dato de origen
    ya venía así (no es un hueco del sistema).
  No se inventó ningún valor para rellenar estas columnas.

### Pendiente

- Confirmar con el cliente si quiere columnas ordenables también en
  Ubicaciones (requeriría rediseñar esa pantalla como tabla).
- Contraseña real del usuario Administrador no coincide con la que se
  tenía registrada — no se pudo verificar visualmente con Playwright
  las pantallas de Administración → Usuarios y → Roles (sí se
  verificaron con la cuenta Operador en el resto de listas). Avísame la
  contraseña correcta si quieres esas capturas.
- Todo lo pendiente de sesiones anteriores (migración de prefijos en
  Render, ambigüedad del ODS, mayúsculas en terceros, etc.) sigue
  igual, sin tocar.

---

## 2026-10-24 (sesión "Facturación múltiple, prefijos, números sin ceros, interfaz")

Trabajo hecho en 5 bloques + cierre, sin commits ni ramas. Detalle
completo en `INFORME_CAMBIOS_CLIENTE.md` (sección "Sesión 2").

- **Bloque 1**: rediseño del listado de Remisiones para facturar varias
  a la vez — casilla general en el encabezado, fila seleccionada en azul
  suave, fila ya facturada atenuada, solo mismo cliente (con aviso),
  barra flotante inferior azul oscuro, Escape limpia selección, columna
  Acciones recortada a Editar/Copiar/Imprimir/"Agregar a factura".
- **Bloque 2**: `POST/DELETE /api/facturas/{numero_factura}/remisiones`
  nuevos — agregar o quitar remisiones de una factura ya existente, todo
  en una transacción. `DetalleFactura.tsx` reescrito con encabezado
  resumen y el modal de selección. Probado de punta a punta en vivo.
- **Bloque 3**: permiso nuevo `prefijos.administrar` (solo
  Administrador). GTM es ahora el único prefijo manual — **MAN pasó de
  manual a automático** (no tenía ninguna remisión asociada, cambio
  seguro). Migración Alembic idempotente
  `213a424fce90_solo_gtm_es_prefijo_manual.py` — **falta correrla en
  Render** en el próximo despliegue.
- **Bloque 4**: los números de remisión se muestran sin ceros a la
  izquierda en toda la interfaz (`formatNumeroRemision`), pero se
  guardan igual en la base. Las búsquedas aceptan con y sin ceros. El
  recibo impreso, las facturas y los reportes Excel **no se tocaron**
  (formato ya aprobado antes).
- **Bloque 5**: Reportes rediseñado como tarjetas con filtro de estado
  nuevo y chips de columnas. Selector de filas por página y estado de
  error-con-reintentar agregados al listado de Remisiones. Formularios y
  modales ya cumplían casi todo lo pedido de una sesión anterior
  (`Modal.tsx` ya tenía foco/Escape/Tab-trap/móvil bien hechos).

### Pendiente

- Columnas ordenables en las tablas (no implementado, requiere soporte
  de orden en el backend).
- Extender el selector de filas por página a Facturas/Terceros/Catálogos/
  Activos (solo se hizo en Remisiones como referencia).
- Correr la migración de prefijos en Render.
- Todo lo pendiente de confirmación de la sesión anterior (municipio mal
  nombrado, mayúsculas masivas en terceros, extender permisos "solo
  crear" a otros módulos) sigue igual, sin tocar.

---

> **Nota:** `NOTAS_RETOMAR.md`, `NOTAS_IMPORTACION.md` y
> `AUDITORIA_PRE_ENTREGA.md` ya no estaban en el repo al empezar esta
> sesión (no aparecen en ningún commit — el repo tiene 5 commits, el más
> reciente del 2026-10-13, probablemente de una limpieza antes de
> publicar/desplegar a Render). Este archivo se recrea desde cero.

## 2026-10-20 (sesión de "Cambios solicitados por el cliente")

Trabajo hecho en 7 bloques, en orden, sin commits ni ramas. Detalle
completo, supuestos, pendientes de confirmación y respaldos en
`INFORME_CAMBIOS_CLIENTE.md`.

### Resumen por bloque

1. **Reportes exactos** (`reportes_service.py` reescrito): el reporte
   general y el de facturadas ahora salen con los encabezados y el orden
   exactos que pidió el cliente, verificados contra sus archivos de
   referencia con un test nuevo (`backend/tests/test_reportes_formato.py`
   — primer test del proyecto). Pendiente de confirmar: "Hola salida" →
   "Hora salida" (asumido como error de digitación) y el mapeo de varias
   columnas "ID".
2. **Catálogo DANE completo**: 34 departamentos y 1.123 municipios
   cargados (antes 5/72), 100% aditivo. Selectores de municipio ahora
   muestran "MUNICIPIO - DEPARTAMENTO" con búsqueda por ambos. Hallazgo
   sin corregir: el municipio código `52696` está mal nombrado como
   "NARIÑO" (debería ser "SANTA BÁRBARA").
3. **Facturación**: el formato de número de factura ahora acepta
   "F-1234" y "F-7-468"/"F-7-2564" (antes solo el primero). Nueva
   función de facturar varias remisiones a la vez (casillas + modal, todo
   en una transacción, mismo cliente obligatorio).
4. **GTM manual**: el prefijo GTM ahora pide el consecutivo a mano (igual
   que el prefijo "MAN" ya existente), confirmado contigo. De paso se
   corrigió un bug real: "copiar remisión" no revisaba si el prefijo era
   manual.
5. **Catálogos — permisos separados**: el rol Operador ahora solo puede
   crear en los 7 catálogos (prefijos, formas de pago, tipos de servicio,
   productos, unidades de medida, prefijos de factura, tipos de tercero),
   no editar ni borrar. Proyectos no se tocó (fuera de alcance).
6. **Terceros**: nombres en mayúsculas automáticas (backend + mientras se
   escribe), solo identificación y nombre obligatorios (migración Alembic
   aditiva aplicada), resto de validaciones del formulario sin asterisco.
7. **Cierre**: tsc, build, pytest, alembic upgrade desde vacío — todo
   limpio. Base real sin alterar en conteos (1.000 remisiones, 1.613
   terceros, 91 facturas, 24 proyectos, igual que al empezar).

### Pendiente de tu confirmación (nada de esto se aplicó)

- Corregir el municipio `52696` (Bloque 2).
- Aplicar alguna propuesta de municipio para los terceros sin municipio
  (Bloque 2, CSV `terceros_sin_municipio_propuesta_v2.csv`).
- Extender "solo crear" a Proyectos/Terceros/Ubicaciones/Activos
  (Bloque 5).
- Aplicar el cambio a mayúsculas a los 7 terceros existentes afectados
  (Bloque 6, script `mayuscular_nombres_terceros.py --aplicar`).
- El favicon/ícono quedó sin tocar ("eso ya no va", según me dijiste).

### Capturas

En `capturas/` (1492×702 @1.25 y 390px donde aplica): selector de
municipio con formato nuevo, selección múltiple y modal de facturación
(válido y con error), formulario de GTM manual, catálogo visto por el
Operador (sin editar/borrar), formulario de tercero con mayúsculas en
vivo.
