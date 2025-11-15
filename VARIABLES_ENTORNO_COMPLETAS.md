# 🔐 Variables de Entorno Completas para el Backend

Este documento contiene **TODAS** las variables de entorno necesarias para el backend, organizadas por categoría y prioridad.

---

## 🔴 Variables OBLIGATORIAS (Sin estas, el backend NO funcionará)

### 1. Supabase (Base de datos y autenticación)

#### SUPABASE_SERVICE_KEY
```
SUPABASE_SERVICE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```
**Descripción:** Service Role Key de Supabase (NO uses la anon key)  
**Dónde encontrarla:**
- Ve a [Dashboard de Supabase](https://app.supabase.com)
- Selecciona tu proyecto
- Ve a **Settings** → **API**
- Copia el valor de **"service_role" key**

#### SUPABASE_URL (o SUPABASE_REST_URL o SUPABASE_DB_URL)
**Elige UNA de estas opciones:**

**Opción A: SUPABASE_URL (URL REST directa)**
```
SUPABASE_URL=https://eixvqedpyuybfywmdulg.supabase.co
```

**Opción B: SUPABASE_REST_URL (URL REST directa)**
```
SUPABASE_REST_URL=https://eixvqedpyuybfywmdulg.supabase.co
```

**Opción C: SUPABASE_DB_URL (URL de conexión PostgreSQL)**
```
SUPABASE_DB_URL=postgresql://postgres:password@db.xxx.supabase.co:5432/postgres
```

**Descripción:** URL de tu proyecto Supabase  
**Dónde encontrarla:**
- Ve a [Dashboard de Supabase](https://app.supabase.com)
- Selecciona tu proyecto
- Ve a **Settings** → **API**
- Copia el valor de **"Project URL"** (para SUPABASE_URL o SUPABASE_REST_URL)
- O ve a **Settings** → **Database** → **Connection string** (para SUPABASE_DB_URL)

---

### 2. Modelo de IA (Al menos UNA debe estar configurada)

**Elige UNA de estas opciones:**

#### Opción A: Deepseek (Recomendado - Más económico)
```
DEEPSEEK_API_KEY=sk-tu_api_key_de_deepseek_aqui
CHAT_MODEL=deepseek/deepseek-chat
```

#### Opción B: OpenAI
```
OPENAI_API_KEY=sk-proj-tu_api_key_de_openai_aqui
CHAT_MODEL=gpt-3.5-turbo
```

**Otras opciones de modelos:**
- `CHAT_MODEL=gpt-4` (GPT-4)
- `CHAT_MODEL=claude-3-opus-20240229` (Claude, requiere ANTHROPIC_API_KEY)
- `CHAT_MODEL=gemini/gemini-pro` (Gemini, requiere GOOGLE_API_KEY)

**⚠️ IMPORTANTE:** Solo configura **UNA** API key principal. Si configuras múltiples, el sistema usará la que esté disponible según la prioridad.

---

### 3. Frontend URL

```
FRONTEND_URL=http://localhost:3000
```

**Para producción, actualiza con la URL de tu frontend:**
```
FRONTEND_URL=https://tu-frontend.vercel.app
```

**Descripción:** URL del frontend para CORS y redirecciones

---

### 4. Email SMTP (Gmail)

```
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=todossomostr4ders@gmail.com
SMTP_PASS=kjhf biie tgrk wncz
EMAIL_FROM=Codex Trader <todossomostr4ders@gmail.com>
ADMIN_EMAIL=todossomostr4ders@gmail.com
```

**⚠️ IMPORTANTE sobre SMTP_PASS:**
- Debe ser una **"App Password"** de Gmail, NO tu contraseña normal
- **Cómo obtener una App Password:**
  1. Ve a [myaccount.google.com](https://myaccount.google.com)
  2. **Seguridad** → **Verificación en 2 pasos** (debe estar activada)
  3. **Contraseñas de aplicaciones** → **Generar nueva contraseña**
  4. Copia la contraseña generada (16 caracteres sin espacios)

**EMAIL_FROM:** Formato `Nombre <email@ejemplo.com>`  
**ADMIN_EMAIL:** Email donde recibirás notificaciones de admin (nuevos registros, pagos, etc.)

---

## 🟡 Variables OPCIONALES (Funcionalidades adicionales)

### 5. RAG (Búsqueda en documentos)

```
SUPABASE_DB_PASSWORD=tu_contraseña_de_postgres
```

**Descripción:** Contraseña de la base de datos PostgreSQL de Supabase  
**Dónde encontrarla:**
- Ve a [Dashboard de Supabase](https://app.supabase.com)
- Selecciona tu proyecto
- Ve a **Settings** → **Database**
- Copia la contraseña de la base de datos

**Nota:** Sin esta variable, el sistema RAG (búsqueda en documentos) no estará disponible, pero el resto del backend funcionará normalmente.

---

### 6. Stripe (Pagos y suscripciones)

**⚠️ Solo necesarias si usas Stripe para pagos**

```
STRIPE_SECRET_KEY=sk_live_tu_secret_key_aqui
STRIPE_WEBHOOK_SECRET=whsec_tu_webhook_secret_aqui
STRIPE_PRICE_ID_EXPLORER=price_tu_price_id_explorer
STRIPE_PRICE_ID_TRADER=price_tu_price_id_trader
STRIPE_PRICE_ID_PRO=price_tu_price_id_pro
STRIPE_PRICE_ID_INSTITUCIONAL=price_tu_price_id_institucional
STRIPE_FAIR_USE_COUPON_ID=FAIR_USE_20
```

**Dónde encontrarlas:**

**STRIPE_SECRET_KEY:**
- Ve a [Dashboard de Stripe](https://dashboard.stripe.com)
- **Developers** → **API keys**
- Copia la **"Secret key"** (usa `sk_live_...` para producción o `sk_test_...` para pruebas)

**STRIPE_WEBHOOK_SECRET:**
- Ve a [Dashboard de Stripe](https://dashboard.stripe.com)
- **Developers** → **Webhooks**
- Crea un webhook apuntando a: `https://tu-backend.railway.app/stripe/webhook`
- Copia el **"Signing secret"**

**STRIPE_PRICE_ID_*:**
- Ve a [Dashboard de Stripe](https://dashboard.stripe.com)
- **Products** → Selecciona cada plan → **Pricing**
- Copia el **"Price ID"** (empieza con `price_`)

**STRIPE_FAIR_USE_COUPON_ID:**
- Ve a [Dashboard de Stripe](https://dashboard.stripe.com)
- **Products** → **Coupons**
- Crea un cupón con 20% de descuento
- Copia el **"Coupon ID"**

---

### 7. Modelos de IA Adicionales (Opcionales)

```
ANTHROPIC_API_KEY=tu_api_key_de_anthropic
GOOGLE_API_KEY=tu_api_key_de_google
COHERE_API_KEY=tu_api_key_de_cohere
```

**Descripción:** API keys para modelos adicionales (Claude, Gemini, Cohere)  
**Nota:** Solo necesarias si quieres usar estos modelos además de Deepseek/OpenAI

---

## 🟢 Variables Automáticas (No necesitas configurarlas)

### PORT
```
PORT=8000
```

**Descripción:** Puerto donde corre el servidor  
**Nota:** Railway y otras plataformas proporcionan esta variable automáticamente. El código ya está configurado para usarla.

---

## 📋 Lista Completa para Copiar y Pegar

### Variables Obligatorias Mínimas

```env
# Supabase
SUPABASE_SERVICE_KEY=tu_service_key_aqui
SUPABASE_URL=https://tu-proyecto.supabase.co

# Modelo de IA (elige UNA opción)
DEEPSEEK_API_KEY=sk-tu_api_key_de_deepseek
CHAT_MODEL=deepseek/deepseek-chat

# O alternativamente:
# OPENAI_API_KEY=sk-proj-tu_api_key_de_openai
# CHAT_MODEL=gpt-3.5-turbo

# Frontend
FRONTEND_URL=http://localhost:3000

# Email SMTP
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=tu_email@gmail.com
SMTP_PASS=tu_app_password_de_gmail
EMAIL_FROM=Codex Trader <tu_email@gmail.com>
ADMIN_EMAIL=tu_email@gmail.com
```

### Variables Opcionales (RAG)

```env
SUPABASE_DB_PASSWORD=tu_contraseña_de_postgres
```

### Variables Opcionales (Stripe)

```env
STRIPE_SECRET_KEY=sk_live_tu_secret_key
STRIPE_WEBHOOK_SECRET=whsec_tu_webhook_secret
STRIPE_PRICE_ID_EXPLORER=price_xxx
STRIPE_PRICE_ID_TRADER=price_xxx
STRIPE_PRICE_ID_PRO=price_xxx
STRIPE_PRICE_ID_INSTITUCIONAL=price_xxx
STRIPE_FAIR_USE_COUPON_ID=FAIR_USE_20
```

### Variables Opcionales (Modelos Adicionales)

```env
ANTHROPIC_API_KEY=tu_api_key_de_anthropic
GOOGLE_API_KEY=tu_api_key_de_google
COHERE_API_KEY=tu_api_key_de_cohere
```

---

## 📝 Cómo Agregar Variables en Railway

1. Ve a tu proyecto en [Railway](https://railway.app)
2. Selecciona el servicio (backend)
3. Haz clic en la pestaña **"Variables"**
4. Haz clic en **"+ New Variable"**
5. Ingresa el **Name** y **Value**
6. Haz clic en **"Add"**
7. **Repite para cada variable**

**⚠️ IMPORTANTE:**
- No uses comillas en los valores (Railway las maneja automáticamente)
- Los nombres son **case-sensitive** (mayúsculas/minúsculas importan)
- Después de agregar variables, Railway reiniciará automáticamente el servicio

---

## ✅ Verificación

Después de agregar todas las variables:

1. **Revisa los logs en Railway:**
   - Ve a **Deployments** → Selecciona el último deployment → **View Logs**
   - No debería haber errores de "variable not found"
   - Debería mostrar: "✓ Iniciando servidor en puerto..."

2. **Prueba el endpoint:**
   - Ve a: `https://tu-proyecto.up.railway.app/docs`
   - Deberías ver la documentación de la API

3. **Verifica funcionalidades:**
   - Autenticación: Prueba registrarte o iniciar sesión
   - Chat: Prueba hacer una consulta
   - Email: Verifica que se envíen emails de bienvenida
   - Stripe (si está configurado): Prueba hacer una compra de prueba

---

## 🆘 Solución de Problemas

### Error: "Faltan variables de entorno obligatorias"

**Causa:** Faltan variables críticas (SUPABASE_SERVICE_KEY o API keys de IA)

**Solución:**
1. Verifica que `SUPABASE_SERVICE_KEY` esté configurada
2. Verifica que al menos una de estas esté configurada:
   - `DEEPSEEK_API_KEY`
   - `OPENAI_API_KEY`

### Error: "No se pudo determinar la URL REST de Supabase"

**Causa:** No hay ninguna variable de Supabase URL configurada

**Solución:**
Configura al menos una de estas:
- `SUPABASE_URL`
- `SUPABASE_REST_URL`
- `SUPABASE_DB_URL`

### Error: "SMTP no está completamente configurado"

**Causa:** Faltan variables de SMTP

**Solución:**
Configura todas estas variables:
- `SMTP_HOST`
- `SMTP_USER`
- `SMTP_PASS`
- `EMAIL_FROM`

**Nota:** Este error no bloquea el backend, solo desactiva el envío de emails.

### Error: "Stripe no está configurado"

**Causa:** Faltan variables de Stripe

**Solución:**
Si usas Stripe, configura:
- `STRIPE_SECRET_KEY`
- `STRIPE_WEBHOOK_SECRET`
- `STRIPE_PRICE_ID_EXPLORER`
- `STRIPE_PRICE_ID_TRADER`
- `STRIPE_PRICE_ID_PRO`
- `STRIPE_PRICE_ID_INSTITUCIONAL`

**Nota:** Este error no bloquea el backend, solo desactiva las funciones de pago.

---

## 📚 Referencias

- [Documentación de Supabase](https://supabase.com/docs)
- [Documentación de Stripe](https://stripe.com/docs)
- [Documentación de LiteLLM](https://docs.litellm.ai/)
- [Gmail App Passwords](https://support.google.com/accounts/answer/185833)

---

**Última actualización:** 2025-01-27

