---
titulo: Orden de servicio y saldo
descripcion: Cómo una remisión descuenta el flete del saldo de una orden de servicio.
orden: 5
rol: todos
actualizado: 2026-11-16
---

## Para qué sirve

Una **orden de servicio** (ODS) es un cupo en pesos que el cliente aprueba para fletes. Si asocias una remisión a una orden, el **Valor flete** de sus productos se descuenta del saldo de esa orden.

## Cómo asociar una orden

:::pasos
1. En la pestaña **Datos**, después de elegir el **Cliente**, abre **Número de orden de servicio**.
2. Cada opción muestra el número y el saldo, por ejemplo «OS-001 — $ 5.000.000 disponible».
3. Elige la orden y haz clic en **Guardar remisión**.
4. En la pestaña **Productos**, al guardar cada producto, su **Valor flete** se descuenta del saldo.
:::

## Reglas y validaciones

- Si el flete supera el saldo disponible, el producto no se guarda y verás «El valor_flete excede el saldo disponible de la orden de servicio…» con el saldo actual.
- Si después de guardar el saldo queda por debajo del **10 %** del valor tope de la orden, verás un aviso de **saldo bajo**.
- Al editar o eliminar un producto, la diferencia del flete se devuelve o se descuenta de la orden.

:::importante
Cambiar la orden de servicio de una remisión **elimina los productos** de esa remisión (y devuelve su flete a la orden anterior). El formulario te lo advierte con «Cambiar la orden elimina los productos de esta remisión.»
:::

## Dónde se crean las órdenes

La aplicación **no tiene una pantalla** para crear o editar órdenes de servicio: aquí solo se consultan y se asocian. Si necesitas una orden nueva, pídesela al administrador del sistema.

## Errores comunes

| Situación | Solución |
|---|---|
| «El valor_flete excede el saldo…» | Baja el valor flete, quita la orden de la remisión o pide ampliar el saldo de la orden. |
| La lista de órdenes está vacía | El cliente no tiene órdenes registradas. Deja el campo vacío. |
