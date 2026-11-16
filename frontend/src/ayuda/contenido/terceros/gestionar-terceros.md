---
titulo: Gestionar terceros
descripcion: Cómo crear, buscar y editar clientes, conductores, proveedores y demás terceros.
orden: 1
rol: todos
actualizado: 2026-11-16
---

## Para qué sirve

La pantalla **Terceros** («Clientes, conductores, proveedores y demás terceros del sistema.») guarda las personas y empresas que aparecen en las remisiones: el **Cliente**, el **Conductor** y la **Empresa** de los activos.

## Quién puede usarla

Todos los roles pueden consultarla. Crear y editar requiere el rol **Administrador** u **Operador**.

## Crear un tercero

:::pasos
1. En el menú, en **Datos**, haz clic en **Terceros**.
2. Haz clic en **Nuevo tercero**.
3. Escribe la **Identificación** y el **Nombre**.
4. Elige el **Municipio** e ingresa los demás datos que tengas.
5. Marca uno o varios **Tipos** (por ejemplo CLIENTE o CONDUCTOR).
6. Si es conductor, marca **¿Tiene licencia?** y escribe la **Fecha de vencimiento de la licencia**.
7. Haz clic en **Guardar**.
:::

@captura 01-nuevo-tercero.png | Ventana Nuevo tercero con datos ficticios de un cliente de prueba

:::campos
| Campo | Qué es | Obligatorio | Ejemplo |
|---|---|---|---|
| Identificación | NIT o cédula, sin puntos | Sí | 900123456 |
| Nombre | Nombre o razón social; se guarda en MAYÚSCULAS | Sí | CLIENTE DE PRUEBA S.A.S. |
| Dirección | Dirección del tercero | No | CALLE 1 # 2-3 |
| Municipio | Municipio, buscado por nombre | Sí | MUNICIPIO A |
| Email | Correo de contacto | No | contacto@ejemplo.com |
| Teléfono | Teléfono de contacto | No | 3000000000 |
| Régimen | Régimen tributario | No | COMÚN |
| ¿Tiene licencia? | Si el conductor tiene licencia de conducción | No | Marcado |
| Fecha de vencimiento de la licencia | Hasta cuándo es válida | No | 31/12/2027 |
| Tipos | Clasificación del tercero (del catálogo Tipos de tercero) | No | CLIENTE |
:::

## Buscar y editar

- Escribe en «Buscar por nombre o identificación…» o filtra con **Todos los tipos**.
- Haz clic en **Editar** en la fila, corrige y guarda.

## Reglas y validaciones

- «La identificación es obligatoria.» y «El nombre es obligatorio.» aparecen si dejas esos campos vacíos.
- Sin municipio verás «Selecciona un municipio.»
- El nombre se convierte a MAYÚSCULAS automáticamente.
- No puede haber dos terceros con la misma identificación.
- Para que un tercero aparezca como **Conductor** en la remisión, debe tener el tipo de conductor.

## Importación

La aplicación **no tiene una pantalla para importar terceros** desde Excel: se crean uno por uno con **Nuevo tercero**.

## Errores comunes

| Situación | Solución |
|---|---|
| El municipio no aparece en la lista | Créalo primero en [Ubicaciones](/ayuda/ubicaciones). |
| El tercero no aparece en **Conductor** de la remisión | Edítalo y marca el tipo de conductor en **Tipos**. |
| «Sin resultados en terceros» | Revisa el texto de búsqueda o elige **Todos los tipos**. |
