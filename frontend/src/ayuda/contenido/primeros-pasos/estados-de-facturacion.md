---
titulo: Estados de facturación
descripcion: Qué significan No facturada, Facturada parcial, Facturada y No aplica facturación.
orden: 6
rol: todos
actualizado: 2026-11-16
---

## Para qué sirve

Cada remisión tiene un **estado de facturación**. Los tres primeros los calcula el sistema solo, comparando el valor total de la remisión con lo que ya se facturó; «No aplica facturación» es una marca que se conserva.

## Los cuatro estados

| Estado | Qué significa | Qué se puede hacer |
|---|---|---|
| **No facturada** | Todavía no tiene ninguna facturación activa. | Editarla, facturarla total o parcialmente, agregarla a una factura. |
| **Facturada parcial** | Ya se facturó una parte; queda **saldo pendiente**. | Editarla y seguir facturando el saldo. |
| **Facturada** | Se facturó por completo (saldo pendiente $ 0). | Solo consultarla: ya no se puede editar. |
| **No aplica facturación** | La remisión no se factura (por ejemplo, un servicio interno o una donación). | Consultarla y editarla. No aparece como pendiente ni se puede facturar ni agregar a una factura. |

## «No aplica facturación» {#no-aplica}

A diferencia de los otros tres, este estado no se calcula: es una marca. El sistema la conserva aunque la remisión tenga facturas registradas (el histórico trae remisiones «No aplica» con factura, y se cargaron tal cual).

- No cuenta en el indicador **Sin facturar** del Inicio.
- Su casilla en el listado de remisiones está deshabilitada y el botón **Facturar** de la pestaña **Facturación** también.
- Se puede filtrar en **Remisiones** y en **Reportes** con el estado **No aplica facturación**.

## Cómo se calculan

- **Valor total de la remisión** = suma de *valor material + valor flete + valor cama baja* de todos sus productos. No se multiplica por el número de viajes.
- **Facturado** = suma de las facturaciones activas (las anuladas no cuentan).
- **Saldo pendiente** = valor total − facturado.

:::nota
Si anulas una facturación o quitas la remisión de una factura, el estado se recalcula: una remisión **Facturada** puede volver a **Facturada parcial** o **No facturada**.
:::

## Errores comunes

| Situación | Solución |
|---|---|
| «Esta remisión está totalmente facturada (FACTURADA) y no se puede editar. Solo puedes consultarla.» | Si hay que corregirla, primero anula su facturación (pestaña **Facturación** de la remisión) o quítala de la factura. |
| No puedo facturar: «no tiene productos» | Una remisión sin productos vale $ 0; agrega al menos un producto. |
