---
titulo: Agregar remisiones a una factura
descripcion: Cómo sumar remisiones del mismo cliente a una factura ya existente.
orden: 3
rol: todos
actualizado: 2026-11-16
---

## Quién puede usarla

Roles **Administrador** y **Operador**.

## Paso a paso

:::pasos
1. Abre el detalle de la factura.
2. Haz clic en **Agregar remisiones**. Se abre **Agregar remisiones a la factura**.
3. Si quieres, filtra con **Buscar** (número o placa), **Desde** y **Hasta**.
4. Marca las remisiones que vas a agregar (o **Seleccionar todas**).
5. Haz clic en **Agregar N remisión(es)**.
:::

@captura 01-agregar-remisiones.png | Ventana Agregar remisiones a la factura con dos remisiones de prueba marcadas

## Columnas de la ventana

| Columna | Qué muestra |
|---|---|
| Número | Número de la remisión. |
| Fecha | Fecha de la remisión. |
| Placa | Placa del vehículo. |
| Estado | No facturada o Facturada parcial. |
| Pendiente | Saldo pendiente que se facturará. |

## Reglas y validaciones

- Solo aparecen remisiones del **mismo cliente** de la factura que no estén totalmente facturadas.
- Cada remisión se agrega por su **saldo pendiente**.

## Errores comunes

| Situación | Solución |
|---|---|
| «Sin remisiones disponibles» | El cliente no tiene remisiones pendientes que coincidan con la búsqueda. Borra los filtros. |

También puedes agregar una sola remisión desde el listado de remisiones con **Agregar a factura existente** (ver [Facturar varias remisiones](/ayuda/remisiones/facturar-seleccionadas#agregar-a-factura-existente)).
