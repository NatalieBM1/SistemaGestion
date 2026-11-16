---
titulo: Prefijos
descripcion: Series de numeración de las remisiones, automáticas o manuales.
orden: 1
rol: todos
actualizado: 2026-11-16
---

## Para qué sirve

Define las series con que se numeran las remisiones (por ejemplo GTS o GTM) y en qué número va cada una.

## Quién puede usarlo

Todos los roles pueden consultarlo. **Solo el Administrador** puede crear, editar o eliminar prefijos.

## Crear un registro

:::pasos
1. En el menú, en **Datos**, haz clic en **Catálogos**.
2. Abre la pestaña **Prefijos**.
3. Haz clic en **Nuevo prefijo**.
4. Ingresa la información en los campos.
5. Haz clic en **Guardar**. Verás «Prefijo creado correctamente.»
:::

@captura 01-prefijos.png | Pestaña Prefijos de Catálogos con registros de prueba y el botón Nuevo prefijo

:::campos
| Campo | Qué es | Obligatorio | Ejemplo |
|---|---|---|---|
| Código | Letras de la serie | Sí | GTS |
| Consecutivo actual | Último número usado; la siguiente remisión automática toma el siguiente | No | 6528 |
| Es manual (remisión de papel) | Márcalo si el número lo escribe el usuario desde un talonario | No | Marcado para GTM |
:::

## Buscar, editar y eliminar

- Para buscar, escribe en el buscador («Buscar por código…»).
- Para corregir, haz clic en **Editar** en la fila, cambia los datos y guarda.
- Para borrar, haz clic en **Eliminar** y confirma en **Confirmar eliminación**. Esta acción no se puede deshacer.

## Reglas y validaciones

- Los nombres y códigos se guardan en MAYÚSCULAS automáticamente.
- No puede haber dos registros con el mismo valor. Si ya existe verás «Ya existe un registro de …».
- No puedes eliminar un registro que ya usan remisiones u otros datos: verás «El registro no se pudo guardar por un conflicto de datos (posible duplicado o referencia en uso).»
- **Solo el Administrador** puede crear, editar o eliminar prefijos; el Operador solo los consulta.
- Cambiar el **Consecutivo actual** afecta el número de la próxima remisión. Hazlo con cuidado para no repetir números.
- Ver [Prefijo y consecutivo](/ayuda/remisiones/prefijo-y-consecutivo).

## Errores comunes

| Situación | Solución |
|---|---|
| El botón **Nuevo prefijo** está deshabilitado | Tu rol no puede crear en este catálogo. |
| Los botones **Editar** y **Eliminar** están deshabilitados | Solo el Administrador edita o elimina. |
| «… es obligatorio.» | Ingresa la información del campo marcado como obligatorio. |
