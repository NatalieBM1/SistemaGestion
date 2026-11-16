---
titulo: Roles y permisos
descripcion: Qué puede hacer cada rol: Administrador, Operador y Solo Consulta.
orden: 2
rol: todos
actualizado: 2026-11-16
---

## Para qué sirve

Cada usuario tiene uno o varios **roles**. El rol decide qué pantallas puede ver y qué botones puede usar. Si un botón aparece deshabilitado y al pasar el mouse dice «No tienes permiso para esta acción», tu rol no lo permite.

## Los tres roles del sistema

| Acción | Administrador | Operador | Solo Consulta |
|---|---|---|---|
| Ver remisiones, facturas, catálogos, terceros, ubicaciones y activos | Sí | Sí | Sí |
| Crear y editar remisiones y sus productos | Sí | Sí | No |
| Facturar remisiones, anular facturaciones y hacer cargas por Excel | Sí | Sí | No |
| Crear terceros, ubicaciones y activos | Sí | Sí | No |
| Crear registros en los catálogos | Sí | Sí | No |
| Editar o eliminar registros de los catálogos | Sí | No | No |
| Crear, editar o eliminar **prefijos** de remisión | Sí | No | No |
| Descargar reportes | Sí | Sí | Sí |
| Recuperar y cambiar **su propia** contraseña | Sí | Sí | Sí |
| Administrar usuarios y roles | Sí | No | No |

:::nota
Los permisos de cada rol se pueden ajustar en **Administración → Roles** (ver [Roles](/ayuda/administracion/roles)). La tabla describe los permisos con los que el sistema crea cada rol.
:::

## Qué pasa si no tienes permiso

- Si entras a una pantalla que tu rol no permite (por ejemplo, Administración), verás la página de **Acceso denegado** con el botón **Volver al inicio**.
- Los botones de acciones no permitidas aparecen deshabilitados.
- Con el rol **Solo Consulta**, en **Cargas por Excel** puedes leer las instrucciones, pero el botón **Procesar archivo** está deshabilitado.

## Errores comunes

| Situación | Solución |
|---|---|
| No veo el menú **Administración** | Solo aparece para usuarios con el permiso de administrar usuarios. Pide a un administrador que revise tu rol. |
| El botón **Editar** del catálogo está deshabilitado | El rol Operador solo puede crear en los catálogos, no editar ni eliminar. |
