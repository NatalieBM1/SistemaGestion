---
titulo: Listado de facturas
descripcion: La pantalla Facturación: buscar facturas, abrirlas y corregir su número o fecha.
orden: 1
rol: todos
actualizado: 2026-11-16
---

## Para qué sirve

La pantalla **Facturación** reúne las facturas registradas en el sistema, con cuántas remisiones tiene cada una y el valor total facturado.

## Quién puede usarla

Todos los roles pueden consultarla. **Actualizar factura** requiere el rol Administrador u Operador.

## Paso a paso

:::pasos
1. En el menú, en **Operación**, haz clic en **Facturación**.
2. Si quieres, filtra con **Desde**, **Hasta**, **Año** y **Mes** (de la fecha de factura), **Cliente**, **Serie** (F-7, F-203, L-201…), **Estado** (Activa o Anulada) o **Número de factura**. Los filtros se combinan.
3. Haz clic en el número de una factura para ver su detalle.
:::

@captura 01-listado-facturas.png | Pantalla Facturación con filtros y facturas de prueba en la tabla

## Columnas

| Columna | Qué muestra |
|---|---|
| **Número de factura** | Enlace al detalle de la factura. |
| **Fecha** | Fecha de la factura. |
| **Cliente** | Cliente de las remisiones de la factura. Si tiene remisiones de varios clientes dice «VARIOS CLIENTES (n)». |
| **Tipo** | **Total** o **Parcial** (si alguna de sus facturaciones es parcial). |
| **Estado** | **Activa**, o **Anulada** si todas sus facturaciones se anularon. |
| **Remisiones** | Cuántas remisiones tiene la factura. |
| **Valor total facturado** | Suma de las facturaciones activas de esa factura. |

Las columnas se pueden ordenar haciendo clic en el encabezado.

## Actualizar el número o la fecha de una factura {#actualizar-factura}

:::pasos
1. En la fila de la factura, haz clic en **Actualizar factura** (ícono de lápiz).
2. Revisa el **Número de factura actual**.
3. Escribe el **Nuevo número de factura** y/o elige la **Nueva fecha de factura**. Lo que dejes vacío no cambia.
4. Haz clic en **Actualizar**.
:::

:::campos
| Campo | Qué es | Obligatorio | Ejemplo |
|---|---|---|---|
| Número de factura actual | El número que tiene hoy (solo lectura) | — | F-7-468 |
| Nuevo número de factura | Número corregido. Déjalo vacío para no cambiarlo. | No | F-7-469 |
| Nueva fecha de factura | Fecha corregida. Déjala vacía para no cambiarla. | No | 16/05/2026 |
:::

El cambio se aplica a todas las remisiones de esa factura.

## Cómo se crean las facturas {#crear-factura}

En esta pantalla **no hay un botón para crear facturas**. Una factura existe cuando le asignas su número a una o más remisiones:

- Desde el listado de remisiones con **Facturar seleccionadas** (ver [Facturar varias remisiones](/ayuda/remisiones/facturar-seleccionadas)).
- Desde una remisión, pestaña **Facturación**, botón **Facturar** (ver [Nueva remisión](/ayuda/remisiones/nueva-remision#pestana-facturacion)).
- De forma masiva con un archivo Excel (ver [Cargas por Excel](/ayuda/cargas-excel)).

El botón **Cargas por Excel** (arriba a la derecha) lleva a esa pantalla.

## Errores comunes

| Situación | Solución |
|---|---|
| «Sin facturas» | No hay facturas con esos filtros. Borra los filtros. |
| El nuevo número es rechazado | Usa el formato: una letra mayúscula, guion y dígitos (F-1234 o F-7-468). |
