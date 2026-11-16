---
titulo: Solución de problemas
descripcion: Qué hacer cuando algo no funciona como esperas.
orden: 3
rol: todos
actualizado: 2026-11-16
---

## No puedo iniciar sesión {#no-puedo-iniciar-sesion}

:::pasos
1. Revisa que el **Correo** esté bien escrito, sin espacios.
2. Revisa la tecla Bloq Mayús y escribe de nuevo la **Contraseña** (usa el ícono del ojo para verla).
3. Si dice «El usuario está inactivo», pide a un administrador que lo active.
4. Si dice «Demasiados intentos…», espera el tiempo indicado.
5. Si olvidaste la contraseña, usa **¿Olvidaste tu contraseña?**.
:::

## No me llega el correo de recuperación {#no-llega-el-correo}

:::pasos
1. Revisa la carpeta de correo no deseado o spam.
2. Espera unos minutos.
3. Haz clic en **¿No recibiste el código? Volver a intentar** y confirma el correo.
4. Si dice «La recuperación de contraseña no está disponible en este momento.», el correo del sistema no está configurado: pide a un administrador que te cambie la contraseña.
:::

:::nota
Solo puedes pedir unos pocos códigos por hora. Si pides muchos seguidos, el sistema te pedirá esperar.
:::

## «Ya existe la remisión …» (consecutivo ya existe) {#consecutivo-ya-existe}

Ese número ya está registrado con ese prefijo. Recuerda que **00123** y **123** son el mismo número.

:::pasos
1. Busca el número en **Remisiones** para ver la remisión existente.
2. Si el prefijo es manual, revisa el número del talonario y corrígelo.
3. Si el prefijo es automático y aparece este error, avisa a un administrador para que revise el **Consecutivo actual** del prefijo en Catálogos.
:::

## Saldo insuficiente en la orden de servicio {#saldo-insuficiente}

Mensaje: «El valor_flete excede el saldo disponible de la orden de servicio…».

:::pasos
1. Revisa el saldo disponible de la orden en el campo **Número de orden de servicio**.
2. Baja el **Valor flete** del producto, o
3. Quita la orden de la remisión (recuerda que cambiarla elimina los productos), o
4. Pide al administrador que amplíe el saldo de la orden.
:::

## No puedo editar una remisión {#no-puedo-editar}

| Causa | Solución |
|---|---|
| Está **Facturada** («…no se puede editar. Solo puedes consultarla.») | Anula su facturación o quítala de la factura y vuelve a intentarlo. |
| Tu rol es Solo Consulta | Pide a un administrador el rol Operador. |

## El reporte sale vacío {#reporte-vacio}

El Excel trae solo los encabezados cuando ninguna remisión cumple los filtros.

:::pasos
1. Revisa **Desde** y **Hasta**.
2. Revisa **Cliente**, **Proyecto** y **Estado de facturación**.
3. Haz clic en **Limpiar** y descarga de nuevo.
:::

## Otros problemas

| Situación | Solución |
|---|---|
| La pantalla dice **Acceso denegado** | Tu rol no tiene permiso para esa pantalla. Haz clic en **Volver al inicio**. |
| Un botón está deshabilitado | Pasa el mouse sobre él: si dice «No tienes permiso para esta acción», tu rol no lo permite. |
| Los datos no se actualizan | Recarga la página con **F5**. |
| Me sacó del sistema | La sesión venció, o tu contraseña se cambió desde otro equipo (por ti o por un administrador). Inicia sesión de nuevo. |
