---
titulo: Recuperar y cambiar la contraseña
descripcion: Cómo recuperar tu contraseña si la olvidaste y cómo cambiarla desde tu cuenta.
orden: 4
rol: todos
actualizado: 2026-11-16
---

## Quién puede usarlo

Cada persona, con su **propia cuenta**. Todos los roles (Administrador, Operador y Solo Consulta) pueden recuperar y cambiar su contraseña. Nadie puede recuperar ni cambiar la contraseña de otra persona por estas opciones: el código llega solo al correo de la cuenta, y para cambiarla hay que conocer la contraseña actual.

| Situación | Qué usar |
|---|---|
| Olvidaste la contraseña y no puedes entrar | [Recuperar la contraseña](#recuperar), desde la pantalla de inicio de sesión. |
| Recuerdas la contraseña y quieres cambiarla | [Cambiar la contraseña](#cambiar), desde el menú de tu cuenta. |
| No tienes acceso a tu correo o el sistema no envía correos | Pide a un administrador que la restablezca (ver [Usuarios](/ayuda/administracion/usuarios#cambiar-contrasena)). |

## Recuperar la contraseña (si la olvidaste) {#recuperar}

:::pasos
1. En la pantalla **Iniciar sesión**, haz clic en **¿Olvidaste tu contraseña?**.
2. En **Correo**, escribe el correo de tu cuenta y haz clic en **Enviar código**.
3. Revisa tu correo: te llega un **código de verificación** de 6 dígitos.
4. Escribe el código en **Código de verificación**.
5. Escribe la contraseña nueva en **Nueva contraseña** y repítela en **Confirmar contraseña**.
6. Haz clic en **Cambiar contraseña**. Verás «Tu contraseña se actualizó correctamente.»
7. Haz clic en **Ir al inicio de sesión** y entra con la contraseña nueva.
:::

@captura 01-recuperar-contrasena.png | Pantalla de recuperación con el campo Correo y el botón Enviar código

:::campos
| Campo | Qué es | Obligatorio | Ejemplo |
|---|---|---|---|
| Correo | Correo de tu cuenta | Sí | usuario@empresa.com |
| Código de verificación | Código de 6 dígitos que llega al correo | Sí | 123456 |
| Nueva contraseña | Tu contraseña nueva | Sí | Mínimo 8 caracteres |
| Confirmar contraseña | La misma contraseña otra vez | Sí | (igual a la anterior) |
:::

### Reglas y validaciones {#reglas-recuperar}

- El código vence a los **15 minutos** y sirve **una sola vez**.
- Si escribes mal el código **5 veces**, ese código queda bloqueado y debes pedir uno nuevo.
- Pedir un código nuevo anula el anterior. Puedes pedir hasta 3 códigos por hora.
- El mensaje después de escribir el correo es siempre el mismo, exista o no la cuenta: así nadie puede averiguar qué correos están registrados.
- La nueva contraseña debe tener al menos **8 caracteres**.

### Errores comunes {#errores-recuperar}

| Mensaje o situación | Solución |
|---|---|
| No me llega el correo | Revisa la carpeta de correo no deseado. Espera un par de minutos. Si no llega, haz clic en **¿No recibiste el código? Volver a intentar**. Si sigue sin llegar, avisa al administrador. |
| «El código es incorrecto, ya venció o se bloqueó por demasiados intentos…» | Pide un código nuevo y úsalo dentro de los 15 minutos. |
| «La recuperación de contraseña no está disponible en este momento.» | El correo del sistema no está configurado. Pide al administrador que te restablezca la contraseña. |
| «Demasiados intentos…» | Espera el tiempo indicado antes de volver a intentar. |

### Qué pasa después {#despues-recuperar}

Se cierran todas las sesiones abiertas con la contraseña anterior, en cualquier equipo. Inicia sesión con la contraseña nueva.

## Cambiar la contraseña (si la recuerdas) {#cambiar}

:::pasos
1. En el menú de la izquierda, abajo, haz clic en la tarjeta con tu nombre y tu rol.
2. En el menú que se abre, haz clic en **Cambiar contraseña**.
3. En **Contraseña actual**, escribe la contraseña que usas hoy.
4. En **Nueva contraseña**, escribe la nueva (mínimo 8 caracteres).
5. Repítela en **Confirmar contraseña**.
6. Haz clic en **Guardar contraseña**. Verás «Tu contraseña se actualizó. Las sesiones abiertas en otros equipos se cerraron.»
:::

@captura 02-cambiar-contrasena.png | Ventana Cambiar contraseña abierta desde el menú de la cuenta, con los tres campos vacíos

:::campos
| Campo | Qué es | Obligatorio | Ejemplo |
|---|---|---|---|
| Contraseña actual | La contraseña con la que entraste | Sí | (la tuya) |
| Nueva contraseña | La contraseña que vas a usar desde ahora | Sí | Mínimo 8 caracteres |
| Confirmar contraseña | La nueva contraseña otra vez | Sí | (igual a la nueva) |
:::

:::consejo
El ícono del ojo en **Contraseña actual** muestra u oculta lo que escribiste en los tres campos.
:::

### Reglas y validaciones {#reglas-cambiar}

- La contraseña actual debe ser la correcta.
- La nueva debe tener al menos **8 caracteres** y ser **diferente** de la actual.
- **Nueva contraseña** y **Confirmar contraseña** deben coincidir.
- Por seguridad, después de varios intentos seguidos el sistema pide esperar un momento.

### Errores comunes {#errores-cambiar}

| Mensaje | Solución |
|---|---|
| «La contraseña actual no es correcta.» | Revisa la tecla Bloq Mayús y vuelve a escribirla. Si no la recuerdas, cierra sesión y usa [Recuperar la contraseña](#recuperar). |
| «La nueva contraseña debe tener al menos 8 caracteres.» | Escribe una contraseña más larga. |
| «La nueva contraseña debe ser diferente de la actual.» | Elige una contraseña distinta. |
| «Las contraseñas no coinciden.» | Escribe lo mismo en **Nueva contraseña** y **Confirmar contraseña**. |
| «Demasiados intentos…» | Espera el tiempo indicado antes de volver a intentar. |

### Qué pasa después {#despues-cambiar}

- En el equipo donde hiciste el cambio **sigues trabajando** sin volver a iniciar sesión.
- Las sesiones abiertas en **otros equipos** se cierran: allí tendrás que entrar con la contraseña nueva.

:::importante
Usa una contraseña que no uses en otros sitios y no la compartas con nadie, ni siquiera con el administrador.
:::
