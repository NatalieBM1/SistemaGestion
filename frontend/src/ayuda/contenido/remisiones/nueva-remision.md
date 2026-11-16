---
titulo: Nueva remisión
descripcion: Cómo crear una remisión pestaña por pestaña: Datos, Productos y Facturación.
orden: 3
rol: todos
actualizado: 2026-11-16
---

## Para qué sirve

Registra un servicio de transporte: quién es el cliente, de dónde a dónde, con qué vehículo y conductor, y qué productos se llevaron. El formulario tiene tres pestañas: **Datos**, **Productos** y **Facturación**.

## Quién puede usarla

Roles **Administrador** y **Operador**. El rol Solo Consulta puede abrir una remisión, pero no guardarla.

## Resumen del proceso

:::pasos
1. En **Remisiones**, haz clic en **Nueva remisión**.
2. Ingresa la información de la pestaña **Datos** y haz clic en **Guardar remisión**.
3. Al guardar se habilitan las pestañas **Productos** y **Facturación**.
4. En **Productos**, agrega cada producto transportado.
5. Cuando corresponda, factura la remisión desde la pestaña **Facturación** o desde el listado.
:::

:::nota
Las pestañas **Productos** y **Facturación** solo se activan después de guardar la remisión por primera vez.
:::

## Pestaña Datos {#pestana-datos}

:::pasos
1. En **Cliente**, escribe parte del nombre o del NIT y elige el cliente de la lista.
2. Si el servicio pertenece a una orden de servicio, elígela en **Número de orden de servicio**. Si no, déjalo vacío.
3. Elige el **Prefijo**. Si el prefijo es automático, el **Número de consecutivo** dice «Automático»; si es manual (por ejemplo GTM), escribe el número en **Número de remisión (manual)**.
4. Revisa la **Fecha** (por defecto es la de hoy). Puedes escribirla, por ejemplo **16112026**, o elegirla con el ícono de calendario (ver [Escribir o elegir una fecha](/ayuda/primeros-pasos/recorrido-por-la-pantalla#fechas)).
5. Elige **Forma de pago** y **Tipo de transporte**.
6. Elige la **Ubicación de origen** y la **Ubicación de destino**.
7. Elige el **Conductor** y el **Vehículo** (busca por placa).
8. Si quieres, ingresa **Hora de salida**, **Hora de llegada**, **Proyecto**, **Tramo**, **Kilómetros**, **Remisión AGRESUR** y **Observaciones**.
9. Si el **Tipo de transporte** es cama baja, elige la placa en **Cama baja / Trailer / Volco**.
10. Haz clic en **Guardar remisión**.
:::

@captura 01-nueva-remision-datos.png | Pestaña Datos de una remisión nueva con cliente, prefijo, origen y destino de prueba ingresados

:::campos
| Campo | Qué es | Obligatorio | Ejemplo |
|---|---|---|---|
| Cliente | Tercero al que se le presta el servicio | Sí | CLIENTE DE PRUEBA S.A.S. |
| Número de orden de servicio | Orden con saldo de la que se descuenta el flete. Muestra el saldo disponible. | No | OS-001 — $ 5.000.000 disponible |
| Prefijo | Serie de la remisión | Sí | GTS |
| Número de consecutivo | Lo asigna el sistema al guardar (prefijos automáticos) | — | Automático |
| Número de remisión (manual) | Número del talonario de papel (prefijos manuales) | Sí, si el prefijo es manual | 00123 |
| Fecha | Fecha del servicio | Sí | 14/05/2026 |
| Forma de pago | Del catálogo Formas de pago | No | CONTADO |
| Tipo de transporte | Del catálogo Tipos de servicio | No | TRANSPORTE |
| Ubicación de origen | Municipio de salida | Sí | MUNICIPIO A, DEPARTAMENTO |
| Ubicación de destino | Municipio de llegada | Sí | MUNICIPIO B, DEPARTAMENTO |
| Conductor | Tercero que conduce | No | CONDUCTOR DE PRUEBA |
| Vehículo | Activo, buscado por placa | No | ABC123 |
| Hora de salida / Hora de llegada | Horas del recorrido | No | 07:30 |
| Proyecto | Proyecto del cliente | No | PROYECTO VÍA NORTE |
| Tramo | Tramo del proyecto (primero elige el proyecto) | No | TRAMO 1 |
| Kilómetros | Distancia recorrida | No | 12,5 |
| Remisión AGRESUR | Número de referencia externa | No | 4567 |
| Cama baja / Trailer / Volco | Placa del remolque | Sí, si el tipo es cama baja | XYZ987 |
| Observaciones | Notas que salen en el recibo impreso | No | Entregar en portería |
:::

### Botones de copiar

Junto al número, al cliente y a las ubicaciones de origen y destino hay un botón para copiar el dato. Las ubicaciones se copian como «MUNICIPIO, DEPARTAMENTO». Al copiar aparece el aviso **Copiado**.

### Reglas y validaciones {#reglas-datos}

- Si faltan datos obligatorios verás «Completa los campos obligatorios: prefijo, cliente, origen y destino.»
- **Tramo** solo se habilita después de elegir un **Proyecto** («Elige un proyecto»).
- El campo **Cama baja / Trailer / Volco** solo aparece si el tipo de transporte es cama baja, y entonces es obligatorio.
- Los nombres se guardan en MAYÚSCULAS automáticamente.
- Ver [Prefijo y consecutivo](/ayuda/remisiones/prefijo-y-consecutivo) y [Orden de servicio y saldo](/ayuda/remisiones/orden-de-servicio-y-saldo).

## Pestaña Productos {#pestana-productos}

:::pasos
1. Abre la pestaña **Productos** (la remisión debe estar guardada).
2. Haz clic en **Agregar producto**.
3. Ingresa los datos del producto.
4. Haz clic en **Guardar producto**.
5. Repite para cada producto. Para corregir uno usa **Editar producto**; para quitarlo, **Eliminar producto**.
:::

@captura 02-nueva-remision-productos.png | Pestaña Productos con dos productos de prueba en la tabla y el botón Agregar producto

:::campos
| Campo | Qué es | Obligatorio | Ejemplo |
|---|---|---|---|
| Producto | Del catálogo Productos | Sí | ARENA |
| Unidad de medida | Del catálogo Unidades de medida | Sí | m³ |
| Cantidad | Cantidad transportada; acepta coma decimal | Sí | 8 · 1,5 |
| Valor material | Valor del material en pesos | No | 1.200.000 |
| Valor flete | Valor del transporte en pesos | No | 850.000 |
| Valor cama baja | Valor del remolque (solo si la remisión tiene cama baja) | No | 300.000 |
| Número de viajes | Viajes realizados | No | 2 |
| Valor comisión | Comisión del servicio | No | 50.000 |
| Valor costo | Costo interno | No | 600.000 |
:::

### Reglas y validaciones {#reglas-productos}

- El **valor total** de la remisión es la suma de valor material + valor flete + valor cama baja de todos los productos. El número de viajes no lo multiplica.
- Si la remisión tiene orden de servicio, el **Valor flete** se descuenta del saldo de la orden. Si lo supera, verás «El valor_flete excede el saldo disponible de la orden de servicio…».
- Si una remisión está **Facturada**, sus productos no se pueden cambiar.

## Pestaña Facturación {#pestana-facturacion}

Muestra el resumen de facturación: **Estado**, **Valor total**, **Facturado** y **Saldo pendiente**, y el historial (**Factura**, **Fecha**, **Tipo**, **Valor**, **Estado**).

:::pasos
1. Abre la pestaña **Facturación**.
2. Haz clic en **Facturar**. Se abre **Facturar remisión**.
3. Escribe el **Número de factura** (formato: una letra mayúscula, guion y dígitos; ej. F-1234 o F-7-468).
4. Elige la **Fecha de factura**.
5. En **Tipo**, elige **Total** o **Parcial**. Si eliges Parcial, escribe el **Valor a facturar** (debajo ves el saldo pendiente).
6. Haz clic en **Facturar**.
:::

@captura 03-facturar-remision.png | Ventana Facturar remisión con tipo Parcial y un valor a facturar de prueba

:::campos
| Campo | Qué es | Obligatorio | Ejemplo |
|---|---|---|---|
| Número de factura | Número de la factura | Sí | F-7-468 |
| Fecha de factura | Fecha de la factura | Sí | 15/05/2026 |
| Tipo | Total (todo el saldo) o Parcial (una parte) | Sí | Parcial |
| Valor a facturar | Valor de la facturación parcial | Sí, si es Parcial | 500.000 |
:::

### Anular una facturación

:::pasos
1. En el historial, en la fila de la factura, haz clic en **Anular facturación**.
2. En **Confirmar anulación**, haz clic en **Anular**.
3. El saldo pendiente y el estado de la remisión se recalculan.
:::

### Reglas y validaciones {#reglas-facturacion}

- El valor parcial debe ser mayor que 0 y no puede superar el saldo pendiente.
- Una remisión sin productos no se puede facturar.
- Si la remisión ya está **Facturada**, el botón **Facturar** queda deshabilitado.

## Qué pasa después

- La remisión aparece en el listado con su estado.
- Puedes imprimir el recibo con **Imprimir** (arriba a la derecha). Ver [Imprimir el recibo](/ayuda/remisiones/imprimir-recibo).
- Para salir sin guardar, haz clic en la **X** (Cancelar y volver).
