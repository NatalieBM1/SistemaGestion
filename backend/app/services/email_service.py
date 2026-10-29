"""Servicio de envío de correos transaccionales (SMTP).

Uso:
    from app.services.email_service import enviar_codigo_recuperacion
    enviar_codigo_recuperacion(email="usuario@empresa.com", nombre="Juan", codigo="482913")

Lanza ValueError si las variables SMTP no están configuradas en el .env.
Lanza smtplib.SMTPException (u otras de red) si falla el envío.
"""
import smtplib
import textwrap
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from app.core.config import settings


def smtp_configurado() -> bool:
    return bool(settings.smtp_host and settings.smtp_user and settings.smtp_password)


def enviar_codigo_recuperacion(*, email: str, nombre: str, codigo: str) -> None:
    """Envía un correo con el código de verificación para recuperar la contraseña.

    Args:
        email: Dirección destino.
        nombre: Nombre del usuario para personalizar el saludo.
        codigo: Código numérico de 6 dígitos.

    Raises:
        ValueError: Si SMTP no está configurado en las variables de entorno.
        smtplib.SMTPException: Si el servidor rechaza la conexión o el envío.
    """
    if not smtp_configurado():
        raise ValueError(
            "El servidor de correo no está configurado. "
            "Completa SMTP_HOST, SMTP_USER y SMTP_PASSWORD en el archivo .env."
        )

    minutos = settings.reset_token_expire_minutes
    from_addr = f"{settings.smtp_from_name} <{settings.smtp_from_email or settings.smtp_user}>"

    # ── Cuerpo HTML ────────────────────────────────────────────────────────────
    html = textwrap.dedent(f"""\
        <!DOCTYPE html>
        <html lang="es">
        <head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1"></head>
        <body style="margin:0;padding:0;background:#f0f4ff;font-family:Arial,Helvetica,sans-serif;">
          <table width="100%" cellpadding="0" cellspacing="0" style="background:#f0f4ff;padding:32px 16px;">
            <tr><td align="center">
              <table width="520" cellpadding="0" cellspacing="0"
                     style="background:#ffffff;border-radius:16px;overflow:hidden;
                            box-shadow:0 4px 24px rgba(47,95,224,0.12);">
                <!-- Cabecera azul -->
                <tr>
                  <td style="background:linear-gradient(135deg,#000079,#2f5fe0);
                             padding:28px 36px;text-align:center;">
                    <p style="margin:0;color:rgba(255,255,255,0.75);font-size:13px;
                               letter-spacing:0.06em;text-transform:uppercase;">
                      Sistema de Remisiones
                    </p>
                    <h1 style="margin:8px 0 0;color:#ffffff;font-size:22px;font-weight:700;">
                      Recuperación de contraseña
                    </h1>
                  </td>
                </tr>
                <!-- Cuerpo -->
                <tr>
                  <td style="padding:36px 36px 28px;">
                    <p style="margin:0 0 16px;color:#1b2a7a;font-size:15px;line-height:1.5;">
                      Hola, <strong>{nombre}</strong>.
                    </p>
                    <p style="margin:0 0 24px;color:#4a5578;font-size:14px;line-height:1.6;">
                      Recibimos una solicitud para restablecer la contraseña de tu cuenta.
                      Usa el código de verificación que aparece a continuación.
                    </p>
                    <!-- Código destacado -->
                    <div style="text-align:center;margin:0 0 28px;">
                      <span style="display:inline-block;padding:18px 40px;
                                   background:#eef2ff;border-radius:12px;
                                   font-size:38px;font-weight:700;letter-spacing:0.22em;
                                   color:#000079;border:2px dashed #a5b4fc;">
                        {codigo}
                      </span>
                    </div>
                    <p style="margin:0 0 8px;color:#4a5578;font-size:13px;line-height:1.5;text-align:center;">
                      Este código es válido por <strong>{minutos} minutos</strong>.
                    </p>
                    <p style="margin:0;color:#9aa4c4;font-size:12px;line-height:1.5;text-align:center;">
                      Si no solicitaste este cambio, ignora este mensaje.
                      Tu contraseña actual permanece segura.
                    </p>
                  </td>
                </tr>
                <!-- Pie -->
                <tr>
                  <td style="background:#f8f9ff;border-top:1px solid #e8edff;
                             padding:16px 36px;text-align:center;">
                    <p style="margin:0;color:#9aa4c4;font-size:11px;">
                      Transportes Guerreros &amp; Guerreros S.A.S.
                    </p>
                  </td>
                </tr>
              </table>
            </td></tr>
          </table>
        </body>
        </html>
    """)

    # Texto plano (fallback)
    texto = textwrap.dedent(f"""\
        Recuperación de contraseña — Sistema de Remisiones

        Hola, {nombre}.

        Tu código de verificación es: {codigo}

        Este código es válido por {minutos} minutos.

        Si no solicitaste este cambio, ignora este mensaje.
    """)

    # ── Armar mensaje MIME ─────────────────────────────────────────────────────
    msg = MIMEMultipart("alternative")
    msg["Subject"] = "Código de recuperación de contraseña"
    msg["From"] = from_addr
    msg["To"] = email
    msg.attach(MIMEText(texto, "plain", "utf-8"))
    msg.attach(MIMEText(html, "html", "utf-8"))

    # ── Enviar via SMTP con STARTTLS ───────────────────────────────────────────
    with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=15) as server:
        server.ehlo()
        server.starttls()
        server.ehlo()
        server.login(settings.smtp_user, settings.smtp_password)
        server.sendmail(from_addr, [email], msg.as_string())
