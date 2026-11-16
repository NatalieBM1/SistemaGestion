---
titulo: Departamentos y municipios
descripcion: Cómo consultar, crear y copiar las ubicaciones con su código DANE.
orden: 1
rol: todos
actualizado: 2026-11-16
---

## Para qué sirve

La pantalla **Ubicaciones** guarda los departamentos y municipios con su **código DANE**. Los municipios son las opciones de **Ubicación de origen** y **Ubicación de destino** de la remisión y del **Municipio** de los terceros.

## Quién puede usarla

Todos los roles pueden consultarla. Crear y editar requiere el rol **Administrador** u **Operador**.

## Consultar

:::pasos
1. En el menú, en **Datos**, haz clic en **Ubicaciones**.
2. En el panel **Departamentos**, busca («Buscar departamento…») y haz clic en un departamento.
3. A la derecha aparecen sus municipios. Puedes buscar con «Buscar municipio…».
:::

@captura 01-ubicaciones.png | Pantalla Ubicaciones con un departamento seleccionado y sus municipios

## Crear un departamento o municipio

:::pasos
1. En el panel correspondiente, haz clic en **Nuevo**. Para un municipio, primero elige el departamento.
2. Escribe el **Código DANE** y el **Nombre**.
3. Haz clic en **Guardar**.
:::

:::campos
| Campo | Qué es | Obligatorio | Ejemplo |
|---|---|---|---|
| Código DANE | Código oficial del DANE | Sí | 05 (departamento) · 05001 (municipio) |
| Nombre | Nombre en MAYÚSCULAS | Sí | MUNICIPIO A |
:::

## Copiar una ubicación

En cada fila hay un botón de copiar. En los municipios copia el texto «MUNICIPIO, DEPARTAMENTO», listo para pegar en otro documento. Al copiar aparece el aviso **Copiado**.

## Reglas y validaciones

- El código DANE no se puede repetir.
- Los nombres se guardan en MAYÚSCULAS.
- Editar con el ícono de lápiz requiere permiso de escritura de ubicaciones.

## Errores comunes

| Situación | Solución |
|---|---|
| «Selecciona un departamento» | Haz clic en un departamento del panel izquierdo para ver sus municipios. |
| No encuentro el municipio en la remisión | Revisa que exista en esta pantalla, con su departamento correcto. |
