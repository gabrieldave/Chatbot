# 🚂 Guía Completa: Desplegar Backend de Codex Trader en Railway

Railway es una excelente opción para desplegar tu backend Python. Es **gratis para empezar** y muy fácil de usar.

---

## 📋 Requisitos Previos

1. ✅ Cuenta en [Railway](https://railway.app) (gratis)
2. ✅ Código del backend en GitHub (ya lo tienes: https://github.com/gabrieldave/Chatbot)
3. ✅ Archivos necesarios:
   - `Procfile` (ya lo tienes)
   - `requirements.txt` (ya lo tienes)
   - `runtime.txt` (ya lo tienes)

---

## 🚀 Paso 1: Crear Cuenta en Railway

1. Ve a [https://railway.app](https://railway.app)
2. Haz clic en **"Start a New Project"** o **"Login"**
3. Elige **"Login with GitHub"**
4. Autoriza Railway a acceder a tus repositorios

---

## 📦 Paso 2: Crear Nuevo Proyecto

1. En el dashboard de Railway, haz clic en **"New Project"**
2. Selecciona **"Deploy from GitHub repo"**
3. Busca y selecciona tu repositorio: **`gabrieldave/Chatbot`**
4. Railway detectará automáticamente que es un proyecto Python

---

## ⚙️ Paso 3: Configurar el Servicio

### 3.1 Seleccionar Directorio del Backend

Railway necesita saber dónde está tu backend:

1. En la configuración del servicio, ve a **"Settings"**
2. Busca **"Root Directory"** o **"Source"**
3. Establece: `backend`
4. Esto le dice a Railway que el código está en la carpeta `backend/`

### 3.2 Configurar Comando de Inicio

Railway debería detectar automáticamente el `Procfile`, pero verifica:

1. Ve a **"Settings"** → **"Deploy"**
2. Verifica que el **Start Command** sea: `python main.py`
   - O si tienes `Procfile`, debería leerlo automáticamente

---

## 🔐 Paso 4: Configurar Variables de Entorno

### 4.1 Variables Requeridas

En Railway, ve a **"Variables"** y agrega todas estas variables:

#### Supabase
```
SUPABASE_URL=https://tu-proyecto.supabase.co
SUPABASE_SERVICE_KEY=tu_service_key_aqui
```

#### Frontend (URL de producción cuando despliegues)
```
FRONTEND_URL=https://tu-frontend.vercel.app
```

#### Email (SMTP)
```
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=todossomostr4ders@gmail.com
SMTP_PASS=tu_app_password_de_gmail
EMAIL_FROM="Codex Trader <todossomostr4ders@gmail.com>"
ADMIN_EMAIL=todossomostr4ders@gmail.com
```

#### Stripe (si usas pagos)
```
STRIPE_SECRET_KEY=sk_live_tu_secret_key
STRIPE_WEBHOOK_SECRET=whsec_tu_webhook_secret
STRIPE_PRICE_ID_EXPLORER=price_xxx
STRIPE_PRICE_ID_TRADER=price_xxx
STRIPE_PRICE_ID_PRO=price_xxx
STRIPE_PRICE_ID_INSTITUCIONAL=price_xxx
```

#### Modelo de IA
```
OPENAI_API_KEY=sk-tu_api_key
# O
DEEPSEEK_API_KEY=tu_api_key
# O el que uses

CHAT_MODEL=deepseek/deepseek-chat
# O el modelo que prefieras
```

### 4.2 Cómo Agregar Variables en Railway

1. En tu servicio, haz clic en **"Variables"** (pestaña en la parte superior)
2. Haz clic en **"+ New Variable"**
3. Ingresa el **Name** y **Value**
4. Haz clic en **"Add"**
5. Repite para cada variable

**⚠️ IMPORTANTE:**
- No uses comillas en los valores (Railway las agrega automáticamente si es necesario)
- Para `EMAIL_FROM`, puedes usar: `Codex Trader <email@gmail.com>` sin comillas externas

---

## 🚀 Paso 5: Desplegar

### 5.1 Primer Despliegue

1. Después de configurar las variables, Railway comenzará a desplegar automáticamente
2. Verás el progreso en la pestaña **"Deployments"**
3. El despliegue tarda 2-5 minutos normalmente

### 5.2 Verificar el Despliegue

1. Ve a la pestaña **"Deployments"**
2. Espera a que el estado sea **"SUCCESS"** (verde)
3. Haz clic en el deployment para ver los logs

### 5.3 Verificar que Funciona

1. Ve a la pestaña **"Settings"**
2. Busca **"Domains"** o **"Networking"**
3. Railway te dará una URL como: `https://tu-proyecto.up.railway.app`
4. Prueba acceder a: `https://tu-proyecto.up.railway.app/docs`
5. Deberías ver la documentación de FastAPI

---

## 🔗 Paso 6: Configurar Dominio Personalizado (Opcional)

### 6.1 Agregar Dominio en Railway

1. Ve a **"Settings"** → **"Networking"** → **"Domains"**
2. Haz clic en **"Custom Domain"**
3. Ingresa tu dominio (ej: `api.codextrader.com`)
4. Sigue las instrucciones para configurar DNS

### 6.2 Configurar DNS

Railway te dará un registro CNAME:
- **Tipo:** CNAME
- **Nombre:** `api` (o el subdominio que prefieras)
- **Valor:** `tu-proyecto.up.railway.app`

---

## ✅ Paso 7: Verificar que Todo Funciona

### 7.1 Checklist de Verificación

- [ ] ✅ El backend responde en la URL de Railway
- [ ] ✅ `/docs` muestra la documentación de FastAPI
- [ ] ✅ Las variables de entorno están configuradas
- [ ] ✅ Los logs no muestran errores críticos
- [ ] ✅ La conexión a Supabase funciona
- [ ] ✅ El envío de emails funciona (prueba con `/debug/test-email`)

### 7.2 Probar Endpoints

1. **Documentación:**
   - Ve a: `https://tu-proyecto.up.railway.app/docs`
   - Deberías ver Swagger UI

2. **Health Check:**
   - Ve a: `https://tu-proyecto.up.railway.app/health`
   - Debería responder: `{"status": "ok"}`

3. **Test Email (solo desarrollo):**
   - `POST https://tu-proyecto.up.railway.app/debug/test-email`
   - Debería enviar un email de prueba

---

## 🔄 Paso 8: Configurar Despliegues Automáticos

### 8.1 Conectar con GitHub

Railway ya está conectado a tu repositorio. Cada vez que hagas `git push`:

- Se creará un nuevo deployment automáticamente
- Railway detectará los cambios y desplegará la nueva versión

### 8.2 Configurar Branch

1. Ve a **"Settings"** → **"Source"**
2. Verifica que **"Branch"** sea `main` (o `master`)
3. Railway desplegará automáticamente cuando hagas push a esta branch

---

## 💰 Paso 9: Planes y Costos

### Plan Gratis (Hobby)

- ✅ **$5 de crédito gratis** cada mes
- ✅ Perfecto para empezar
- ✅ Suficiente para desarrollo y pruebas
- ⚠️ Se suspende después de 5 días de inactividad

### Plan Pro ($20/mes)

- ✅ Sin límite de crédito
- ✅ No se suspende por inactividad
- ✅ Mejor para producción

**Recomendación:** Empieza con el plan gratis. Si necesitas más recursos, actualiza después.

---

## 🐛 Solución de Problemas Comunes

### Error: "Module not found"

**Solución:**
- Verifica que `requirements.txt` tenga todas las dependencias
- Revisa los logs de build en Railway
- Asegúrate de que el `Root Directory` esté configurado como `backend`

### Error: "Port not found" o "Application failed to respond"

**Solución:**
- Verifica que tu aplicación escuche en el puerto que Railway asigna
- Railway asigna un puerto dinámicamente en la variable `PORT`
- Asegúrate de que `main.py` use: `port = int(os.getenv("PORT", 8000))`

### Error: "Environment variable not found"

**Solución:**
- Verifica que todas las variables estén en Railway
- Revisa que los nombres sean exactos (case-sensitive)
- Reinicia el servicio después de agregar variables

### Error: "Build failed"

**Solución:**
- Revisa los logs de build en Railway
- Verifica que `requirements.txt` esté correcto
- Asegúrate de que `runtime.txt` tenga una versión válida de Python

### Error: "Supabase connection failed"

**Solución:**
- Verifica que `SUPABASE_URL` y `SUPABASE_SERVICE_KEY` sean correctos
- Asegúrate de usar la `service_role` key (no la `anon` key)
- Verifica que el proyecto de Supabase esté activo

---

## 📝 Resumen de Variables de Entorno

Copia y pega esto en un documento mientras configuras Railway:

```
# Supabase
SUPABASE_URL=https://tu-proyecto.supabase.co
SUPABASE_SERVICE_KEY=tu_service_key

# Frontend (actualizar después de desplegar frontend)
FRONTEND_URL=https://tu-frontend.vercel.app

# Email
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=todossomostr4ders@gmail.com
SMTP_PASS=tu_app_password
EMAIL_FROM=Codex Trader <todossomostr4ders@gmail.com>
ADMIN_EMAIL=todossomostr4ders@gmail.com

# Stripe (si usas)
STRIPE_SECRET_KEY=sk_live_...
STRIPE_WEBHOOK_SECRET=whsec_...
STRIPE_PRICE_ID_EXPLORER=price_...
STRIPE_PRICE_ID_TRADER=price_...
STRIPE_PRICE_ID_PRO=price_...
STRIPE_PRICE_ID_INSTITUCIONAL=price_...

# IA
OPENAI_API_KEY=sk-...
# O
DEEPSEEK_API_KEY=...
CHAT_MODEL=deepseek/deepseek-chat
```

---

## 🎉 ¡Listo!

Tu backend debería estar funcionando en Railway. Guarda la URL que Railway te dio, la necesitarás para:

1. Configurar el frontend en Vercel (`NEXT_PUBLIC_BACKEND_URL`)
2. Configurar webhooks de Stripe
3. Configurar redirects en Supabase

### Próximos Pasos

1. ✅ Backend desplegado en Railway
2. ⏭️ Desplegar frontend en Vercel (siguiente paso)
3. ⏭️ Configurar webhooks de Stripe con la URL de Railway
4. ⏭️ Actualizar `FRONTEND_URL` en Railway cuando tengas la URL de Vercel

---

## 📞 Soporte

Si tienes problemas:

1. Revisa los logs en Railway: **Deployments** → Selecciona un deployment → **View Logs**
2. Revisa la documentación de Railway: [https://docs.railway.app](https://docs.railway.app)
3. Verifica que todas las variables estén configuradas correctamente

---

**¡Éxito con tu despliegue! 🚂**

