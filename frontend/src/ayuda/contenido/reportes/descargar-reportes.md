---
titulo: Descargar reportes
descripcion: Cómo generar los reportes en Excel de remisiones y de remisiones facturadas.
orden: 1
rol: todos
actualizado: 2026-11-16
---

## Para qué sirve

La pantalla **Reportes** («Genera y descarga reportes en Excel del módulo de Remisiones, con filtros opcionales.») produce dos archivos Excel con columnas fijas, listos para análisis o conciliación.

## Quién puede usarla

Todos los roles.

## Los dos reportes

| Reporte | Qué trae |
|---|---|
| **Reporte general de remisiones** | Una fila por cada línea de producto de la remisión, con 34 columnas. |
| **Reporte de remisiones facturadas** | Una fila por cada facturación activa (una remisión con varias facturas parciales aparece varias veces), con 32 columnas. |

## Paso a paso

:::pasos
1. En el menú, en **Análisis**, haz clic en **Reportes**.
2. En la tarjeta del reporte que necesitas, ingresa los filtros que quieras (todos son opcionales).
3. Haz clic en **Descargar Excel**. Mientras se genera dice «Descargando…».
4. Abre el archivo descargado.
:::

@captura 01-reportes.png | Pantalla Reportes con las dos tarjetas y los filtros vacíos

:::campos
| Campo | Qué es | Obligatorio | Ejemplo |
|---|---|---|---|
| Desde | Fecha inicial de la remisión | No | 01/05/2026 |
| Hasta | Fecha final de la remisión | No | 31/05/2026 |
| Cliente | Un solo cliente | No | Todos |
| Proyecto | Un solo proyecto | No | Todos |
| Estado de facturación | Todos, No facturada, Facturada parcial o Facturada | No | Todos |
:::

Para borrar los filtros de una tarjeta, haz clic en **Limpiar**.

## Reglas y validaciones

- Las columnas y su orden son fijos (los pidió el cliente) y no se pueden cambiar desde la aplicación.
- En el Excel, el número de remisión sale con 6 dígitos (por ejemplo GTS-006528) y la unidad con el nombre del catálogo (METRO CÚBICO), para que el archivo se pueda volver a importar.
- La columna **ID** del reporte general es el identificador interno de la remisión; es el que se usa en [Cargas por Excel](/ayuda/cargas-excel).
- La columna **ID del usuario** sale de la **Identificación (cédula)** del usuario; si no la tiene, queda vacía.

## Cierre anual {#cierre-anual}

La tarjeta **Cierre anual** genera un Excel con tres hojas para el año que elijas:

| Hoja | Qué trae |
|---|---|
| **Resumen** | Total facturado del año, por mes, por cliente y por serie de factura; cantidad de facturas y de remisiones; remisiones del año sin facturar, facturadas parcialmente y «No aplica facturación»; y cuántas remisiones del año se facturaron en otro año (y al revés). |
| **Facturas** | Una fila por factura del año: número, fecha, cliente, tipo (Total/Parcial), valor facturado y cantidad de remisiones. |
| **Detalle** | Una fila por remisión facturada, con las mismas 32 columnas del reporte de remisiones facturadas. |

:::pasos
1. En la tarjeta **Cierre anual**, elige el **Año**.
2. En **Agrupar por** elige **Fecha de factura (cierre contable)** o **Fecha de la remisión**.
3. Haz clic en **Descargar Excel**. Un año completo puede tardar unos segundos (dice «Generando…»).
:::

:::nota
Las cifras del cierre por fecha de factura coinciden con el listado de **Facturación** filtrado por ese año. El cierre por fecha de la remisión sirve cuando una factura cubre remisiones de otro año.
:::

## Errores comunes

| Situación | Solución |
|---|---|
| El Excel solo trae encabezados | No hay datos con esos filtros. Verás «Reporte descargado. Si no hay resultados con estos filtros, el Excel trae solo los encabezados.» Amplía las fechas o haz clic en **Limpiar**. |
| «No se pudo generar el reporte.» | Intenta de nuevo; si persiste, avisa al administrador. |
