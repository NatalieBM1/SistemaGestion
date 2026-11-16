---
titulo: Roles
descripcion: Ver los roles y cambiar los permisos de cada uno.
orden: 2
rol: administrador
actualizado: 2026-11-16
---

## Para qué sirve

La pantalla **Roles** muestra los roles del sistema, cuántos permisos tiene cada uno y cuántos usuarios lo usan. Desde aquí cambias qué puede hacer cada rol.

## Quién puede usarla

Solo usuarios con el permiso de administrar usuarios (rol **Administrador**).

## Cambiar los permisos de un rol

:::pasos
1. Abre la pantalla **Roles**: en la barra de direcciones del navegador, cambia el final de la dirección por **/admin/roles** y presiona **Enter**. Verás «Haz clic en un rol para editar sus permisos.»
2. Haz clic en el nombre del rol.
3. Marca o desmarca los permisos («Marca los permisos que debe tener este rol, agrupados por módulo.»).
4. Haz clic en **Guardar permisos**. Verás «Permisos del rol '…' actualizados correctamente.»
:::

:::nota
Hoy el menú **Administración** abre directamente **Usuarios** y no muestra un enlace a **Roles**; por eso se entra con la dirección. Desde el detalle de un rol puedes volver a la lista con **Cancelar** (sin guardar) o con la miga de pan **Roles**.
:::

## Columnas de la lista

| Columna | Qué muestra |
|---|---|
| **Rol** | Nombre del rol. |
| **Permisos asignados** | Cuántos permisos tiene. |
| **Usuarios con este rol** | Cuántos usuarios lo tienen. |

## Permisos principales

| Permiso | Qué permite |
|---|---|
| leer (de cada módulo) | Ver la pantalla y sus datos. |
| escribir (de cada módulo) | Crear y editar en remisiones, facturas, terceros, ubicaciones y activos. |
| catalogos.crear / editar / eliminar | Crear, editar o eliminar en los catálogos. |
| prefijos.administrar | Crear, editar o eliminar prefijos de remisión. |
| usuarios.administrar | Entrar a Administración. |

Los permisos con que viene cada rol están en [Roles y permisos](/ayuda/primeros-pasos/roles-y-permisos).

## Reglas y validaciones

- Si quitas a tu propio rol el permiso **usuarios.administrar** y no tienes otro rol que lo dé, el sistema te avisa que perderás el acceso a esta sección y no te deja guardar.
- Los cambios aplican a todos los usuarios con ese rol.

:::importante
Antes de quitar permisos, revisa la columna **Usuarios con este rol** para saber a cuántas personas afecta.
:::
