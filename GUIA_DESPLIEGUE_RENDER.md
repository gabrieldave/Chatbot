# 🚀 Guía de Despliegue en Render - CODEX TRADER Backend

Esta guía te ayudará a desplegar el backend de CODEX TRADER en Render.

---

## 📋 Requisitos Previos

1. Cuenta en [Render](https://render.com)
2. Repositorio de GitHub con el código del backend
3. Variables de entorno configuradas (ver sección de Variables)

---

## 🚀 Paso 1: Crear el Servicio en Render

### 1.1 Crear Nuevo Web Service

1. Ve a [Render Dashboard](https://dashboard.render.com)
2. Haz clic en **"+ New"** → **"Web Service"**
3. Conecta tu repositorio de GitHub
4. Selecciona el repositorio que contiene el backend

### 1.2 Configuración Básica

**Nombre del servicio:**
```
codex-trader-backend
```
(O el nombre que prefieras)

**Región:**
- Selecciona la región más cercana a tus usuarios
- Recomendado: **Oregon (US West)** para mejor compatibilidad con Supabase

**Rama:**
```
main
```
(O la rama que uses para producción)

---

## ⚙️ Paso 2: Configurar Build y Start Commands

### 2.1 Build Command

```
pip install -r requirements.txt
```

### 2.2 Start Command

```
uvicorn main:app --host 0.0.0.0 --port $PORT
```

**⚠️ IMPORTANTE:** Render proporciona automáticamente la variable `PORT`, no necesitas configurarla manualmente.

---

## 🔐 Paso 3: Configurar Variables de Entorno

Ve a **Environment** en la configuración de tu servicio y agrega estas variables:

### Variables Obligatorias

```env
SUPABASE_URL=https://eixvqedpyuybfywmdulg.supabase.co
SUPABASE_SERVICE_KEY=tu_service_key_completa_aqui
DEEPSEEK_API_KEY=sk-113b676b0f8743438d47722440079739
CHAT_MODEL=deepseek/deepseek-chat
FRONTEND_URL=http://localhost:3000
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=todossomostr4ders@gmail.com
SMTP_PASS=kjhf biie tgrk wncz
EMAIL_FROM=Codex Trader <todossomostr4ders@gmail.com>
ADMIN_EMAIL=todossomostr4ders@gmail.com
```

### Variables Opcionales (RAG)

```env
SUPABASE_DB_PASSWORD=tu_contraseña_de_postgres
```

### Variables Opcionales (Stripe)

```env
STRIPE_SECRET_KEY=sk_test_[TU_STRIPE_SECRET_KEY_AQUI]
STRIPE_WEBHOOK_SECRET=whsec_tu_webhook_secret
STRIPE_PRICE_ID_EXPLORER=price_1STXp3G2B99hBCyaEUlT1dxZ
STRIPE_PRICE_ID_TRADER=price_1STXqOG2B99hBCya333a5zac
STRIPE_PRICE_ID_PRO=price_1STXqlG2B99hBCyaSmGIfMGu
STRIPE_PRICE_ID_INSTITUCIONAL=price_1STXr0G2B99hBCyaVE2kQzYi
STRIPE_FAIR_USE_COUPON_ID=z3OlKNN6
```

**⚠️ IMPORTANTE:**
- NO uses comillas en los valores
- Los nombres son case-sensitive (mayúsculas/minúsculas importan)
- Después de agregar variables, Render reiniciará automáticamente

---

## 🔧 Paso 4: Configuración Avanzada (Opcional)

### 4.1 Python Version

Render detecta automáticamente la versión de Python desde `requirements.txt` o `runtime.txt`.

Si tienes `runtime.txt`, asegúrate de que tenga:
```
python-3.12
```

### 4.2 Health Check (Opcional)

Render puede verificar que tu servicio esté funcionando. Configura:

**Health Check Path:**
```
/health
```

**Health Check Interval:**
```
30 seconds
```

---

## 🚀 Paso 5: Desplegar

1. Haz clic en **"Create Web Service"**
2. Render comenzará a construir y desplegar tu aplicación
3. Espera 3-5 minutos para que complete el build
4. Verifica los logs para asegurarte de que no hay errores

---

## ✅ Verificación

### 1. Verificar que el Servicio Esté Funcionando

Después del despliegue, Render te dará una URL como:
```
https://codex-trader-backend.onrender.com
```

Abre en tu navegador:
```
https://tu-servicio.onrender.com/docs
```

Deberías ver la documentación de la API de FastAPI.

### 2. Verificar Logs

1. Ve a **Logs** en Render Dashboard
2. Busca mensajes como:
   - `✓ Iniciando servidor en puerto...`
   - `✓ API Key de Deepseek configurada`
   - `✓ Modelo por defecto: deepseek/deepseek-chat`
3. **NO debería** aparecer:
   - `Faltan variables de entorno obligatorias`
   - `Error al iniciar servidor`

### 3. Probar Endpoint de Health

Abre en tu navegador:
```
https://tu-servicio.onrender.com/health
```

Debería responder:
```json
{"status": "ok"}
```

---

## 🐛 Solución de Problemas Comunes

### Error: "Faltan variables de entorno obligatorias"

**Causa:** Faltan variables críticas

**Solución:**
1. Ve a **Environment** en Render
2. Verifica que estas variables estén configuradas:
   - `SUPABASE_SERVICE_KEY`
   - `DEEPSEEK_API_KEY` o `OPENAI_API_KEY`
3. Verifica que los nombres sean exactos (case-sensitive)
4. Haz clic en **"Manual Deploy"** → **"Deploy latest commit"**

---

### Error: "No se pudo determinar la URL REST de Supabase"

**Causa:** `SUPABASE_URL` no está configurada o tiene formato incorrecto

**Solución:**
1. Verifica que `SUPABASE_URL` esté configurada en Render
2. Debe tener el formato: `https://xxx.supabase.co`
3. No debe tener espacios al inicio o final
4. Haz redeploy después de corregir

---

### Error: "ModuleNotFoundError" o "ImportError"

**Causa:** Faltan dependencias en `requirements.txt`

**Solución:**
1. Verifica que `requirements.txt` tenga todas las dependencias
2. Revisa los logs del build para ver qué módulo falta
3. Agrega la dependencia faltante a `requirements.txt`
4. Haz commit y push a GitHub
5. Render redeployará automáticamente

---

### Error: "Port already in use" o "Address already in use"

**Causa:** El código no está usando la variable `PORT` correctamente

**Solución:**
Verifica que el Start Command sea:
```
uvicorn main:app --host 0.0.0.0 --port $PORT
```

**NO uses:**
- ❌ `--port 8000` (puerto fijo)
- ❌ `--port 8080` (puerto fijo)

**SÍ usa:**
- ✅ `--port $PORT` (variable de entorno que Render proporciona)

---

### El servicio se detiene después de unos minutos

**Causa:** Render suspende servicios gratuitos después de 15 minutos de inactividad

**Solución:**
1. **Opción A:** Actualizar a plan de pago (recomendado para producción)
2. **Opción B:** Usar un servicio de "ping" para mantener el servicio activo
3. **Opción C:** Configurar un cron job que haga requests periódicos

---

### Error de conexión a Supabase

**Causa:** Problemas de red o configuración incorrecta

**Solución:**
1. Verifica que `SUPABASE_URL` y `SUPABASE_SERVICE_KEY` estén correctas
2. Verifica que no haya restricciones de IP en Supabase
3. Revisa los logs para ver el error específico
4. Considera usar `SUPABASE_DB_URL` en lugar de `SUPABASE_URL` si tienes problemas

---

## 📝 Notas Importantes

1. **Render proporciona `PORT` automáticamente** - No necesitas configurarla
2. **Los servicios gratuitos se suspenden** después de 15 minutos de inactividad
3. **El primer deploy puede tardar** 5-10 minutos
4. **Los redeploys son más rápidos** (2-3 minutos)
5. **Render reinicia automáticamente** cuando detecta cambios en GitHub

---

## 🔄 Actualizar el Servicio

Para actualizar el código:

1. Haz commit y push a GitHub
2. Render detectará automáticamente los cambios
3. Iniciará un nuevo deploy automáticamente
4. Puedes ver el progreso en **Events** → **Deployments**

Para forzar un redeploy manual:

1. Ve a **Manual Deploy** en Render Dashboard
2. Selecciona **"Deploy latest commit"**
3. Render iniciará un nuevo deploy

---

## 🌐 Configurar Dominio Personalizado (Opcional)

1. Ve a **Settings** → **Custom Domain**
2. Agrega tu dominio (ej: `api.codextrader.tech`)
3. Render te dará instrucciones para configurar DNS
4. Actualiza `FRONTEND_URL` con tu dominio personalizado

---

## 📚 Referencias

- [Documentación de Render](https://render.com/docs)
- [Render Python Guide](https://render.com/docs/deploy-python)
- [Variables de Entorno en Render](https://render.com/docs/environment-variables)

---

**Última actualización:** 2025-01-27

