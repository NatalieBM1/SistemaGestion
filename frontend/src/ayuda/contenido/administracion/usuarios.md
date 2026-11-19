---
titulo: Usuarios
descripcion: Crear usuarios, asignar roles, desactivar cuentas y restablecer contraseñas.
orden: 1
rol: administrador
actualizado: 2026-11-16
---

## Para qué sirve

La pantalla **Usuarios** administra quién puede entrar al sistema y con qué roles.

## Quién puede usarla

Solo usuarios con el permiso de administrar usuarios (rol **Administrador**).

## Crear un usuario

:::pasos
1. En el menú, en **Análisis**, haz clic en **Administración** y luego en **Usuarios**.
2. Haz clic en **Nuevo usuario**.
3. Escribe **Nombre**, **Email** y, si la tienes, la **Identificación (cédula)**.
4. Escribe la **Contraseña** inicial.
5. Deja **Activo** encendido.
6. Marca uno o varios **Roles**.
7. Haz clic en **Guardar**. Verás «Usuario '…' guardado correctamente.»
8. Entrega al usuario su correo y contraseña por un medio seguro.
:::

@captura 01-nuevo-usuario.png | Ventana Nuevo usuario con datos ficticios y el rol Operador marcado

:::campos
| Campo | Qué es | Obligatorio | Ejemplo |
|---|---|---|---|
| Nombre | Nombre completo | Sí | USUARIO DE PRUEBA |
| Email | Correo para iniciar sesión | Sí | usuario@empresa.com |
| Identificación (cédula) | Sale en los reportes como «ID del usuario» y en el recibo como CC No. Si se deja vacía, esa columna queda vacía. | No | 1000000000 |
| Contraseña | Contraseña inicial | Sí (al crear) | (una contraseña segura) |
| Activo | Si el usuario puede iniciar sesión | — | Encendido |
| Roles | Administrador, Operador o Solo Consulta | — | Operador |
:::

## Editar o desactivar un usuario {#desactivar}

:::pasos
1. Busca al usuario («Buscar por nombre o email…»).
2. Haz clic en **Editar**.
3. Cambia los datos o los roles. Para desactivarlo, apaga **Activo**.
4. Haz clic en **Guardar**.
:::

Un usuario desactivado aparece con estado **Inactivo**, no puede iniciar sesión y sus sesiones abiertas se cierran. Sus remisiones y facturaciones se conservan.

## Restablecer la contraseña de un usuario {#cambiar-contrasena}

:::pasos
1. En la fila del usuario, haz clic en **Cambiar contraseña**.
2. Escribe la **Nueva contraseña**.
3. Haz clic en **Guardar**. Verás «Contraseña de '…' actualizada correctamente.»
:::

Las sesiones abiertas de ese usuario se cierran: deberá entrar con la contraseña nueva y, al entrar, el sistema le pedirá **cambiarla** antes de dejarle usar cualquier otra pantalla (ver [Cambio obligatorio al entrar](/ayuda/primeros-pasos/recuperar-y-cambiar-contrasena#obligatorio)). Si cambias tu propia contraseña desde aquí no se te pide de nuevo.

En el sistema en producción, las cuentas nuevas también deben cambiar la contraseña al primer ingreso.

:::nota
Úsalo solo cuando la persona no pueda hacerlo por su cuenta (por ejemplo, si no tiene acceso a su correo). Cada usuario puede [recuperar](/ayuda/primeros-pasos/recuperar-y-cambiar-contrasena#recuperar) o [cambiar](/ayuda/primeros-pasos/recuperar-y-cambiar-contrasena#cambiar) su propia contraseña sin ayuda.
:::

## Activar la cuenta de un usuario histórico {#activar-historico}

Los usuarios **históricos** son las personas que crearon remisiones en el Excel anterior. Aparecen con estado **Inactivo** y, en Email, «Histórico, sin acceso». Para darles acceso **no crees un usuario nuevo**: activa el que ya existe, así sus remisiones quedan a su nombre.

:::pasos
1. En la fila del usuario histórico, haz clic en **Activar cuenta**.
2. Revisa la **Identificación**, escribe el **Correo** y elige el **Rol**.
3. Haz clic en **Activar cuenta**.
4. Copia la **Contraseña temporal** que aparece y entrégala a la persona por un canal seguro. Se muestra **una sola vez**.
5. Haz clic en **Listo**.
:::

Al entrar con esa contraseña, el sistema le pedirá cambiarla antes de usar cualquier otra pantalla.

:::importante
A un usuario histórico no se le puede poner correo, contraseña ni roles con **Editar**: solo con **Activar cuenta**, que genera una contraseña aleatoria. Si pierdes la contraseña temporal antes de entregarla, usa **Cambiar contraseña** en su fila (también le pedirá cambiarla al entrar).
:::

## Reglas y validaciones

- No puede haber dos usuarios con el mismo email («Ya existe un usuario con email …»).
- «El nombre es obligatorio.», «El email es obligatorio.» y «La contraseña es obligatoria.» aparecen si faltan.
- No puedes quitarte a ti mismo todos los roles que dan acceso a Administración: el botón **Guardar** se deshabilita y verás el aviso «Estás editando tu propio usuario…».
- Usa contraseñas de al menos 8 caracteres, aunque este formulario no lo exige.

:::importante
No compartas contraseñas por chat ni correo sin cifrar. Nunca escribas contraseñas en documentos compartidos.
:::

## Errores comunes

| Situación | Solución |
|---|---|
| El usuario dice que no puede entrar | Revisa que esté **Activo** y restablece su contraseña. |
| CC No sale en blanco en el recibo | Agrega la **Identificación (cédula)** del usuario que creó la remisión. |
