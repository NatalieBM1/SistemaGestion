---
titulo: Unidades de medida
descripcion: Unidades con que se miden las cantidades de los productos.
orden: 5
rol: todos
actualizado: 2026-11-16
---

## Para qué sirve

Las unidades que se eligen en **Unidad de medida** al agregar un producto a la remisión.

## Quién puede usarlo

Todos los roles pueden consultarlo. Los roles **Administrador** y **Operador** pueden crear registros; solo el **Administrador** puede editarlos o eliminarlos.

## Crear un registro

:::pasos
1. En el menú, en **Datos**, haz clic en **Catálogos**.
2. Abre la pestaña **Unidades de medida**.
3. Haz clic en **Nuevo unidad de medida**.
4. Ingresa la información en los campos.
5. Haz clic en **Guardar**. Verás «Unidad de medida creado correctamente.»
:::

@captura 01-unidades-de-medida.png | Pestaña Unidades de medida de Catálogos con registros de prueba y el botón Nuevo unidad de medida

:::campos
| Campo | Qué es | Obligatorio | Ejemplo |
|---|---|---|---|
| Nombre | Nombre de la unidad | Sí | METRO CÚBICO |
:::

## Buscar, editar y eliminar

- Para buscar, escribe en el buscador («Buscar por nombre…»).
- Para corregir, haz clic en **Editar** en la fila, cambia los datos y guarda.
- Para borrar, haz clic en **Eliminar** y confirma en **Confirmar eliminación**. Esta acción no se puede deshacer.

## Reglas y validaciones

- Los nombres y códigos se guardan en MAYÚSCULAS automáticamente.
- No puede haber dos registros con el mismo valor. Si ya existe verás «Ya existe un registro de …».
- No puedes eliminar un registro que ya usan remisiones u otros datos: verás «El registro no se pudo guardar por un conflicto de datos (posible duplicado o referencia en uso).»
- **METRO CÚBICO** aparece de primera en las listas y en pantalla y en el recibo se muestra abreviado como **m³**. En los reportes de Excel se conserva el nombre del catálogo.

## Errores comunes

| Situación | Solución |
|---|---|
| El botón **Nuevo unidad de medida** está deshabilitado | Tu rol no puede crear en este catálogo. |
| Los botones **Editar** y **Eliminar** están deshabilitados | Solo el Administrador edita o elimina. |
| «… es obligatorio.» | Ingresa la información del campo marcado como obligatorio. |
