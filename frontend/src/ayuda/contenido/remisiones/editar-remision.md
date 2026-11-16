---
titulo: Editar una remisión
descripcion: Cómo corregir los datos o productos de una remisión existente.
orden: 7
rol: todos
actualizado: 2026-11-16
---

## Quién puede usarla

Roles **Administrador** y **Operador**.

## Paso a paso

:::pasos
1. En **Remisiones**, busca la remisión.
2. En la fila, haz clic en **Editar remisión**.
3. Corrige lo necesario en las pestañas **Datos** o **Productos**.
4. Haz clic en **Guardar remisión** (en Productos, cada producto se guarda con **Guardar producto**).
:::

## Reglas y validaciones

- Una remisión **Facturada** no se puede editar: verás «Esta remisión está totalmente facturada (FACTURADA) y no se puede editar. Solo puedes consultarla.» Los campos quedan de solo lectura.
- Una remisión **Facturada parcial** sí se puede editar. Si cambias valores de productos, revisa después el **Saldo pendiente** en la pestaña **Facturación**.
- Cambiar la orden de servicio elimina los productos (ver [Orden de servicio y saldo](/ayuda/remisiones/orden-de-servicio-y-saldo)).
- El número de una remisión no se puede repetir.

## Errores comunes

| Situación | Solución |
|---|---|
| Todos los campos están bloqueados | La remisión está Facturada. Anula la facturación en la pestaña **Facturación** o quítala de la factura y vuelve a intentar. |
| El botón **Guardar remisión** está deshabilitado | Tu rol es Solo Consulta. |
