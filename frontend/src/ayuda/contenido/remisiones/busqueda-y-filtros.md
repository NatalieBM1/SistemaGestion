---
titulo: Búsqueda, filtros, orden y filas
descripcion: Cómo encontrar remisiones por cliente, número, placa, proyecto, factura o fechas, y cómo ordenar la tabla.
orden: 2
rol: todos
actualizado: 2026-11-16
---

## Para qué sirve

Con el buscador y los filtros reduces la lista a las remisiones que necesitas. Con el orden de columnas y **Filas por página** controlas cómo se muestran.

## Búsqueda rápida

:::pasos
1. En el buscador («Buscar por cliente, número, placa, proyecto o factura…») escribe lo que buscas, por ejemplo **GTS-6525**, **ABC123** o parte del nombre del cliente.
2. La tabla se actualiza sola mientras escribes.
3. Para ver todo de nuevo, borra el texto del buscador.
:::

## Filtros

Los filtros están siempre visibles debajo del buscador.

:::pasos
1. Ingresa o elige uno o varios filtros (todos son opcionales): **Número de remisión**, **Placa**, **Proyecto**, **Número de factura**, **Desde**, **Hasta**, **Estado** y **Cliente**.
2. La tabla se actualiza sola con cada cambio. El botón **Buscar** vuelve a consultar los datos por si alguien más hizo cambios.
3. Para quitar todos los filtros, haz clic en **Limpiar**.
:::

@captura 02-filtros.png | Zona de filtros de Remisiones con Número de remisión, Placa, Proyecto, Número de factura, Desde, Hasta, Estado y Cliente, con datos de prueba

:::campos
| Campo | Qué es | Obligatorio | Ejemplo |
|---|---|---|---|
| Número de remisión | Número con o sin prefijo. Con o sin ceros a la izquierda encuentra la misma remisión. | No | GTS-6525 |
| Placa | Placa del vehículo | No | ABC123 |
| Proyecto | Proyecto elegido de la lista | No | Todos |
| Número de factura | Factura en la que quedó la remisión | No | FV-0000 |
| Desde | Fecha inicial (incluida) | No | 01/05/2026 |
| Hasta | Fecha final (incluida) | No | 31/05/2026 |
| Estado | Todos, No facturada, Facturada parcial o Facturada | No | No facturada |
| Cliente | Un cliente de la lista, o Todos | No | Todos |
:::

:::nota
Los filtros se combinan: si ingresas **Placa** y **Desde**, verás solo las remisiones de esa placa a partir de esa fecha.
:::

## Ordenar la tabla {#ordenar}

Haz clic en el encabezado de **Número**, **Fecha**, **Cliente**, **Estado**, **Placa** o **Valor total**:

- Primer clic: de menor a mayor (flecha hacia arriba).
- Segundo clic: de mayor a menor (flecha hacia abajo).
- Tercer clic: vuelve al orden normal (más recientes primero).

El orden se aplica a **todas** las remisiones que cumplen los filtros, no solo a la página que ves.

## Filas por página {#filas}

Abajo de la tabla, en **Filas por página**, elige 10, 25, 50 o 100. El texto de la izquierda indica el rango, por ejemplo «1–25 de 1.000». Usa **Anterior** y **Siguiente** para cambiar de página. El sistema recuerda tu elección en ese navegador.

## Errores comunes

| Situación | Solución |
|---|---|
| No aparece una remisión que sé que existe | Revisa que el filtro de **Estado** esté en **Todos** y que **Desde**/**Hasta** la incluyan. Haz clic en **Limpiar**. |
| Busqué por número y no aparece | Escribe el prefijo y el número con guion, por ejemplo GTS-6525. |
