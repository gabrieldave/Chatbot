"""
Módulo de utilidades para envío de emails usando SMTP.
Proporciona funciones para enviar emails genéricos y notificaciones al administrador.
"""
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

# Obtener variables de entorno de SMTP
SMTP_HOST = os.getenv("SMTP_HOST", "smtp.gmail.com").strip('"').strip("'").strip()
SMTP_PORT = int(os.getenv("SMTP_PORT", "587").strip('"').strip("'").strip())
SMTP_USER = os.getenv("SMTP_USER", "").strip('"').strip("'").strip()
SMTP_PASS = os.getenv("SMTP_PASS", "").strip('"').strip("'").strip()
EMAIL_FROM = os.getenv("EMAIL_FROM", "").strip('"').strip("'").strip()
ADMIN_EMAIL = os.getenv("ADMIN_EMAIL", "").strip('"').strip("'").strip()

# Verificar si SMTP está configurado
SMTP_AVAILABLE = bool(SMTP_HOST and SMTP_USER and SMTP_PASS and EMAIL_FROM)

if not SMTP_AVAILABLE:
    print("WARNING: SMTP no está completamente configurado. Las funciones de email no estarán disponibles.")
    print("   Variables requeridas: SMTP_HOST, SMTP_USER, SMTP_PASS, EMAIL_FROM")


def send_email(
    to: str,
    subject: str,
    html: str,
    text: Optional[str] = None
) -> bool:
    """
    Envía un email usando SMTP.
    
    Esta función es robusta y no lanza excepciones para no bloquear el flujo principal.
    Si falla, solo registra el error en los logs.
    
    Args:
        to: Dirección de email del destinatario
        subject: Asunto del email
        html: Contenido HTML del email
        text: Contenido en texto plano (opcional, se genera desde HTML si no se proporciona)
        
    Returns:
        True si el email se envió correctamente, False en caso contrario
    """
    if not SMTP_AVAILABLE:
        print(f"WARNING: No se puede enviar email: SMTP no está configurado")
        return False
    
    if not to or not subject or not html:
        print(f"WARNING: No se puede enviar email: faltan parámetros requeridos (to, subject, html)")
        return False
    
    try:
        # Crear mensaje
        msg = MIMEMultipart('alternative')
        msg['From'] = EMAIL_FROM
        msg['To'] = to
        msg['Subject'] = subject
        
        # Agregar contenido en texto plano si se proporciona, sino generar desde HTML
        if text:
            part_text = MIMEText(text, 'plain', 'utf-8')
            msg.attach(part_text)
        else:
            # Generar texto plano básico desde HTML (remover tags HTML simples)
            import re
            text_content = re.sub(r'<[^>]+>', '', html)
            text_content = text_content.replace('&nbsp;', ' ')
            text_content = text_content.replace('&amp;', '&')
            text_content = text_content.replace('&lt;', '<')
            text_content = text_content.replace('&gt;', '>')
            part_text = MIMEText(text_content, 'plain', 'utf-8')
            msg.attach(part_text)
        
        # Agregar contenido HTML
        part_html = MIMEText(html, 'html', 'utf-8')
        msg.attach(part_html)
        
        # Conectar al servidor SMTP y enviar
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
            server.starttls()  # Habilitar encriptación TLS
            server.login(SMTP_USER, SMTP_PASS)
            server.send_message(msg)
        
        print(f"OK: Email enviado exitosamente a {to}: {subject}")
        print(f"    Thread ID: {os.getpid()}")
        return True
        
    except smtplib.SMTPAuthenticationError as e:
        print(f"ERROR: Error de autenticación SMTP: {e}")
        print(f"   Verifica que SMTP_PASS sea una 'app password' de Gmail, no la contraseña normal")
        return False
    except smtplib.SMTPException as e:
        print(f"ERROR: Error SMTP al enviar email: {e}")
        return False
    except Exception as e:
        print(f"ERROR: Error inesperado al enviar email: {e}")
        return False


def send_admin_email(
    subject: str,
    html: str,
    text: Optional[str] = None
) -> bool:
    """
    Envía un email al administrador.
    
    Args:
        subject: Asunto del email
        html: Contenido HTML del email
        text: Contenido en texto plano (opcional)
        
    Returns:
        True si el email se envió correctamente, False en caso contrario
    """
    if not ADMIN_EMAIL:
        print("WARNING: ADMIN_EMAIL no está configurado, no se puede enviar email al administrador")
        return False
    
    return send_email(
        to=ADMIN_EMAIL,
        subject=subject,
        html=html,
        text=text
    )

