---
titulo: Tipos de servicio
descripcion: Opciones del campo Tipo de transporte de la remisión.
orden: 3
rol: todos
actualizado: 2026-11-16
---

## Para qué sirve

Las opciones que aparecen en el campo **Tipo de transporte** de la remisión.

## Quién puede usarlo

Todos los roles pueden consultarlo. Los roles **Administrador** y **Operador** pueden crear registros; solo el **Administrador** puede editarlos o eliminarlos.

## Crear un registro

:::pasos
1. En el menú, en **Datos**, haz clic en **Catálogos**.
2. Abre la pestaña **Tipos de servicio**.
3. Haz clic en **Nuevo tipo de servicio**.
4. Ingresa la información en los campos.
5. Haz clic en **Guardar**. Verás «Tipo de servicio creado correctamente.»
:::

@captura 01-tipos-de-servicio.png | Pestaña Tipos de servicio de Catálogos con registros de prueba y el botón Nuevo tipo de servicio

:::campos
| Campo | Qué es | Obligatorio | Ejemplo |
|---|---|---|---|
| Nombre | Tipo de servicio | Sí | TRANSPORTE |
:::

## Buscar, editar y eliminar

- Para buscar, escribe en el buscador («Buscar por nombre…»).
- Para corregir, haz clic en **Editar** en la fila, cambia los datos y guarda.
- Para borrar, haz clic en **Eliminar** y confirma en **Confirmar eliminación**. Esta acción no se puede deshacer.

## Reglas y validaciones

- Los nombres y códigos se guardan en MAYÚSCULAS automáticamente.
- No puede haber dos registros con el mismo valor. Si ya existe verás «Ya existe un registro de …».
- No puedes eliminar un registro que ya usan remisiones u otros datos: verás «El registro no se pudo guardar por un conflicto de datos (posible duplicado o referencia en uso).»
- En las listas, los tipos aparecen en este orden: **TRANSPORTE**, **DESALOJO**, **MATERIA PRIMA** y después el resto en orden alfabético.
- El tipo de cama baja hace que la remisión pida la placa en **Cama baja / Trailer / Volco** (ver [Cama baja](/ayuda/remisiones/cama-baja)).

## Errores comunes

| Situación | Solución |
|---|---|
| El botón **Nuevo tipo de servicio** está deshabilitado | Tu rol no puede crear en este catálogo. |
| Los botones **Editar** y **Eliminar** están deshabilitados | Solo el Administrador edita o elimina. |
| «… es obligatorio.» | Ingresa la información del campo marcado como obligatorio. |
