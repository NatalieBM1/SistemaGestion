---
titulo: Prefijo y consecutivo
descripcion: Cómo se numeran las remisiones con prefijos automáticos y manuales (GTM).
orden: 4
rol: todos
actualizado: 2026-11-16
---

## Para qué sirve

Cada remisión tiene un **número** formado por un **prefijo** y un consecutivo, por ejemplo **GTS-6528**. El prefijo indica la serie.

## Prefijo automático

El sistema asigna el siguiente número de la serie al guardar. En el formulario, el campo **Número de consecutivo** dice «Automático».

:::pasos
1. En **Prefijo**, elige un prefijo automático (por ejemplo GTS).
2. Ingresa el resto de la información de la pestaña **Datos**.
3. Haz clic en **Guardar remisión**. El número queda asignado.
:::

## Prefijo manual (remisión de papel) {#manual}

Los prefijos marcados como **Es manual (remisión de papel)**, como **GTM**, corresponden a talonarios físicos: el número lo escribes tú.

:::pasos
1. En **Prefijo**, elige el prefijo manual (por ejemplo GTM).
2. Aparece **Número de remisión (manual)**. Escribe el número del talonario, por ejemplo **00123**.
3. Haz clic en **Guardar remisión**.
:::

@captura 01-prefijo-manual.png | Pestaña Datos con prefijo GTM elegido y el campo Número de remisión (manual) visible

## Reglas y validaciones

- El número no se puede repetir dentro del mismo prefijo. **00123** y **123** se consideran el mismo número.
- Si el número ya existe verás, por ejemplo, «Ya existe la remisión GTS-6528.»
- En pantalla el número se muestra sin ceros a la izquierda (GTS-6528). En los reportes de Excel se muestra con 6 dígitos (GTS-006528) para que se puedan volver a importar.
- Solo un **Administrador** crea o modifica prefijos. Ver [Prefijos](/ayuda/catalogos/prefijos).

## Errores comunes

| Mensaje | Solución |
|---|---|
| «Ya existe la remisión …» | Revisa el talonario: ese número ya se registró. Busca la remisión existente en el listado. |
| Me pide número manual y el prefijo debería ser automático | El prefijo está marcado como manual en el catálogo. Pide a un administrador que lo revise. |
