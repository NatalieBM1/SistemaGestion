# Cambios solicitados por el cliente — informe de entrega

Se trabaja bloque por bloque, en el orden pedido. Sin commits ni ramas.
Me detengo a confirmar contigo antes de cualquier cosa que pueda alterar
datos ya existentes.

---

## Bloque 1 — Reportes con las columnas exactas

### Archivos de referencia
Movidos a `backend/app/data_import/formatos/`:
- `reporte-remisiones-general-programa_nuevo.xlsx`
- `reporte-remisiones-facturadas-programa_nuevo.xlsx`
- `Listado-censal-consejos-organizaciones-base-formas-y-expr.-organizativas.-Anexo-3.-Vr-02-25-02-2022.xlsx`

### Archivos tocados
- `backend/app/services/reportes_service.py` — reescrito por completo.
- `backend/tests/test_reportes_formato.py` — nuevo (primer test del
  proyecto).
- `backend/app/data_import/formatos/ejemplo_generado_reporte_general.xlsx`
  y `..._facturadas.xlsx` — ejemplos generados con los datos reales ya
  cargados (no hay una base de "datos de prueba" separada; si prefieres
  un ejemplo con datos sintéticos en vez de los históricos reales, lo
  regenero).

No se tocó `backend/app/routers/reportes.py` (mismos endpoints, mismos
parámetros) ni ninguna pantalla de la app — el cambio es solo en el
contenido del archivo exportado.

### "Hola salida" → "Hora salida"
Lo cambié a "Hora salida" en ambos reportes, como pediste, asumiendo que
es un error de digitación del cliente. **Pendiente de que lo confirmes
con él** — si de verdad quiere la columna literal "Hola salida", avísame
y la dejo tal cual.

### Mapeo de columnas "ID" — supuestos usados

Los que tú ya diste están aplicados tal cual. Donde no diste una regla
explícita, usé estos supuestos (pendientes de tu confirmación):

| Columna | De dónde sale |
|---|---|
| ODS | `numero` de la orden de servicio enlazada (`remision.orden_servicio_id`), vacía si no hay ninguna enlazada. **Importante:** en las remisiones históricas importadas, `orden_servicio_id` quedó `NULL` a propósito (no había forma de reconstruir el control de saldo real — ver `NOTAS_IMPORTACION.md`, ambigüedad 3); el texto "OS01" etc. de esas remisiones quedó solo en `Observaciones`, no en esta columna. Para remisiones nuevas creadas con una orden de servicio real sí va a traer el número. |
| ID factura | `id` interno de la factura (no el número de factura) |
| ID usuario / ID usuario factura | `id` interno del usuario |
| Id Producto | `id` del producto en el catálogo (no el id de la línea `remision_productos`) |
| **Subtotal** (reporte facturadas) | Valor flete + Valor Camabaja de la remisión (el costo de transporte, sin el material) |
| **Total** (reporte facturadas) | Subtotal + Valor Material = el mismo total que usa el reporte general |

### Reglas de formato aplicadas
- Fechas: celdas de fecha real de Excel, formato `yyyy-mm-dd`.
- `ID del cliente` / `ID cliente` / `ID del conductor`: forzadas a texto
  (para no perder ceros a la izquierda ni que Excel las convierta a
  número).
- El resto de columnas numéricas: números reales, no texto.
- General: una fila por línea de producto; una remisión sin ninguna
  línea sale en una sola fila con esas columnas vacías.
- Facturadas: una fila por remisión+factura activa (una remisión con
  varias facturas parciales sale en varias filas).

### Pruebas hechas
- `pytest backend/tests/test_reportes_formato.py` — 3 pruebas, todas
  pasan:
  1. Encabezados del reporte general = columna E exacta del archivo de
     referencia (con el cambio Hola→Hora salida).
  2. Encabezados del reporte facturadas = columna E exacta del archivo
     de referencia.
  3. El reporte general trae exactamente `líneas de producto +
     remisiones sin ninguna línea` filas (1.226 contra los 1.000
     remisiones reales hoy en la base, de las cuales 1 no tiene
     productos).
- Probado también contra el servidor real corriendo (`GET
  /api/reportes/remisiones-general` con token de Operador): mismos
  encabezados y conteo de filas que el test.
- No hubo que crear ni borrar ningún dato — es un reporte de solo
  lectura.

---

## Bloque 2 — Catálogo DANE completo

### 1. Carga del catálogo completo — aplicada

- Script nuevo: `backend/app/scripts/cargar_dane_completo.py`. Idempotente
  por `codigo_dane` (upsert): si el código ya existe, **nunca** se toca
  (ni nombre ni id), solo se insertan los que faltan.
- Respaldo automático antes de escribir:
  `backend/app/data_import/backups/backup_20261019_234014_pre_dane_completo.dump`.
- Vista previa corrida primero, resultado 100% aditivo (0 modificaciones a
  lo existente) — apliqué directamente sin pausar, porque no hay forma de
  que esto altere un dato ya cargado.
- **Resultado:** 34 departamentos (5→34, +29) y 1.123 municipios
  (72→1.123, +1.051). Verificado que los 72 municipios y 5 departamentos
  originales conservan el mismo `id` y `nombre` de antes.

**Hallazgo a revisar (no lo corregí, solo lo reporto):** el municipio con
`codigo_dane = 52696`, que hoy en la base se llama **"NARIÑO"**, según el
catálogo oficial del DANE en realidad corresponde a **"SANTA BÁRBARA"**
(departamento Nariño). Parece un error de origen en la carga anterior
(probablemente alguien confundió el nombre del departamento con el del
municipio). No lo toqué — dime si quieres que lo corrija (implicaría
renombrar ese municipio; cualquier tercero o remisión que ya lo tenga
asignado seguiría apuntando al mismo `id`, solo cambiaría el nombre que
se ve en pantalla).

Otras 9 diferencias de nombre encontradas (todas mucho más leves — el
nombre guardado es una variante corta o con otro orden de palabras, ej.
"EL TABLÓN" vs "EL TABLÓN DE GÓMEZ", "TUMACO" vs "SAN ANDRÉS DE TUMACO"):
listadas completas en la salida del script, no creo que necesiten acción,
pero quedan ahí si quieres revisarlas.

### 2. Selectores: "MUNICIPIO - DEPARTAMENTO", con búsqueda

- `MunicipioRead` (backend) ahora trae `departamento_nombre` y
  `presentacion` ("MUNICIPIO - DEPARTAMENTO").
- `GET /api/ubicaciones/municipios?q=...` ahora busca por nombre de
  municipio **o** de departamento (antes solo por municipio) — probado:
  `q=Cauca` devuelve municipios de "Cauca" y de "Valle del Cauca"
  (86 resultados).
- Frontend: los 3 selectores de municipio (origen y destino en el
  formulario de remisión, y municipio en el formulario de terceros) ahora
  muestran `presentacion` en vez de solo el nombre.
- Archivos tocados: `backend/app/schemas/ubicacion.py`,
  `backend/app/routers/ubicaciones.py`,
  `frontend/src/pages/Remisiones/RemisionForm.tsx`,
  `frontend/src/pages/Terceros/ListadoTerceros.tsx`.

### 3. Origen/destino: no hace falta crear nada

Revisé cómo se relacionan Ubicaciones con los municipios: **no hay una
tabla "Ubicación" intermedia** — `Remision.origen_municipio_id` y
`destino_municipio_id` apuntan directo a `municipios.id`. Con el catálogo
completo ya cargado (punto 1), **los 1.123 municipios ya se pueden
elegir directamente como origen o destino, sin ningún paso adicional.**
No hay que crear registros masivos ni nada parecido — ya lo probé:

- Busqué municipios de Boyacá (antes no existían en la base) y confirmé
  que ya aparecen en el buscador.
- Creé una remisión de prueba real con origen "Almeida - Boyacá" y
  destino "Aquitania - Boyacá" — se guardó sin problema. La borré
  después de la prueba.

### 4. Terceros sin municipio (620): revisión con el catálogo completo

Con el catálogo completo, volví a correr la comparación:

- **5 auto-asignables** (coincidencia exacta y sin ambigüedad entre el
  campo `direccion` completo y un municipio): PUERTO ASÍS, TUNJA, PUERTO
  SALGAR, OLAYA (Antioquia), BARRANQUILLA. Listados completos en
  `backend/app/data_import/terceros_sin_municipio_propuesta_v2.csv`.
- **25 con pista débil** (el nombre de un municipio aparece como palabra
  dentro de un texto de dirección más largo, incluidos los 5 casos que
  mencionaste: "BOGOTA DC", "YUMBO VALLE", etc.) — **ninguno aplicado
  todavía**, y con una advertencia real: uno de los 25
  (`AV BOYACA 55 80`, una dirección en Bogotá) coincidió con el
  municipio "Boyacá" solo porque "Avenida Boyacá" es un nombre de calle
  en Bogotá, no una referencia al municipio — es exactamente el tipo de
  falso positivo que esta regla puede producir, por eso ninguno de los
  25 se aplica solo, quedan para que los revises uno por uno.
- **590 siguen sin ninguna pista** (ni coincidencia exacta ni palabra
  reconocible en la dirección).

**No se modificó ningún tercero.** El CSV
`terceros_sin_municipio_propuesta_v2.csv` tiene las columnas
`id, nombre, NIT, direccion, municipio_propuesto, fuente_propuesta,
accion, municipio_final` — mismo patrón que el anterior, para que lo
llenes y yo aplique con `aplicar_revision_municipios.py` cuando
confirmes.

---

## Bloque 3 — Facturación

### 1. Formato del número de factura

- Patrón exacto usado: `^[A-Z]-\d+(-\d+)?$` — una letra mayúscula, guion,
  dígitos, y **opcionalmente** otro guion y más dígitos. Acepta tanto el
  histórico ("F-1234") como el real vigente ("F-7-468", "F-7-2564").
- Cambiado en el único lugar donde vivía la validación:
  `backend/app/services/facturacion_service.py` (todos los flujos —
  modal manual, masivo/eliminar/actualizar por Excel — pasan por esta
  misma función, no había validaciones duplicadas en otro lado).
- Mensaje de error y textos de ayuda actualizados en backend y frontend
  (`FacturacionPanel.tsx`, `CargasExcel.tsx`, `ListadoFacturas.tsx`).
- Probado en vivo: facturé una remisión real con "F-7-2564" (el caso
  exacto que mencionaste) — funcionó. Verifiqué que ninguna factura ya
  cargada en la base (91 reales) deja de cumplir el nuevo patrón.

### 2. Facturar varias remisiones a la vez

- **Backend:** dos endpoints nuevos en `facturas.py` /
  `facturacion_service.py`:
  - `POST /api/facturas/facturar-multiples/resumen` — vista previa, no
    escribe nada: dice si se puede facturar, el cliente, cantidad y
    valor total, o el motivo exacto por remisión si no se puede.
  - `POST /api/facturas/facturar-multiples` — aplica, reutilizando
    `facturar_remision(..., tipo="TOTAL")` (la misma función del
    endpoint individual) en una sola transacción: si cualquier remisión
    falla, no se escribe ninguna.
  - Reglas aplicadas tal cual las pediste: solo remisiones NO_FACTURADA
    o FACTURADA_PARCIAL: incluidas; mismo cliente obligatorio (si no,
    dice cuáles sobran); tipo TOTAL por el saldo pendiente de cada una;
    todo o nada.
- **Frontend** (`ListadoRemisiones.tsx`): casilla por fila (deshabilitada
  si la remisión ya está FACTURADA), "Seleccionar todas en esta página",
  contador de seleccionadas, botón "Facturar seleccionadas" que abre un
  modal con el resumen (cliente, cantidad, valor total) y los campos de
  número y fecha de factura, o la lista de motivos si no se puede
  facturar la selección.
- **La selección se conserve al paginar:** sí, es viable y quedó así —
  se guarda en un `Set` de ids en el estado de la página, no se resetea
  al cambiar de página, solo cuando se limpia a mano o se aplica la
  factura.

### Pruebas hechas
- **API, con datos reales de prueba (creados y borrados al terminar):**
  resumen con 2 remisiones del mismo cliente → total y saldo correctos;
  aplicar → 1 factura con 2 `remision_facturacion` (ambas TOTAL, mismo
  `factura_id`), ambas remisiones pasaron a FACTURADA; intentar con una
  remisión ya facturada → rechazado con el motivo exacto, nada escrito;
  intentar con remisiones de clientes distintos → rechazado señalando
  cuáles sobran, nada escrito (confirmé con `COUNT(*)` en la base antes
  y después).
- **En el navegador real** (Playwright, ya que no tenía esa herramienta
  antes pero la instalé para esta tarea — `frontend/node_modules`, no
  versionado): login como Operador, seleccioné 3 remisiones de clientes
  distintos y confirmé que el modal muestra el error correcto; luego
  seleccioné 2 remisiones del mismo cliente y confirmé que el modal
  muestra el resumen correcto con los campos listos para llenar. No
  envié el formulario (no hizo falta crear datos de prueba vía UI,
  ya estaba probado por API).
- Capturas en `capturas/`:
  - `bloque2_municipio_1492x702.png` / `..._390px.png` — selector de
    origen mostrando "ALMEIDA - BOYACA" etc. (Bloque 2).
  - `bloque3_seleccion_1492x702.png` / `..._390px.png` — casillas +
    barra de selección en el listado.
  - `bloque3_modal_error_1492x702.png` / `..._390px.png` — modal con
    remisiones de clientes distintos (estado de error).
  - `bloque3_modal_valido_1492x702.png` — modal con una selección
    válida (resumen + campos).

---

## Bloque 4 — Remisión: consecutivo manual para GTM

### Lo que pregunté y tu respuesta

GTM tenía `es_manual = false`. El mecanismo de "prefijo manual" **ya
existía en el código** (se usa hoy para el prefijo "MAN": el usuario
escribe el `numero_remision` completo como texto libre, sin forzar
formato ni agregarle el prefijo). Te pregunté si para GTM querías ese
mismo comportamiento simple, o uno más estricto (validar entero
positivo y componer "GTM-000123"). **Elegiste: igual que MAN, texto
libre.** Así quedó.

### Cambio de dato aplicado

- Respaldo previo:
  `backend/app/data_import/backups/backup_20261020_063624_pre_gtm_manual.dump`.
- `UPDATE prefijos SET es_manual = true WHERE codigo = 'GTM';` —
  `consecutivo_actual` de GTM no se tocó (sigue en 76257, el máximo
  histórico real).

### Bug encontrado y corregido de paso

Al revisar el flujo completo encontré que **"copiar remisión" nunca
revisaba `es_manual`** — para cualquier prefijo manual (MAN, y ahora
GTM), copiar intentaba autogenerar un número con
`generar_numero_remision_automatico`, lo cual está mal para un prefijo
manual. Lo corregí: ahora usa la misma función `resolver_numero_remision`
que ya usa la creación, así que copiar una remisión de un prefijo manual
**pide el nuevo número** (frontend: campo nuevo en el modal "Duplicar
remisión", solo visible cuando el prefijo es manual) y lo valida igual
que al crear. Para prefijos automáticos el comportamiento no cambió.

### Archivos tocados
`backend/app/schemas/remision.py`, `backend/app/routers/remisiones.py`,
`frontend/src/api/remisiones.ts`,
`frontend/src/pages/Remisiones/ListadoRemisiones.tsx`. El formulario de
Nueva/Editar remisión y la validación de backend para crear ya existían
tal cual se pedían — no hizo falta tocarlos.

### Pruebas hechas (API, datos borrados al final)
- Crear remisión GTM sin `numero_remision` → 422, mensaje claro.
- Crear remisión GTM con `numero_remision="GTM-900001"` → creada,
  `consecutivo_actual` de GTM sin cambios.
- Repetir el mismo número → 409 (duplicado).
- Crear con prefijo automático (GTS) → sigue funcionando igual que
  antes, numeración automática intacta.
- Copiar la remisión GTM sin número nuevo → 422; con número nuevo →
  copiada correctamente.
- Captura `capturas/bloque4_gtm_manual_1492x702.png`: formulario con
  "GTM (manual)" seleccionado y el campo "Número de remisión (manual)"
  habilitado.

---

## Bloque 5 — Catálogos: el operador solo crea

### 1. Backend: permisos separados

- Permisos nuevos (`backend/app/seed_auth.py`): `catalogos.crear`,
  `catalogos.editar`, `catalogos.eliminar` — separados del ya existente
  `catalogos.escribir`.
- `backend/app/core/simple_crud.py` (el generador de routers CRUD
  compartido por todos los catálogos) ahora acepta
  `create_permission`/`update_permission`/`delete_permission` además de
  `write_permission`; si no se dan los específicos, sigue usando
  `write_permission` para las tres operaciones (así los catálogos que no
  pediste restringir no cambian de comportamiento).
- Aplicado a los 7 catálogos exactos que pediste:
  prefijos, formas de pago, tipos de servicio, productos, unidades de
  medida, prefijos de factura, tipos de tercero
  (`backend/app/routers/catalogos.py`).
- **Proyectos NO se tocó** — sigue con `write_permission="catalogos.escribir"`
  tal cual estaba (ver punto 3 abajo).
- Respaldo antes de aplicar los nuevos permisos a la base:
  `backend/app/data_import/backups/backup_20261020_074828_pre_permisos_catalogos.dump`.
- Probado en vivo: Operador crea una forma de pago (201), intenta
  editarla (403) y borrarla (403); Administrador sí puede editar (200) y
  borrar (204) ese mismo registro.

### 2. Frontend: botones ocultos, no solo deshabilitados

`components/CatalogoCRUD.tsx` (usado por los 7 catálogos): los botones
de **Editar** y **Eliminar** ahora no se renderizan en absoluto si el
usuario no tiene `catalogos.editar`/`catalogos.eliminar` — antes se
mostraban deshabilitados. El botón **Nuevo** sigue siempre visible,
deshabilitado solo para Solo Consulta (que tampoco tiene
`catalogos.crear`).

### 3. Matriz final de permisos por rol

| Permiso | Administrador | Operador | Solo Consulta |
|---|---|---|---|
| catalogos.leer | ✅ | ✅ | ✅ |
| catalogos.crear | ✅ | ✅ | ❌ |
| catalogos.editar | ✅ | ❌ | ❌ |
| catalogos.eliminar | ✅ | ❌ | ❌ |
| catalogos.escribir (**Proyectos**, sin cambios) | ✅ | ✅ | ❌ |
| terceros / ubicaciones / activos / remisiones / facturas .escribir | ✅ | ✅ | ❌ |
| usuarios.administrar | ✅ | ❌ | ❌ |

**Otros módulos donde el Operador hoy puede crear, editar y borrar sin
distinción** (mismo patrón que tenían los 7 catálogos antes de este
cambio) — **no los toqué**, solo te los señalo por si quieres el mismo
tratamiento:
- **Proyectos** (justo el que explícitamente no tocar).
- **Terceros** (`terceros.escribir`).
- **Ubicaciones** — departamentos y municipios (`ubicaciones.escribir`).
- **Activos** — vehículos y camas bajas (`activos.escribir`).

Dime si alguno de estos también debería pasar a "solo crear" para el
Operador.

Captura `capturas/bloque5_catalogo_operador_1492x702.png` /
`..._390px.png`: pantalla de catálogos (Formas de pago) con el Operador
logueado — "Nuevo Forma de pago" visible, sin ningún botón de editar o
borrar en las filas.

---

## Bloque 6 — Terceros

### 1. Mayúsculas en el nombre

- **Al crear/editar (backend):** `terceros.py` convierte `nombre` a
  mayúsculas antes de guardar (`str.upper()`, conserva tildes —
  probado: "luis fernández pérez" → "LUIS FERNÁNDEZ PÉREZ").
- **Mientras se escribe (frontend):** el campo "Nombre" del formulario
  se convierte a mayúsculas en vivo, letra por letra, sin perder la
  posición del cursor.
- **No se tocó ningún tercero existente.** Script nuevo
  `backend/app/scripts/mayuscular_nombres_terceros.py` (vista previa por
  defecto, `--aplicar` hace respaldo y recién ahí escribe). Corrí la
  vista previa contra la base real:
  **1.613 terceros totales, solo 7 cambiarían** (todos de prueba/demo,
  ej. "Constructora Andina S.A.S.", "Tercero Prueba Doble Tipo" — los
  terceros reales del histórico ya venían en mayúsculas). **No apliqué
  nada** — avísame si quieres que corra el `--aplicar` sobre esos 7.

### 2. Campos opcionales

- Revisé la base: `direccion`, `municipio_id`, `email`, `telefono`,
  `regimen` eran `NOT NULL`. Solo `identificacion` y `nombre` siguen
  obligatorios.
- **Migración Alembic nueva (aditiva):**
  `549c342624e6_terceros_columnas_opcionales.py` — le quita `NOT NULL` a
  esas 5 columnas, no borra ni transforma ningún dato existente. Corrida
  contra la base real (con respaldo previo:
  `backend/app/data_import/backups/backup_20261020_075738_pre_terceros_nullable.dump`).
  El `downgrade()` vuelve a exigir `NOT NULL` (y fallaría a propósito si
  para entonces ya hay filas con `NULL`, en vez de inventar un valor).
- **Código que asumía estos campos, revisado y ajustado:**
  - `backend/app/routers/empresa.py` (usa un Tercero para los datos de
    la empresa en el recibo impreso): ya tenía resguardos para
    `municipio_id`/`telefono`/`email`; le agregué el mismo resguardo a
    `direccion` y `regimen`.
  - `backend/app/schemas/empresa.py` / `frontend/src/api/empresa.ts`:
    `direccion` y `responsabilidad_iva` pasan a opcionales.
  - `frontend/src/pages/Remisiones/ReciboRemision.tsx`: esas dos líneas
    del recibo ahora solo se imprimen si hay dato.
  - `backend/app/schemas/tercero.py` y `app/models/tercero.py`: los 5
    campos pasan a opcionales en los schemas de creación/edición/lectura
    y en el modelo.
  - `backend/app/routers/terceros.py`: el `session.get(Municipio, ...)`
    ya no se llama con `None` (rompía antes de probar el flujo).
  - Facturación y reportes: revisé y **no** usan estos 5 campos del
    tercero en ningún lado (solo `nombre`/`identificacion`), no hizo
    falta tocarlos.
- Probado: creé un tercero real con **solo** identificación y nombre —
  se guardó con los otros 5 campos en `NULL`, apareció bien en el
  listado, y el endpoint de empresa (que sí depende de un Tercero
  completo) se probó aparte y sigue funcionando normal.

### 3. Validación del formulario

Solo "Identificación" y "Nombre" muestran asterisco rojo y error de
"obligatorio"; el resto (Dirección, Municipio, Email, Teléfono, Régimen)
ya no tiene ninguna validación de obligatorio ni asterisco.

De paso encontré que el asterisco nunca se había mostrado para ningún
campo (el componente `Input` necesita la prop `required` además de la
regla de validación de `react-hook-form`, y no se estaba pasando) — lo
agregué para Identificación y Nombre, que es donde correspondía.

Captura `capturas/bloque6_tercero_form_1492x702.png` / `..._390px.png`:
formulario "Nuevo tercero" con el nombre convirtiéndose a mayúsculas
mientras se escribe, asterisco solo en Identificación y Nombre.

---

## Bloque 7 — Cierre

### Verificación final

- `tsc -b --noEmit`: sin errores.
- `npm run build`: compila bien (mismo aviso ya conocido del chunk de
  ~611 KB, sin cambios de fondo).
- `pytest`: 3/3 pasan (`test_reportes_formato.py`, bloque 1).
- `alembic upgrade head` contra una base vacía nueva: corre limpio de
  principio a fin, las 3 migraciones en orden (incluida la nueva de
  terceros).
- `ruff check`: sin errores nuevos en nada de lo tocado hoy (el único
  aviso de import sin usar es de un script de la carga histórica, de
  antes de esta sesión).
- Cada bloque se probó en la app real (servidor en el puerto 8000,
  frontend en 5173) con datos de prueba creados y borrados al terminar
  cada prueba — el conteo final de la base real quedó igual que al
  empezar: 1.000 remisiones, 1.613 terceros, 91 facturas, 24 proyectos.

### Nota: el repo ya tiene commits

Al revisar `git status` para este cierre encontré que el repo **ya no
está vacío de commits** — tiene 5, el más reciente del 13 de octubre
(antes de esta sesión), incluyendo uno de despliegue a Render. No los
hice yo (seguí "sin commits" en todo momento, como pediste); deben ser
de una revisión/publicación que hiciste tú después de la auditoría
pre-entrega. Lo señalo porque cambia el contexto: los cambios de hoy
(36 archivos entre modificados y nuevos) quedan como cambios sin
commitear sobre esa base, listos para que tú los revises y decidas cómo
commitear/publicar.

### Supuestos hechos (para tu confirmación)

1. **Bloque 1:** "Hola salida" → "Hora salida" (error de digitación).
   Mapeo de columnas ID (ODS, ID factura, Usuario Factura, etc.) y la
   definición de Subtotal/Total del reporte facturadas — ver detalle en
   el Bloque 1.
2. **Bloque 4:** GTM manual con comportamiento "texto libre" (igual que
   el prefijo "MAN" existente), confirmado por ti en el momento.

### Pendiente de tu confirmación (nada de esto se aplicó)

- Bloque 2: corregir el municipio mal nombrado (código `52696`,
  "NARIÑO" → debería ser "SANTA BÁRBARA"); aplicar alguno de los 5+25
  casos de terceros sin municipio con pista (débil o exacta).
- Bloque 5: extender "solo crear" a Proyectos, Terceros, Ubicaciones o
  Activos.
- Bloque 6: aplicar el cambio a mayúsculas a los 7 terceros existentes
  que quedarían afectados.
- Confirmar si quieres que corrija el favicon/ícono más adelante (lo
  diste de baja esta sesión — "eso ya no va").

### Migraciones y cambios de datos aplicados hoy

| Qué | Respaldo previo |
|---|---|
| Catálogo DANE completo (34 deptos, 1.123 municipios) | `backup_20261019_234014_pre_dane_completo.dump` |
| GTM marcado como prefijo manual | `backup_20261020_063624_pre_gtm_manual.dump` |
| Permisos nuevos de catálogos (crear/editar/eliminar) | `backup_20261020_074828_pre_permisos_catalogos.dump` |
| Migración Alembic: terceros, 5 columnas opcionales | `backup_20261020_075738_pre_terceros_nullable.dump` |

Todos en `backend/app/data_import/backups/`.

---

# Sesión 2 (2026-10-24) — Facturación múltiple, prefijos, números sin ceros, interfaz

Nuevo pedido, trabajado por bloques sin pausar entre ellos (como pediste).
Sin commits ni ramas. Verificado con Playwright a 1492×702 @1.25 y 390px
(capturas en `capturas/sesion2_*`).

## Bloque 1 — Facturar varias remisiones desde el listado

Ya existía una primera versión de esta función (sesión anterior); se
rediseñó para cumplir el detalle que pediste:

- **Columna de casillas con casilla general en el encabezado** (no en una
  barra aparte): `Table.tsx` ahora acepta un `header` tipo nodo, no solo
  texto, para poder poner el checkbox ahí.
- **Fila seleccionada con fondo azul suave** y **fila ya facturada
  atenuada** (opacidad reducida, casilla deshabilitada):
  `Table.module.css` (`.rowSelected`, `.rowDisabled`) +
  `getRowClassName` nuevo en `Table.tsx`.
- **Solo mismo cliente**: al marcar una remisión de otro cliente, se
  muestra un aviso (toast) con los nombres de los clientes en conflicto y
  **no se marca** — no permite llegar a una selección mixta como antes
  (antes solo se validaba al momento de facturar).
- **Barra flotante inferior, azul oscuro, centrada**: reemplaza la barra
  gris de arriba. Usa `var(--accent-deep)` (ya existía en `tokens.css`).
- **Escape limpia la selección** en toda la pantalla (listener global).
- **Columna Acciones**: Editar, Copiar, Imprimir, y "Agregar a factura"
  **solo si la remisión no está FACTURADA en su totalidad** — quité
  "Agregar producto" (no estaba en tu lista; sigue disponible dentro del
  formulario de edición, pestaña Productos).
- **Selección persistente al paginar/filtrar**: ya era así (un `Set` en
  el estado de la página, no se reinicia con los filtros); se limpia al
  facturar o con "Limpiar".
- "Agregar a factura" individual abre un modal chico para escribir el
  número de factura y usa el mismo endpoint del Bloque 2.

Archivos: `frontend/src/pages/Remisiones/ListadoRemisiones.tsx` (reescrito
en gran parte), `ListadoRemisiones.module.css`, `components/ui/Table.tsx`,
`Table.module.css`.

## Bloque 2 — Agregar remisiones a una factura existente

- **Backend**: `POST /api/facturas/{numero_factura}/remisiones` (uso
  `numero_factura` en vez de un id numérico — es la clave natural que ya
  usa toda la app para identificar facturas, p.ej.
  `/api/facturas/{numero_factura}/remisiones` para listarlas) con
  `{remision_ids: [...]}`: una sola transacción, valida mismo cliente de
  la factura, que no estén ya FACTURADA ni ya en esa factura, reutiliza
  `facturar_remision(tipo="TOTAL")` internamente (mismo código que ya
  estaba probado). `DELETE .../remisiones/{remision_id}` ("Quitar")
  reutiliza `anular_facturacion` — revierte estado y totales en la misma
  transacción. Permisos: `facturas.escribir`, igual que facturar hoy.
  Auditoría: ya quedaba registrada automáticamente (ambas funciones
  reutilizadas ya llaman a `registrar_auditoria`).
- **Frontend** (`DetalleFactura.tsx`, reescrito): encabezado resumen
  (cliente, fecha, # remisiones, valor facturado), tabla con acción
  "Quitar" (con confirmación), botón "Agregar remisiones" que abre el
  modal: buscador (número o placa), filtros Desde/Hasta, tabla con
  casillas (selección + casilla general) de remisiones sin facturar o
  parcialmente facturadas del mismo cliente, columna "Pendiente"
  (calculada por remisión, reutilizando `getResumenFacturacion` que ya
  existía), pie con "N seleccionada(s)" y botón "Agregar N
  remisión(es)".

Archivos: `backend/app/services/facturacion_service.py`,
`app/routers/facturas.py`, `app/schemas/facturacion.py` (+
`cliente_id`/`cliente_nombre` agregados a `RemisionFacturacionRead` para
poder mostrar el cliente en el encabezado sin otra llamada),
`frontend/src/api/facturas.ts`,
`frontend/src/pages/Facturas/DetalleFactura.tsx` (reescrito).

**Probado en vivo, de punta a punta** (captura
`capturas/sesion2_b2_modal_agregar_1492x702.png`): agregar una remisión a
una factura existente → el encabezado y la tabla se actualizan al
instante (2 remisiones, $160.000) → quitarla → vuelve a 1 remisión,
$80.000, la fila queda "Anulada" atenuada.

## Bloque 3 — Prefijos

- **Permiso nuevo y más restrictivo**: `prefijos.administrar`, solo
  Administrador (separado de `catalogos.crear/editar/eliminar`, que sí
  tiene Operador para los otros 6 catálogos). Probado: Operador → 403 al
  crear un prefijo; Administrador → 201.
- **Frontend**: el catálogo de Prefijos usa esos permisos específicos
  (`config/catalogos.ts` ahora admite un override `permisos` por
  catálogo) — Operador ve "Nuevo Prefijo" deshabilitado y ninguna fila
  con editar/borrar (captura
  `capturas/sesion2_b3_prefijos_operador_1492x702.png`).
- **Antes de cambiar datos, revisé qué prefijos eran manuales hoy**:
  **GTM y MAN** tenían `es_manual = true`; los demás ya estaban en
  `false`. Como pediste que GTM sea el único manual, la migración
  **también cambió MAN a `false`** (antes permitía número de remisión
  libre tipo "remisión de papel"; confirmé que **no tiene ninguna
  remisión asociada** — 0 filas —, así que el cambio no rompe nada
  existente).
- **Migración Alembic idempotente**:
  `213a424fce90_solo_gtm_es_prefijo_manual.py` — pone `es_manual=true`
  solo en GTM y `false` en todos los demás; se puede correr varias veces
  sin efecto adicional. Ya corrida en la base real (respaldo previo:
  `backup_20261024_194926_pre_solo_gtm_manual.dump`). **Esta migración
  tiene que correr también en Render** cuando despliegues — es la mismas
  migraciones de Alembic que ya corren ahí (`alembic upgrade head`), no
  necesita nada especial aparte de eso.

## Bloque 4 — Número de remisión sin ceros a la izquierda

- **Utilidad nueva** `frontend/src/lib/formatNumeroRemision.ts`: quita
  los ceros a la izquierda del consecutivo (`GTS-006525` → `GTS-6525`);
  si el número no sigue el patrón PREFIJO-DÍGITOS (texto libre de un
  prefijo manual), lo deja tal cual. Usada en todas las pantallas de uso
  diario: listado y modales de Remisiones, formulario de Remisión,
  detalle de Factura. **No se tocó** lo que se guarda en la base.
- **Buscadores y filtros**: backend (`routers/remisiones.py`) ahora
  genera, además del texto buscado, la variante con ceros (relleno a 6
  dígitos, el mismo ancho que usa la numeración automática) y sin ellos,
  y busca con las tres. Probado con un número real: `6520`, `GTS-6520` y
  `GTS-006520` encuentran la misma remisión (la real, guardada como
  `GTS-6520`, sin ceros — el histórico importado nunca los tuvo; **las
  dos direcciones del ajuste eran necesarias**: también probé al revés,
  con una remisión nueva guardada **con** ceros por la numeración
  automática, buscada **sin** ceros, y funcionó igual).
- **Antes de tocar el recibo impreso, las facturas y los reportes
  Excel**: los revisé y **no los toqué** — siguen con el formato
  original (con ceros) porque:
  - El recibo impreso y la hoja "Imprimir" son el documento que ya
    aprobaste pixel a pixel contra el Excel del cliente en una sesión
    anterior.
  - El formato de número de **factura** ("F-7-468") es un dato distinto
    al número de **remisión** — no tiene ceros que quitar, no aplica
    este bloque.
  - Los reportes Excel (Bloque 1 de la sesión anterior) ya salen con las
    columnas exactas que pidió el cliente; cambiarles el formato del
    número de remisión sin que lo pidiera habría sido modificar un
    entregable ya aprobado por tu cuenta.

Archivos: `backend/app/routers/remisiones.py` (búsqueda),
`frontend/src/lib/formatNumeroRemision.ts` (nuevo),
`ListadoRemisiones.tsx`, `RemisionForm.tsx`, `ProductosModal.tsx`,
`DetalleFactura.tsx`.

## Bloque 5 — Mejoras de interfaz

- **Reportes**: cada uno es ahora una tarjeta con título, descripción,
  chip "N columnas", filtros (fechas, cliente, proyecto, **estado de
  facturación** — nuevo filtro agregado en backend y frontend), chips
  con las columnas exactas que trae el archivo, botón "Limpiar" y
  "Descargar Excel" con estado de carga. Las columnas en sí **no
  cambiaron** (siguen siendo las del Bloque 1 de la sesión anterior).
  Archivos: `reportes_service.py` / `routers/reportes.py` (filtro
  `estado_facturacion` nuevo), `pages/Reportes/Reportes.tsx` (reescrito),
  `Reportes.module.css` (nuevo).
- **Tablas y listas**: encabezado fijo al hacer scroll vertical (nuevo,
  `Table.module.css`), resaltado de fila al pasar el mouse (ya existía),
  alineación derecha de valores (ya existía), estados de carga
  (skeleton, ya existía). **Agregué** en el listado de Remisiones:
  selector de filas por página (10/20/50/100) y un estado de error
  separado del de "sin resultados", con botón "Reintentar" — antes un
  error de red se veía igual que "no hay resultados", lo cual era
  confuso. **No alcancé a implementar columnas ordenables** (requiere
  que el backend acepte un parámetro de orden y tocar cada listado) **ni
  extender el selector de filas por página a las demás listas**
  (Facturas, Terceros, Catálogos, Activos) — lo dejo señalado como
  pendiente, priorizé terminar bien lo demás con el tiempo que quedaba.
- **Formularios y modales**: revisé `Modal.tsx` — **ya cumplía casi todo
  esto de una sesión anterior**: foco inicial en el primer campo,
  Escape cierra, atrapa el Tab dentro del modal, se adapta a móvil sin
  desbordar (ya tenía `max-width: 100%` a 768px). Los botones con
  `loading`/`disabled` mientras envían y los errores bajo el campo ya
  eran el patrón estándar en todo el proyecto (`Button`, `Input`,
  `Select`). Las confirmaciones antes de acciones destructivas (borrar
  en catálogos, ahora también "Quitar" de una factura) ya usan un modal
  de confirmación. No tuve que tocar nada aquí — ya estaba bien hecho.
- **Facturación**: encabezado resumen y tabla con "Quitar" — ver
  Bloque 2.

## Cierre

- `tsc -b --noEmit`: sin errores. `npm run build`: compila (mismo aviso
  de chunk de 618 KB, sin cambios de fondo). `ruff check` (solo los
  archivos tocados hoy, filtrando ruido ya conocido): sin errores
  nuevos. `pytest`: 3/3 pasan. `alembic upgrade head` desde una base
  vacía nueva: corre las 4 migraciones en orden, incluida la nueva de
  prefijos.
- **Probado el flujo completo en la app real** (capturas en
  `capturas/sesion2_*`): seleccionar varias remisiones del mismo cliente
  → barra flotante → facturar (ya probado por API en la sesión anterior,
  reutiliza el mismo endpoint sin cambios); agregar remisiones a una
  factura existente → quitar (probado de punta a punta en vivo, con
  capturas antes/después); prefijos con usuario no Administrador →
  confirmado 403 por API y botones ocultos en pantalla; búsquedas con y
  sin ceros → confirmado con una remisión real en ambas direcciones.
  Todos los datos de prueba creados se borraron al terminar — la base
  real quedó igual que al empezar (1.000 remisiones, 91 facturas, 1.613
  terceros).
- `NOTAS_RETOMAR.md` actualizado.

### Pendiente / para tu confirmación

- Columnas ordenables en las tablas, y extender el selector de filas por
  página a Facturas/Terceros/Catálogos/Activos — no alcanzó el tiempo,
  quedó señalado, no a medio hacer.
- Recuerda correr `alembic upgrade head` en Render para que la migración
  de prefijos (GTM único manual) llegue a producción.

---

# Sesión 3 (2026-10-25) — Columnas ordenables, filas por página, reportes exactos

Trabajado por bloques sin pausar entre ellos, sin commits ni ramas.
Verificado con Playwright a 1492×702 @1.25 y 390px (capturas en
`capturas/sesion3_*`).

## Bloque A — Columnas ordenables en todas las tablas

Componente reutilizable: hook `useOrdenamiento`
(`frontend/src/hooks/useOrdenamiento.ts`) + encabezados clicables
centralizados en `Table.tsx` — clic alterna ascendente → descendente →
sin orden, con flecha azul pequeña indicando el sentido, `aria-sort` en
el `<th>`, y accesible por teclado (son `<button>` normales, así que
Enter/Espacio ya funcionan sin código extra). La columna de casillas y
la de Acciones no son ordenables (no se les asignó `sortField`).

Aplicado a:

- **Remisiones**: ya existía; se mantiene. Número de remisión ordena
  por prefijo y consecutivo numérico real (`GTS-9` antes que
  `GTS-10`), no como texto.
- **Catálogos** (los 7: Prefijos, Formas de pago, Tipos de servicio,
  Productos, Unidades de medida, Prefijos de factura, Tipos de
  tercero): como todos comparten `CatalogoCRUD.tsx`, se hizo una sola
  vez y cubre los siete. El orden en backend es automático — el
  endpoint genérico (`simple_crud.py`) arma la lista blanca de columnas
  a partir de los campos del modelo, así que no hay que tocar cada
  catálogo por separado.
- **Facturación**: Número de factura y Fecha. "Remisiones" y "Valor
  total facturado" **no son ordenables** a propósito: esos dos valores
  se calculan en Python por cada factura (cuentan remisiones activas y
  suman lo facturado), no son columnas de la base de datos — ordenar
  por ellos exigiría traer todas las facturas a memoria antes de
  paginar, lo que rompe la paginación en servidor. Si en algún momento
  se necesita ordenar por esas columnas, hay que decidir si vale la
  pena perder la paginación eficiente.
- **Terceros**: Identificación, Nombre, Teléfono. "Tipos" y
  "Municipio" tampoco son ordenables por el mismo motivo (se arman con
  una consulta aparte por cada tercero).
- **Activos**: Placa, Tipo, Clase, Estado (bloqueado/activo). "Empresa"
  no es ordenable (nombre se resuelve con una consulta aparte).
- **Administración → Usuarios**: Nombre, Email, Estado. "Roles" no es
  ordenable (lista calculada).
- **Administración → Roles**: esta pantalla carga **todos** los roles
  de una sola vez (no está paginada), así que el orden se hace en el
  navegador, no en el backend — ordena por Rol, Permisos asignados o
  Usuarios con este rol.
- **Ubicaciones**: **no se agregaron encabezados ordenables.** Esta
  pantalla no es una tabla de columnas — son dos listas de nombres
  (departamento / municipio) en formato maestro-detalle, con un botón
  de editar al lado de cada uno. No hay "columnas" que ordenar en el
  sentido que pide el Bloque A. Si quieres que también se pueda
  ordenar ahí, dime y lo vemos — implicaría rediseñar esa vista como
  tabla, o agregar un selector de orden aparte (A-Z / Z-A).

Orden en backend: cada router bespoke (Remisiones, Facturas, Terceros,
Activos, Administración) tiene su propia lista blanca de columnas
permitidas (`COLUMNAS_ORDENABLES_*`) — si se pide ordenar por algo que
no está en la lista, el backend responde 422 en vez de ejecutar
cualquier cosa con el nombre recibido (protege contra inyección SQL).
Los catálogos genéricos la arman solos a partir del modelo.

## Bloque B — Selector de filas por página en todas las listas

Mismo componente que ya existía en Remisiones
(`SelectorFilasPorPagina`: 10 · 25 · 50 · 100, con "1–25 de 1.000"),
reutilizado sin duplicar en Catálogos, Facturación, Terceros, Activos y
Administración → Usuarios. La elección se recuerda por lista en el
navegador (`localStorage`, con fallo silencioso si no hay
almacenamiento disponible — nunca rompe la pantalla).

**Ubicaciones** no tenía paginación visible en absoluto (cargaba 50
departamentos/municipios fijo, sin poder pedir más ni menos) — se le
agregó paginación real con el mismo selector a los dos paneles.

Estado de error con botón "Reintentar" agregado a todas las listas que
no lo tenían (antes solo Remisiones lo tenía) — si falla la carga, se
ve un mensaje claro en vez de una pantalla vacía o un error en consola.

## Bloque C — Reportes con columnas exactas (ajuste y verificación)

- **"Hola salida" (no "Hora salida")**: en una sesión anterior yo había
  corregido ese nombre pensando que era un error de dedo del cliente.
  Esta instrucción aclara que el typo es intencional y debe
  conservarse tal cual aparece en el Excel original. Se revirtió en
  `reportes_service.py` y en la prueba que compara encabezados. Los
  archivos de ejemplo (`app/data_import/formatos/ejemplo_generado_reporte_general.xlsx`
  y `_facturadas.xlsx`) se regeneraron con el nombre correcto.
- **Prueba de encabezados exacta**: `backend/tests/test_reportes_formato.py`
  compara, carácter por carácter, el encabezado generado contra la hoja
  de referencia del cliente — si cambia un nombre, el orden, o se
  agrega/quita una columna, la prueba falla y dice exactamente en qué
  columna está la diferencia.
- **Prueba de tipos de dato**: verifica que las columnas de texto (ID
  cliente, ID conductor) sean texto real (no se conviertan a número),
  que las de fecha tengan formato `yyyy-mm-dd` real en la celda (no
  solo texto parecido a fecha), y que las de dinero sean números (sin
  `$` ni separador de miles).
- **Prueba de ida y vuelta** (la más importante, pedida explícitamente):
  se generó el reporte general contra la base real (solo lectura), se
  clonó la base real a una base de prueba descartable
  (`roundtrip_test`, nunca se tocó la real), y se reimportó el reporte
  generado con el importador histórico que ya existe
  (`importar_registros.py`). Resultado: **1000 de 1000 remisiones
  coincidieron** (`omitidas_ya_existian: 1000`, cero creadas de más,
  cero columnas sin reconocer). Un solo error, ya conocido de antes:
  la remisión GTS-6467 tiene una línea sin producto en el dato
  original (no es un problema del formato del reporte). La base de
  prueba se borró al terminar.
- **Qué columnas salen vacías hoy, y de dónde vendría el dato**
  (sin inventar nada):

  | Columna | % vacía (de 1000) | De dónde vendría |
  |---|---|---|
  | ID del conductor, Valor de comisión, Valor de costo, Unidad de medida, Id Producto | ~0.1% (solo la fila con error conocido) | **Ya casi nunca están vacías** — si pensabas que faltaban seguido, los datos reales no lo confirman. |
  | ODS (orden de servicio) | 100% | El campo `orden_servicio_id` quedó sin asignar en toda la importación histórica (ambigüedad ya reportada en una sesión anterior: no quedó claro qué columna del Excel original mapea a esto). |
  | Proyecto / Tramo | 100% en esta muestra de 1000 | Sí existen proyectos cargados en el catálogo, pero están asociados a remisiones más antiguas que no entran en esta ventana de 1000 — no falta el dato en el sistema, es que no aplica a esta muestra concreta. |
  | Kilometros, Cama Baja, Hora llegada, Hola salida, Remision AGRESUR | Parcial (varía por fila) | El dato de origen (Excel del cliente) ya venía así de incompleto — no es un hueco introducido por el sistema. |

## Cierre de la sesión

- `tsc -b --noEmit`: sin errores.
- `npm run build`: build de producción exitoso.
- `pytest` (suite completa del backend): 5 de 5 pruebas pasaron.
- `alembic upgrade head` desde una base vacía creada de cero: las 4
  migraciones corrieron sin errores (se usó una base descartable,
  `alembic_scratch_test`, borrada al terminar).
- Base de datos real verificada intacta al final: 1.000 remisiones, 91
  facturas, 1.613 terceros — igual que al empezar.
- Verificación visual con Playwright (cuenta Operador) en Remisiones,
  Catálogos (pestaña "Formas de pago"), Facturación, Terceros, Activos
  y Ubicaciones, a 1492×702 @1.25 y 390px — encabezados ordenables con
  flecha visible, selector de filas por página con el conteo, todo
  responsive sin desbordes horizontales.
- **Pendiente de verificar visualmente**: Administración → Usuarios y
  → Roles. La contraseña del usuario Administrador que me diste no
  coincidió con la que tiene la base real (401 al iniciar sesión) — no
  quise resetear la contraseña de un usuario real sin que me lo
  pidieras explícitamente. Esas dos pantallas sí tienen el código
  aplicado (se ve en el informe arriba) y pasan `tsc`, solo falta la
  captura de pantalla. Dime la contraseña correcta y la hago.
- `NOTAS_RETOMAR.md` actualizado.

### Pendiente / para tu confirmación

- ¿Quieres columnas ordenables también en Ubicaciones? Esa pantalla no
  es una tabla hoy — habría que rediseñarla o agregar un selector de
  orden aparte.
- Confirmar la contraseña real del usuario Administrador para terminar
  la verificación visual de Admin → Usuarios/Roles.
- Todo lo pendiente de sesiones anteriores (migración de prefijos en
  Render, ambigüedad del ODS, etc.) sigue igual, sin tocar.

---

# Sesión 4 (2026-10-27) — Seguridad del inicio de sesión

## Parte 1 — Límite de intentos (rate limiting)

### Qué cambia para el usuario
Nada en el uso normal. Si alguien (o un programa) intenta adivinar una
contraseña o un código de recuperación, después de unos pocos intentos
la app responde **"Demasiados intentos. Por seguridad, espera N
minutos/segundos antes de volver a intentarlo."** y se muestra en el
mismo recuadro rojo de error de la pantalla.

| Acción | Límite |
|---|---|
| Iniciar sesión | 20 por minuto por IP, 5 por minuto por correo |
| Pedir código de recuperación | 3 por hora |
| Usar el código para cambiar la contraseña | 10 cada 15 minutos |

Cada límite se cuenta **dos veces**: por dirección IP y por correo
(en el login el cupo por IP es más amplio para que varios usuarios de
una misma oficina, con la misma IP pública, no se bloqueen entre sí). Así,
dos personas en IPs distintas no se bloquean entre sí, y un atacante no
puede esquivar el límite cambiando de IP sobre una misma cuenta.

### Archivos
- `backend/app/core/rate_limit.py` — nuevo: configuración de slowapi,
  límite por correo, respuesta 429 en español con `Retry-After`.
- `backend/app/routers/auth.py` — límites en `/login`,
  `/forgot-password`, `/verify-reset-code`, `/reset-password`.
- `backend/app/main.py` — registra el limitador y los manejadores de
  429; CORS expone `Retry-After` al frontend.
- `backend/app/core/config.py` — `RATE_LIMIT_ENABLED`,
  `RATE_LIMIT_STORAGE_URI` (opcionales).
- `backend/Dockerfile` — uvicorn arranca con `--proxy-headers
  --forwarded-allow-ips='*'` (necesario en Render, ver abajo).
- `backend/requirements.txt` — `slowapi`, `limits` (+ dependencias) y
  `httpx` (solo para pruebas).
- `frontend/src/api/errors.ts` — mensaje de respaldo para un 429 sin
  texto.
- `backend/tests/conftest.py`, `backend/tests/test_rate_limit.py` —
  nuevos.

### Pruebas
- 10 pruebas nuevas contra una base SQLite en memoria (nunca la real):
  misma IP se bloquea al pasar el límite; dos IPs distintas no se
  bloquean entre sí; mismo correo rotando IPs se bloquea; login normal
  sigue funcionando; `Retry-After` presente y coherente.
- Probado en vivo con uvicorn y los mismos flags de Render.
- `pytest` 15/15, `tsc` y `npm run build` OK. Datos reales intactos
  (1.000 remisiones / 91 facturas / 1.613 terceros); backup previo en
  `backups/`.

### Pasos para Render
1. **Comando de arranque** (ya está en el `Dockerfile`, no hay que
   cambiar nada en el panel si se usa Docker):
   `alembic upgrade head && python -m app.seed_auth && uvicorn app.main:app --host 0.0.0.0 --port 8000 --proxy-headers --forwarded-allow-ips='*'`
   Si en el panel de Render hay un "Docker Command" personalizado, debe
   incluir esos dos flags.
2. **Migraciones**: esta parte no agrega ninguna.
3. **Variables de entorno**: ninguna obligatoria. Opcionales:
   `RATE_LIMIT_ENABLED` (por defecto `true`) y `RATE_LIMIT_STORAGE_URI`
   (por defecto `memory://`; solo hace falta un Redis si algún día se
   corre con varias instancias). Los límites (login 20/min por IP y
   5/min por correo, etc.) están en el código, no hay que configurarlos.

---

## Parte 2 — Recuperación de contraseña y sesiones

### Qué cambia para el usuario
- Si alguien escribe mal el código de recuperación **5 veces**, ese
  código deja de servir (aunque después se escriba bien) y hay que pedir
  uno nuevo. Pedir un código nuevo reinicia el contador.
- El código vence a los 15 minutos y sirve **una sola vez**.
- "Olvidé mi contraseña" responde exactamente lo mismo exista o no el
  correo: nadie puede averiguar qué correos están registrados.
- Al **cambiar la contraseña** (por recuperación o desde
  Administración) o al **desactivar** un usuario, se cierran todas sus
  sesiones abiertas en cualquier equipo. Las sesiones de los demás no se
  ven afectadas, y nadie pierde la sesión por el despliegue.

### Detalle técnico
- Campos nuevos en `usuarios`: `reset_intentos` y `token_version`
  (migración `a3c9e1f04b72`, idempotente, valor 0 para los existentes).
  Verificada desde una base vacía, re-aplicada, con downgrade/upgrade y
  sobre un clon de la base real.
- El código se guarda como HMAC-SHA256 (no en claro) y se compara con
  `hmac.compare_digest` (tiempo constante).
- El correo del código se envía en segundo plano: un SMTP lento o caído
  ya no demora ni rompe la respuesta (queda en el log).
- **`verify-reset-code` eliminado**: busqué en el frontend y ninguna
  pantalla lo usaba (solo estaba declarado en `api/auth.ts`, también
  quitado). El flujo valida el código al cambiar la contraseña.

### Pruebas
12 pruebas nuevas (`tests/test_recuperacion_y_tokens.py`): token viejo
rechazado tras el reset (acceso y refresco), bloqueo al 5.º intento,
contador reiniciado con código nuevo y al usarlo bien, código de un solo
uso y vencido, respuesta idéntica con correo inexistente (también sin
SMTP), fallo de SMTP sin romper la respuesta, admin que cambia contraseña
o desactiva → tokens inválidos.

## Parte 3 — Cabeceras HTTP, documentación, CORS y archivos subidos

- **Cabeceras de seguridad en la API**: `X-Content-Type-Options`,
  `X-Frame-Options: DENY`, `Referrer-Policy`, `Permissions-Policy`,
  `X-XSS-Protection: 0` (la obsoleta, apagada) y HSTS solo en
  producción.
- **Cabeceras del frontend**: en `render.yaml`, sección `headers` del
  sitio estático (Render no lee archivos `_headers`). Si el sitio no se
  creó desde el blueprint, cargarlas en Settings → Headers.
- **/docs, /redoc y /openapi.json**: ocultos en producción, visibles en
  desarrollo. Lo controla la variable `APP_ENV` (por defecto
  `production`).
- **CORS**: solo GET, POST, PUT, PATCH, DELETE y OPTIONS (los que usa el
  frontend) y las cabeceras `Authorization` y `Content-Type`.
- **Excel subidos** (facturación masiva, eliminar/actualizar facturas,
  actualizar NIT): solo `.xlsx` (si no, 415), máximo 10 MB (413,
  comprobado antes de cargarlo entero) y el contenido debe ser un Excel
  real, no solo la extensión (422 con un mensaje que explica qué hacer).
- 19 pruebas nuevas (`tests/test_seguridad_http.py`), incluido un
  preflight simulado desde el frontend, archivo grande, extensión falsa
  y archivo dañado.

## Parte 4 — Rendimiento

- **Listado de remisiones**: pasó de **118 consultas** a la base por
  página (571 con 100 filas) a **3**. La respuesta es idéntica: se
  compararon 122 páginas (12.150 filas, 376.650 campos) antes y después,
  0 diferencias. Queda una prueba permanente que lo verifica.
- **Conexiones a la base**: máximo 10 (pool de 3 + 7 extra, con
  verificación de conexiones caídas), dentro de las 25 que permite
  Render free. Ajustable con `DB_POOL_SIZE` / `DB_MAX_OVERFLOW`.
- **Correo**: ya no bloquea la petición (hecho en la Parte 2).

## Parte 5 — Limpieza de bajo riesgo

- `REDIS_URL` eliminado (no se usaba en ninguna parte): configuración,
  `.env.example`, README y `docker-compose.yml`.
- La constante del permiso de administración quedó definida en un solo
  lugar.
- El inicio de sesión hace una petición menos (la respuesta del login ya
  trae los datos del usuario; se comprobó con una prueba que son
  idénticos a los de `/me`).

## Parte 6 — Limpieza de alto riesgo

### Valor total de una remisión — NO se unificó
Hay dos cálculos y **no dan lo mismo en 282 de las 1.000 remisiones**
(todas las que tienen alguna línea con más de un viaje):

| | Cálculo | Dónde se usa |
|---|---|---|
| A | (material + flete + cama baja) **× número de viajes** | Campo `valor_total` de la API de remisiones (columna "Valor total" del listado de Remisiones; ver corrección en la sesión 5) |
| B | material + flete + cama baja, **sin multiplicar** | Facturación: saldo, estado, validaciones, panel de facturación |

**La que parece correcta es la B (sin viajes):**
- En las **261 remisiones ya facturadas** que difieren, lo facturado
  coincide exactamente con B; con A, en ninguna.
- En el informe del programa anterior el flete ya es el total de la
  línea. Ejemplo: GTM-29826, 154 m³ de tierra en 11 viajes, flete
  2.002.000 = 154 × 13.000. Con A daría 22.022.000.
- Las otras 21 aún no están facturadas.

Lista completa (número, fecha, estado, A, B, facturado, viajes por
línea): `backups/diferencias_valor_total_remisiones.csv`.
**Actualización (mismo día):** el cliente confirmó la regla B. Ya está
unificada; ver "Seguimiento" al final de esta sesión.

### Fechas
Se fijó un único criterio: **hora UTC sin zona horaria**, que es como
están definidas hoy todas las columnas de fecha en la base y como ya
está guardado todo. Se reemplazó la función obsoleta en todos los
modelos y servicios a la vez. **No se modificó ningún dato guardado.**
9 pruebas: vencimiento de códigos y sesiones, creación/actualización de
registros y anulación de facturación (sobre una copia de la base, sin
dejar cambios).

## Cierre de la sesión

- `pytest`: 79 pruebas pasan + 1 "falla esperada" (la del valor total,
  a propósito). `tsc` y `npm run build`: OK.
- `alembic upgrade head` desde una base vacía: aplica las 6 migraciones
  sin errores y el esquema coincide con los modelos (`alembic check`).
- **Base real intacta**: 1.000 remisiones, 91 facturas, 1.613 terceros;
  el contenido es idéntico, línea por línea, al backup tomado antes de
  empezar. Todas las pruebas corrieron sobre SQLite en memoria o sobre
  una copia (`remisiones_prueba`).

### Pasos para Render (toda la sesión)
1. **Comando de arranque** (ya en el `Dockerfile`):
   `alembic upgrade head && python -m app.seed_auth && uvicorn app.main:app --host 0.0.0.0 --port 8000 --proxy-headers --forwarded-allow-ips='*'`
2. **Migraciones**: se aplican solas al arrancar (`a3c9e1f04b72` y las
   pendientes anteriores, como la de prefijos).
3. **Variables de la API**: `APP_ENV=production` (ya en `render.yaml`);
   `SMTP_*` configuradas para la recuperación de contraseña; opcionales
   `DB_POOL_SIZE`, `DB_MAX_OVERFLOW`, `RATE_LIMIT_ENABLED`,
   `RATE_LIMIT_STORAGE_URI`. `REDIS_URL` ya no se usa.
4. **Frontend**: cabeceras en `render.yaml` (o en el panel si el sitio
   no usa el blueprint).
5. **En local**: correr `alembic upgrade head` antes de levantar el
   backend (sin eso el login falla) y tener `APP_ENV=development` en
   `.env` (ya agregado).

### Pendiente
- Configurar una cuenta de correo real en `SMTP_*` (local y Render).
- Revisar en Render qué IP llega en `X-Forwarded-For`.
- Siguiente fase (documentado, no hecho): sesión en cookies httpOnly +
  CSP en lugar de `localStorage`; lista negra de tokens con Redis;
  índices trigram (`pg_trgm`) para las búsquedas; auditoría en catálogos
  y al cambiar la contraseña de un usuario desde Administración.

## Seguimiento — Valor total unificado (regla B, sin viajes)

- Una sola regla para todo el sistema: **valor total = material + flete
  + cama baja de cada línea, sin multiplicar por el número de viajes**.
- Comprobado sobre una copia de la base, antes vs después del cambio:
  - **Facturación sin ningún cambio** en las 1.000 remisiones: valor
    total, valor facturado, saldo y estado iguales.
  - **Ninguna remisión facturada cambió de valor** (718 facturadas o
    parciales).
  - **Reportes Excel idénticos** celda por celda (general: 1.227 filas;
    facturadas: 719).
  - Solo cambia el campo `valor_total` que entrega la API de remisiones
    en las 282 remisiones con varios viajes; ahora coincide con
    facturación. **Corrección (sesión 5):** ese valor sí se ve en la
    columna "Valor total" del listado de Remisiones, que antes mostraba
    el valor multiplicado por los viajes y ahora el correcto.
- Prueba sobre las 1.000 remisiones: **cero diferencias**. `pytest`: 81
  pruebas pasan.
- Prueba manual (login, recuperación, importación de Excel) correcta,
  salvo la recepción real del correo: las variables `SMTP_*` del `.env`
  local tienen todavía el valor de ejemplo.

---

# Sesión 5 (2026-10-28) — Orden de columnas, filas por página y reportes exactos

Esta sesión partió de lo hecho el 25-10 (sesión 3): se verificó cada punto
contra lo pedido y se corrigió lo que faltaba. Sin commits ni ramas. Todas
las pruebas usaron la copia de la base (`remisiones_prueba`), nunca la real.

## Bloque A — Columnas ordenables

**Cómo funciona**: clic en el encabezado → ascendente (▲) → descendente
(▼) → sin orden. También con teclado (Enter / Espacio) y con `aria-sort`
para lectores de pantalla. Las columnas de casillas y de Acciones no se
ordenan.

**Qué se agregó o corrigió hoy**
- **Pantallas nuevas con orden**: Ubicaciones (los dos paneles ahora son
  tablas, por Nombre y Código DANE), el detalle de una factura (y la
  lista del modal "Agregar remisiones") y Roles.
- **Columnas que antes no se podían ordenar**: Valor total (Remisiones),
  Remisiones y Valor total facturado (Facturación), Tipos y Municipio
  (Terceros), Empresa (Activos), Roles (Usuarios).
- **Números como números**: el número de factura se ordena por sus
  partes (F-7-468 antes que F-7-1000); la identificación y el teléfono
  de terceros como número; el número de remisión por prefijo y
  consecutivo; fechas como fecha.
- **El orden se conserva al paginar**: antes, al ordenar por una columna
  con valores repetidos (fecha, estado, cliente…), una fila podía
  aparecer en dos páginas o en ninguna. Ahora cada lista desempata
  siempre de la misma forma. Los vacíos van al final.
- El orden se hace en el servidor en las listas paginadas (con lista
  cerrada de columnas permitidas: cualquier otra se rechaza) y en el
  navegador en las que se cargan completas.
- En Remisiones, ordenar no borra la selección.

**Verificación**: 23 pruebas automáticas recorren todas las páginas de 8
listas con cada columna en ambos sentidos (sin filas repetidas ni
perdidas). En el navegador (Playwright, 1492×702 @1,25 y 390 px):
**62/62 comprobaciones correctas**. Capturas en `capturas/bloqueA_*`.

> **Corrección a lo informado en la sesión 4**: la columna "Valor total"
> del listado de Remisiones **sí** muestra el valor que cambió con la
> unificación. En las 282 remisiones con varios viajes, antes se veía el
> valor multiplicado por los viajes; ahora se ve el valor correcto (el
> mismo que usa facturación).

## Bloque B — Filas por página

El selector (10 · 25 · 50 · 100) con el total ("1–25 de 1.000") ya estaba
en todas las listas paginadas y recuerda la elección por lista. Se
completaron los estados que faltaban: carga en Ubicaciones, y error con
"Reintentar" / vacío en Roles y en el detalle de factura.

**Verificación en el navegador: 99/99 correctas** en Remisiones,
Facturación, Terceros, Activos, Usuarios, Catálogos y Ubicaciones, en
ambos tamaños: selector, rango, se recuerda al recargar, carga, vacío,
error + Reintentar, y funciona aunque el navegador no permita guardar
datos. Capturas en `capturas/bloqueB_*`.

## Bloque C — Reportes con las columnas exactas

**Encabezados**: los dos reportes ya tenían exactamente las 34 y 32
columnas pedidas, en orden y con la ortografía del original ("Hola
salida", "Numero de remision", "Número de factura"). No hubo que renombrar
nada.

**Formato corregido**
- ID del usuario / ID usuario / ID usuario factura: ahora como texto
  (antes número).
- Horas: con formato `hh:mm` (antes sin formato).
- Valores en pesos: número entero cuando no tienen centavos (250000, no
  250000.0), como en la hoja de referencia; los centavos que existen se
  conservan.

**Importador corregido** (lo encontró la prueba de ida y vuelta)
- No reconocía la columna "Hola salida": **al reimportar se perdía la
  hora de salida**.
- No entendía los estados como los escribe el reporte (NO_FACTURADA,
  FACTURADA_PARCIAL).
- Quitaba los ceros a la izquierda de las identificaciones.

**Verificación**
1. Encabezados comparados carácter por carácter con la lista pedida y con
   las hojas de referencia: idénticos.
2. Tipo y formato por columna (fechas, horas, identificaciones, valores),
   fila 1 con los encabezados, sin celdas combinadas ni título, número de
   remisión con el formato aprobado, y en facturadas una fila por remisión
   y factura (718).
3. **Ida y vuelta**: se generó el reporte general, se borraron las
   remisiones en la copia de la base, se reimportó el archivo con el
   importador existente y se comparó campo por campo con lo original:
   **1.000 de 1.000 remisiones y 1.225 de 1.225 líneas coinciden**, 0
   columnas sin reconocer, 0 remisiones con error. Único aviso: el ya
   conocido de GTS-6467 (una línea sin producto en el dato original).
   Todo dentro de una transacción que se deshizo al final.
   (La prueba de la sesión 3 no llegaba a comparar datos: el importador
   omitía las 1.000 remisiones porque ya existían.)
4. **Columnas vacías por falta de dato** (no se inventó ningún valor):

| Columna | Vacía | De dónde saldría | Propuesta |
|---|---|---|---|
| ID del conductor, Valor de comisión, Valor de costo, Unidad de medida, Id Producto | 0,1% (solo GTS-6467) | Casi nunca faltan | Nada que hacer |
| ODS | 100% | No hay órdenes de servicio cargadas; en la importación histórica no quedó claro qué columna del Excel es la ODS | Definir esa columna con el cliente y cargarla |
| Proyecto / Tramo | 100% | Hay 24 proyectos, pero ninguno de estas 1.000 remisiones | Nada (no aplica a esta muestra) |
| Kilometros, Cama Baja, Hora llegada, Hola salida, Remision AGRESUR | 97% / 99% / 98% / 45% / 52% | El Excel de origen ya venía así | Nada |
| **Usuario / ID del usuario** | Llenas, pero **no reales** | Las 1.000 históricas dicen "Administrador del Sistema" / "1": el nombre real quedó solo en Observaciones y el sistema no guarda la cédula de los usuarios | Agregar un campo de identificación a los usuarios y asignar el creador real a las históricas a partir de esa nota. **Requiere tu aprobación** (modifica datos) |

Los dos archivos de ejemplo de `formatos/` se regeneraron con el formato
corregido.

## Cierre

- `pytest`: **123 pruebas pasan**. `tsc` y `npm run build`: OK.
- `alembic upgrade head` desde una base vacía: 6 migraciones sin errores
  y el esquema coincide con los modelos.
- **Base real intacta**: 1.000 remisiones, 91 facturas, 1.613 terceros;
  las 27 tablas tienen exactamente los mismos datos que el backup previo.
- **Pasos para Render**: sin cambios respecto de la sesión 4 (esta sesión
  no agrega migraciones ni variables de entorno).

### Pendiente
- Aprobar (o no) la propuesta de Usuario / ID del usuario.
- Definir de dónde sale la ODS.
- Reiniciar los servidores locales para tomar el código nuevo.

---
