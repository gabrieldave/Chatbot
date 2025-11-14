# 🔐 Variables de Entorno para Railway - Codex Trader Backend

Este documento contiene **TODAS** las variables de entorno que necesitas configurar en Railway para que tu backend funcione correctamente.

---

## 📋 Cómo Agregar Variables en Railway

1. Ve a tu proyecto en Railway
2. Selecciona el servicio (backend)
3. Haz clic en la pestaña **"Variables"**
4. Haz clic en **"+ New Variable"**
5. Ingresa el **Name** y **Value**
6. Haz clic en **"Add"**
7. Repite para cada variable

**⚠️ IMPORTANTE:**
- No uses comillas en los valores (Railway las maneja automáticamente)
- Los nombres son **case-sensitive** (mayúsculas/minúsculas importan)
- Después de agregar variables, Railway reiniciará automáticamente el servicio

---

## 🔴 Variables OBLIGATORIAS (Debes configurarlas)

### 1. Supabase

```
SUPABASE_URL=https://eixvqedpyuybfywmdulg.supabase.co
```

**Dónde encontrarla:**
- Ve a tu [Dashboard de Supabase](https://app.supabase.com)
- Selecciona tu proyecto
- Ve a **Settings** → **API**
- Copia el valor de **"Project URL"**

---

```
SUPABASE_SERVICE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImVpeHZxZWRweXV5YmZ5d21kdWxnIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTczODA1NzYwMCwiZXhwIjoyMDUzNjMzNjAwfQ.tu_service_key_aqui
```

**Dónde encontrarla:**
- Ve a tu [Dashboard de Supabase](https://app.supabase.com)
- Selecciona tu proyecto
- Ve a **Settings** → **API**
- Copia el valor de **"service_role" key** (NO uses la "anon" key aquí)
- ⚠️ **Esta key es SECRETA**, no la compartas

---

### 2. Frontend URL

```
FRONTEND_URL=https://tu-frontend.vercel.app
```

**Valor temporal (mientras despliegas):**
```
FRONTEND_URL=http://localhost:3000
```

**Valor final (después de desplegar frontend en Vercel):**
```
FRONTEND_URL=https://codex-trader.vercel.app
```
(Reemplaza con tu URL real de Vercel)

---

### 3. Email (SMTP - Gmail)

```
SMTP_HOST=smtp.gmail.com
```

```
SMTP_PORT=587
```

```
SMTP_USER=todossomostr4ders@gmail.com
```

```
SMTP_PASS=kjhf biie tgrk wncz
```

**⚠️ IMPORTANTE:** Esta es una "App Password" de Gmail, NO tu contraseña normal.

**Cómo obtener una App Password:**
1. Ve a [myaccount.google.com](https://myaccount.google.com)
2. **Seguridad** → **Verificación en 2 pasos** (debe estar activada)
3. **Contraseñas de aplicaciones** → **Generar nueva contraseña**
4. Copia la contraseña generada (16 caracteres sin espacios)

---

```
EMAIL_FROM=Codex Trader <todossomostr4ders@gmail.com>
```

**Formato:** `Nombre <email@ejemplo.com>`

---

```
ADMIN_EMAIL=todossomostr4ders@gmail.com
```

**Email donde recibirás notificaciones de admin** (nuevos registros, pagos, etc.)

---

### 4. Modelo de IA

Elige **UNA** de estas opciones:

#### Opción A: OpenAI

```
OPENAI_API_KEY=sk-proj-tu_api_key_de_openai_aqui
```

```
CHAT_MODEL=gpt-3.5-turbo
```

O si prefieres GPT-4:
```
CHAT_MODEL=gpt-4
```

#### Opción B: Deepseek (Recomendado - Más barato)

```
DEEPSEEK_API_KEY=sk-tu_api_key_de_deepseek_aqui
```

```
CHAT_MODEL=deepseek/deepseek-chat
```

**⚠️ IMPORTANTE:** Solo configura **UNA** API key. Si configuras ambas, el sistema usará la que esté disponible.

---

## 🟡 Variables OPCIONALES (Solo si usas Stripe para pagos)

### 5. Stripe

```
STRIPE_SECRET_KEY=sk_live_tu_secret_key_aqui
```

**Dónde encontrarla:**
- Ve a [Dashboard de Stripe](https://dashboard.stripe.com)
- **Developers** → **API keys**
- Copia la **"Secret key"** (usa la de producción `sk_live_...` o la de prueba `sk_test_...`)

---

```
STRIPE_WEBHOOK_SECRET=whsec_tu_webhook_secret_aqui
```

**Dónde encontrarla:**
- Ve a [Dashboard de Stripe](https://dashboard.stripe.com)
- **Developers** → **Webhooks**
- Crea un webhook apuntando a: `https://tu-backend.railway.app/stripe/webhook`
- Copia el **"Signing secret"**

---

```
STRIPE_PRICE_ID_EXPLORER=price_tu_price_id_explorer
```

```
STRIPE_PRICE_ID_TRADER=price_tu_price_id_trader
```

```
STRIPE_PRICE_ID_PRO=price_tu_price_id_pro
```

```
STRIPE_PRICE_ID_INSTITUCIONAL=price_tu_price_id_institucional
```

**Dónde encontrarlas:**
- Ve a [Dashboard de Stripe](https://dashboard.stripe.com)
- **Products** → Selecciona cada plan → **Pricing**
- Copia el **"Price ID"** (empieza con `price_`)

---

```
STRIPE_FAIR_USE_COUPON_ID=FAIR_USE_20
```

**Dónde encontrarla:**
- Ve a [Dashboard de Stripe](https://dashboard.stripe.com)
- **Products** → **Coupons**
- Crea un cupón con 20% de descuento
- Copia el **"Coupon ID"**

---

## 🟢 Variables Automáticas (Railway las proporciona)

Estas variables las proporciona Railway automáticamente, **NO** necesitas configurarlas:

```
PORT=8000
```

Railway asigna un puerto automáticamente y lo pasa como variable de entorno. Tu código ya está configurado para usarlo.

---

## 📋 Lista Completa para Copiar y Pegar

Copia estas variables y pégalas en Railway una por una:

### Variables Obligatorias

```
SUPABASE_URL=https://eixvqedpyuybfywmdulg.supabase.co
SUPABASE_SERVICE_KEY=tu_service_key_aqui
FRONTEND_URL=http://localhost:3000
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=todossomostr4ders@gmail.com
SMTP_PASS=kjhf biie tgrk wncz
EMAIL_FROM=Codex Trader <todossomostr4ders@gmail.com>
ADMIN_EMAIL=todossomostr4ders@gmail.com
DEEPSEEK_API_KEY=tu_api_key_de_deepseek
CHAT_MODEL=deepseek/deepseek-chat
```

### Variables Opcionales (Solo si usas Stripe)

```
STRIPE_SECRET_KEY=sk_live_tu_secret_key
STRIPE_WEBHOOK_SECRET=whsec_tu_webhook_secret
STRIPE_PRICE_ID_EXPLORER=price_xxx
STRIPE_PRICE_ID_TRADER=price_xxx
STRIPE_PRICE_ID_PRO=price_xxx
STRIPE_PRICE_ID_INSTITUCIONAL=price_xxx
STRIPE_FAIR_USE_COUPON_ID=FAIR_USE_20
```

---

## ✅ Verificación

Después de agregar todas las variables:

1. **Revisa los logs en Railway:**
   - Ve a **Deployments** → Selecciona el último deployment → **View Logs**
   - No debería haber errores de "variable not found"

2. **Prueba el endpoint:**
   - Ve a: `https://tu-proyecto.up.railway.app/docs`
   - Deberías ver la documentación de FastAPI

3. **Prueba el email:**
   - Ve a: `https://tu-proyecto.up.railway.app/debug/test-email`
   - Debería enviar un email de prueba

---

## 🔄 Actualizar Variables

Si necesitas actualizar una variable:

1. Ve a **Variables** en Railway
2. Encuentra la variable que quieres actualizar
3. Haz clic en los tres puntos (⋯) → **Edit**
4. Actualiza el valor
5. Haz clic en **Save**
6. Railway reiniciará automáticamente

---

## ⚠️ Notas Importantes

### Seguridad

- ⚠️ **NUNCA** compartas tus variables de entorno
- ⚠️ **NUNCA** subas el archivo `.env` a GitHub
- ⚠️ Las variables en Railway son **privadas** y **seguras**

### Valores con Espacios

Si un valor tiene espacios (como `EMAIL_FROM`), puedes usar:
- Con comillas: `"Codex Trader <email@ejemplo.com>"` (Railway las maneja)
- Sin comillas: `Codex Trader <email@ejemplo.com>` (también funciona)

### Case Sensitivity

Los nombres de variables son **case-sensitive**:
- ✅ `SUPABASE_URL` (correcto)
- ❌ `supabase_url` (incorrecto)
- ❌ `Supabase_Url` (incorrecto)

---

## 🆘 Problemas Comunes

### "Environment variable not found"

**Solución:**
- Verifica que el nombre sea exacto (case-sensitive)
- Verifica que hayas hecho clic en **"Add"** después de ingresar el valor
- Reinicia el servicio manualmente si es necesario

### "Supabase connection failed"

**Solución:**
- Verifica que `SUPABASE_URL` sea correcta (debe terminar en `.supabase.co`)
- Verifica que `SUPABASE_SERVICE_KEY` sea la **service_role** key (no la anon key)
- Verifica que el proyecto de Supabase esté activo

### "SMTP authentication failed"

**Solución:**
- Verifica que `SMTP_PASS` sea una **App Password** de Gmail (16 caracteres)
- Verifica que la verificación en 2 pasos esté activada en Gmail
- Verifica que `SMTP_USER` sea el email correcto

---

**¡Configuración completada! 🎉**

