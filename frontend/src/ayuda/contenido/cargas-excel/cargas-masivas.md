---
titulo: Cargas masivas por Excel
descripcion: Cómo facturar, anular y actualizar facturas en bloque con un archivo .xlsx.
orden: 1
rol: todos
actualizado: 2026-11-16
---

## Para qué sirve

La pantalla **Cargas por Excel** procesa muchas filas de una vez: facturar remisiones, anular sus facturaciones o cambiar número y fecha de facturas.

## Quién puede usarla

Roles **Administrador** y **Operador**. Con **Solo Consulta** puedes ver las instrucciones, pero el botón **Procesar archivo** está deshabilitado.

## Cómo llegar

En **Facturación**, haz clic en **Cargas por Excel**. Para regresar, usa **Volver a facturas**.

## Paso a paso (igual para las tres pestañas)

:::pasos
1. Elige la pestaña: **Facturar masivo**, **Eliminar por Excel** o **Actualizar por Excel**.
2. Prepara el archivo .xlsx con las columnas exactas de esa pestaña (primera fila = encabezados).
3. Arrastra el archivo al recuadro «Arrastra un archivo .xlsx aquí, o haz clic para seleccionarlo.» o haz clic para elegirlo.
4. Haz clic en **Procesar archivo** (mientras trabaja dice «Procesando…»).
5. Revisa el resultado: **Total**, **Exitosas** y **Con error**. Si hay errores, revisa el **Detalle de filas con error**.
:::

@captura 01-cargas-excel.png | Pantalla Cargas por Excel en la pestaña Facturar masivo con el resultado de una carga de prueba

:::consejo
El **ID** de cada remisión lo encuentras en la primera columna del **Reporte general de remisiones** (ver [Reportes](/ayuda/reportes)).
:::

## Facturar masivo {#facturar-masivo}

:::campos
| Campo | Qué es | Obligatorio | Ejemplo |
|---|---|---|---|
| ID | Id de la remisión a facturar | Sí | 1520 |
| ES_PARCIAL | «S» o «N». Si es «N», factura el saldo total pendiente | Sí | N |
| VALOR_PARCIAL | Valor a facturar | Solo si ES_PARCIAL = «S» | 500000 |
| NUMERO_FACTURA | Número de factura (F-7-468 o F-1234) | Sí | F-7-468 |
| FECHA_FACTURA | Fecha en formato dd/mm/aaaa | Sí | 15/05/2026 |
:::

## Eliminar por Excel {#eliminar}

:::campos
| Campo | Qué es | Obligatorio | Ejemplo |
|---|---|---|---|
| ID | Id de la remisión cuyas facturaciones activas se anularán | Sí | 1520 |
:::

El saldo de la remisión se recalcula automáticamente. Las facturaciones quedan **Anuladas**, no se borran.

## Actualizar por Excel {#actualizar}

:::campos
| Campo | Qué es | Obligatorio | Ejemplo |
|---|---|---|---|
| NUMERO_FACTURA_ACTUAL | Número de la factura existente a modificar | Sí | F-7-468 |
| NUMERO_FACTURA_NUEVO | Número nuevo; vacío para no cambiarlo | No | F-7-469 |
| FECHA_FACTURA_NUEVA | Fecha nueva dd/mm/aaaa; vacía para no cambiarla | No | 16/05/2026 |
:::

## Reglas y validaciones

- Solo se aceptan archivos **.xlsx** de máximo **10 MB**.
- Cada fila se procesa por separado: las filas buenas se guardan aunque otras tengan error.
- Las reglas son las mismas que en pantalla: formato del número de factura, valor parcial mayor que 0 y no mayor que el saldo, remisión con productos.

## Errores comunes

| Mensaje | Solución |
|---|---|
| «Solo se aceptan archivos de Excel con extensión .xlsx.» | Guarda el archivo como «Libro de Excel (.xlsx)». |
| «El archivo supera el tamaño máximo permitido (10 MB).» | Divide el archivo en varios más pequeños. |
| «El archivo no es un Excel .xlsx válido…» | Ábrelo en Excel y guárdalo de nuevo como .xlsx (no basta con cambiar la extensión). |
| Filas en **Con error** | Lee el motivo de cada fila en el detalle, corrige solo esas filas y vuelve a cargarlas. |
