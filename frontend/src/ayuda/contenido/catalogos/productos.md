---
titulo: Productos
descripcion: Materiales y servicios que se registran en los productos de la remisión.
orden: 4
rol: todos
actualizado: 2026-11-16
---

## Para qué sirve

Los productos que se eligen en la pestaña **Productos** de la remisión.

## Quién puede usarlo

Todos los roles pueden consultarlo. Los roles **Administrador** y **Operador** pueden crear registros; solo el **Administrador** puede editarlos o eliminarlos.

## Crear un registro

:::pasos
1. En el menú, en **Datos**, haz clic en **Catálogos**.
2. Abre la pestaña **Productos**.
3. Haz clic en **Nuevo producto**.
4. Ingresa la información en los campos.
5. Haz clic en **Guardar**. Verás «Producto creado correctamente.»
:::

@captura 01-productos.png | Pestaña Productos de Catálogos con registros de prueba y el botón Nuevo producto

:::campos
| Campo | Qué es | Obligatorio | Ejemplo |
|---|---|---|---|
| Código | Código interno del producto | No | ARE-01 |
| Nombre | Nombre del producto | Sí | ARENA |
:::

## Buscar, editar y eliminar

- Para buscar, escribe en el buscador («Buscar por nombre…»).
- Para corregir, haz clic en **Editar** en la fila, cambia los datos y guarda.
- Para borrar, haz clic en **Eliminar** y confirma en **Confirmar eliminación**. Esta acción no se puede deshacer.

## Reglas y validaciones

- Los nombres y códigos se guardan en MAYÚSCULAS automáticamente.
- No puede haber dos registros con el mismo valor. Si ya existe verás «Ya existe un registro de …».
- No puedes eliminar un registro que ya usan remisiones u otros datos: verás «El registro no se pudo guardar por un conflicto de datos (posible duplicado o referencia en uso).»

## Errores comunes

| Situación | Solución |
|---|---|
| El botón **Nuevo producto** está deshabilitado | Tu rol no puede crear en este catálogo. |
| Los botones **Editar** y **Eliminar** están deshabilitados | Solo el Administrador edita o elimina. |
| «… es obligatorio.» | Ingresa la información del campo marcado como obligatorio. |
