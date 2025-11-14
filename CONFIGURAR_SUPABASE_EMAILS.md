# Configuración de Emails de Supabase

## Problema
Los emails de confirmación de Supabase se ven feos y la página de redirección después de confirmar también es horrible.

## Solución

### 1. Configurar URL de Redirección en Supabase

1. Ve a tu proyecto en Supabase Dashboard
2. Ve a **Authentication** > **URL Configuration**
3. En **Redirect URLs**, agrega:
   - Para desarrollo: `http://localhost:3000/auth/callback`
   - Para producción: `https://tu-dominio.com/auth/callback`
4. Guarda los cambios

### 2. Personalizar Plantillas de Email (Opcional)

Para personalizar los emails de confirmación de Supabase:

1. Ve a **Authentication** > **Email Templates**
2. Selecciona la plantilla que quieres personalizar (ej: "Confirm signup")
3. Puedes personalizar:
   - El asunto del email
   - El contenido HTML del email
   - Variables disponibles: `{{ .ConfirmationURL }}`, `{{ .Email }}`, etc.

**Ejemplo de plantilla personalizada:**

```html
<h2>Bienvenido a Codex Trader</h2>
<p>Hola,</p>
<p>Gracias por registrarte en Codex Trader. Para confirmar tu cuenta, haz clic en el siguiente enlace:</p>
<p><a href="{{ .ConfirmationURL }}">Confirmar mi cuenta</a></p>
<p>Si no solicitaste este registro, puedes ignorar este email.</p>
<p>Saludos,<br>El equipo de Codex Trader</p>
```

### 3. Configurar Site URL

1. Ve a **Authentication** > **URL Configuration**
2. En **Site URL**, configura:
   - Desarrollo: `http://localhost:3000`
   - Producción: `https://tu-dominio.com`

### 4. Verificar que la Página de Callback Funcione

La página `/auth/callback` ya está creada y debería:
- Mostrar un mensaje de carga mientras se procesa la confirmación
- Redirigir automáticamente a `/app` después de confirmar
- Enviar el email de bienvenida al backend cuando se confirme

## Notas Importantes

- Los emails de Supabase se envían desde `noreply@mail.app.supabase.io` por defecto
- Para personalizar completamente los emails, necesitarías usar un servicio de email personalizado (SMTP custom)
- La página de callback ya está implementada en `/app/auth/callback/page.tsx`

