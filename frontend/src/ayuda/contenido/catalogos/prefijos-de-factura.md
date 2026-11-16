---
titulo: Prefijos de factura
descripcion: Prefijos registrados para los números de factura.
orden: 6
rol: todos
actualizado: 2026-11-16
---

## Para qué sirve

Lista de referencia de los prefijos de factura que usa la empresa.

## Quién puede usarlo

Todos los roles pueden consultarlo. Los roles **Administrador** y **Operador** pueden crear registros; solo el **Administrador** puede editarlos o eliminarlos.

## Crear un registro

:::pasos
1. En el menú, en **Datos**, haz clic en **Catálogos**.
2. Abre la pestaña **Prefijos de factura**.
3. Haz clic en **Nuevo prefijo de factura**.
4. Ingresa la información en los campos.
5. Haz clic en **Guardar**. Verás «Prefijo de factura creado correctamente.»
:::

@captura 01-prefijos-de-factura.png | Pestaña Prefijos de factura de Catálogos con registros de prueba y el botón Nuevo prefijo de factura

:::campos
| Campo | Qué es | Obligatorio | Ejemplo |
|---|---|---|---|
| Código | Prefijo de la factura | Sí | F |
:::

## Buscar, editar y eliminar

- Para buscar, escribe en el buscador («Buscar por código…»).
- Para corregir, haz clic en **Editar** en la fila, cambia los datos y guarda.
- Para borrar, haz clic en **Eliminar** y confirma en **Confirmar eliminación**. Esta acción no se puede deshacer.

## Reglas y validaciones

- Los nombres y códigos se guardan en MAYÚSCULAS automáticamente.
- No puede haber dos registros con el mismo valor. Si ya existe verás «Ya existe un registro de …».
- No puedes eliminar un registro que ya usan remisiones u otros datos: verás «El registro no se pudo guardar por un conflicto de datos (posible duplicado o referencia en uso).»
- El número de factura que se escribe al facturar debe cumplir el formato del sistema (ver [Formato del número de factura](/ayuda/facturacion/formato-de-factura)).

## Errores comunes

| Situación | Solución |
|---|---|
| El botón **Nuevo prefijo de factura** está deshabilitado | Tu rol no puede crear en este catálogo. |
| Los botones **Editar** y **Eliminar** están deshabilitados | Solo el Administrador edita o elimina. |
| «… es obligatorio.» | Ingresa la información del campo marcado como obligatorio. |
