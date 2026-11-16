---
titulo: Vehículos y cama baja
descripcion: Cómo registrar los activos (vehículos, cama baja, trailer, volco) y bloquearlos.
orden: 1
rol: todos
actualizado: 2026-11-16
---

## Para qué sirve

La pantalla **Activos** guarda los vehículos y remolques con su placa. Son las opciones de los campos **Vehículo** y **Cama baja / Trailer / Volco** de la remisión.

## Quién puede usarla

Todos los roles pueden consultarla. Crear, editar y bloquear requiere el rol **Administrador** u **Operador**.

## Crear un activo

:::pasos
1. En el menú, en **Datos**, haz clic en **Activos**.
2. Haz clic en **Nuevo activo**.
3. Escribe la **Placa**, el **Tipo de activo** y la **Clase**.
4. Elige la **Empresa** propietaria.
5. Si aplica, marca **¿Es de segunda mano?**.
6. Haz clic en **Guardar**.
:::

@captura 01-nuevo-activo.png | Ventana Nuevo activo con una placa ficticia y tipo CAMA BAJA

:::campos
| Campo | Qué es | Obligatorio | Ejemplo |
|---|---|---|---|
| Placa | Placa del vehículo o remolque | Sí | ABC123 |
| Tipo de activo | Qué es | Sí | VEHÍCULO · CAMA BAJA |
| Clase | Clase de vehículo | Sí | TRACTOCAMIÓN · VOLQUETA |
| Empresa | Tercero propietario | Sí | EMPRESA DE PRUEBA S.A.S. |
| ¿Es de segunda mano? | Si el activo se compró usado | No | Sin marcar |
:::

## Buscar, editar y bloquear

- Busca con «Buscar por placa…».
- Haz clic en **Editar** en la fila para corregir.
- Haz clic en **Bloquear** (o **Desbloquear**) y confirma en **Confirmar bloqueo** / **Confirmar desbloqueo**. La columna **Estado** muestra **Activo** o **Bloqueado**.

:::nota
El estado **Bloqueado** es una marca informativa: hoy no impide elegir el activo en una remisión.
:::

## Reglas y validaciones

- «La placa es obligatoria.», «El tipo de activo es obligatorio.», «La clase es obligatoria.» y «Selecciona una empresa.» aparecen si faltan esos datos.
- Placa, tipo y clase se guardan en MAYÚSCULAS.
- No puede haber dos activos con la misma placa.

## Errores comunes

| Situación | Solución |
|---|---|
| La empresa no aparece | Créala primero en [Terceros](/ayuda/terceros). |
| La placa no aparece en **Vehículo** de la remisión | Revisa que el activo esté creado con esa placa exacta. |
