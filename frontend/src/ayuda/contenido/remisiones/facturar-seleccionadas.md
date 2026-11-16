---
titulo: Facturar varias remisiones
descripcion: Cómo seleccionar varias remisiones del mismo cliente y facturarlas juntas, o agregar una a una factura existente.
orden: 10
rol: todos
actualizado: 2026-11-16
---

## Para qué sirve

Factura en un solo paso varias remisiones del mismo cliente con el mismo número de factura.

## Quién puede usarla

Roles **Administrador** y **Operador**.

## Facturar seleccionadas

:::pasos
1. En **Remisiones**, marca la casilla de cada remisión que vas a facturar.
2. Abajo aparece una barra con «N remisión(es) seleccionada(s) · cliente».
3. Haz clic en **Facturar seleccionadas**. Se abre **Facturar remisiones seleccionadas**.
4. Escribe el **Número de factura** y elige la **Fecha de factura**.
5. Revisa el resumen (mientras se calcula dice «Calculando resumen…»).
6. Haz clic en **Confirmar factura**.
:::

@captura 01-barra-seleccion.png | Listado con tres remisiones de prueba marcadas y la barra Facturar seleccionadas visible

:::campos
| Campo | Qué es | Obligatorio | Ejemplo |
|---|---|---|---|
| Número de factura | Una letra mayúscula, guion y dígitos | Sí | F-7-468 |
| Fecha de factura | Fecha de la factura | Sí | 15/05/2026 |
:::

### Reglas y validaciones

- Todas las remisiones deben ser del **mismo cliente**: al marcar la primera, las de otros clientes quedan deshabilitadas.
- Las remisiones **Facturada** no se pueden marcar.
- Cada remisión se factura por su **saldo pendiente** completo.
- Si alguna no se puede facturar verás «No se puede facturar esta selección:» con el motivo de cada una.
- Para quitar la selección haz clic en **Limpiar** o presiona **Esc**.

## Agregar a factura existente {#agregar-a-factura-existente}

:::pasos
1. En la fila de la remisión, haz clic en **Agregar a factura existente**.
2. Escribe el **Número de factura** (por ejemplo F-7-468).
3. Haz clic en **Agregar**.
:::

La factura debe existir y ser del **mismo cliente** que la remisión.

## Qué pasa después

- Las remisiones cambian a **Facturada** y la factura aparece en [Facturación](/ayuda/facturacion).
- Si te equivocas, abre la factura y usa **Quitar de la factura** (ver [Quitar remisiones](/ayuda/facturacion/quitar-remisiones)).
