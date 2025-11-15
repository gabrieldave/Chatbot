# 🔧 Solución de Errores Comunes en Render

Esta guía te ayudará a resolver los errores más comunes al desplegar el backend en Render.

---

## 🔴 Error 1: "No se pudo determinar la URL REST de Supabase"

### Síntomas:
```
RuntimeError: No se pudo determinar la URL REST de Supabase.
Configura una de estas variables:
  - SUPABASE_REST_URL (URL REST directa, ej: https://xxx.supabase.co)
  - SUPABASE_DB_URL (URL de Postgres, ej: postgresql://postgres:pass@db.xxx.supabase.co:5432/postgres)
  - SUPABASE_URL (URL REST o Postgres, para compatibilidad)
```

### Causa:
Falta la variable `SUPABASE_URL` o está mal configurada.

### Solución:

**Opción A: Usar SUPABASE_URL (Recomendado - Más simple)**

En Render Dashboard → Environment, agrega:

```
SUPABASE_URL=https://eixvqedpyuybfywmdulg.supabase.co
```

**⚠️ IMPORTANTE:** 
- Debe empezar con `https://`
- Debe terminar en `.supabase.co` (NO `.com`)
- NO debe tener espacios al inicio o final
- NO uses comillas

**Opción B: Usar SUPABASE_REST_URL (Alternativa)**

```
SUPABASE_REST_URL=https://eixvqedpyuybfywmdulg.supabase.co
```

**Opción C: Usar SUPABASE_DB_URL (Si tienes la URL de Postgres)**

```
SUPABASE_DB_URL=postgresql://postgres:tu_password@db.eixvqedpyuybfywmdulg.supabase.co:5432/postgres
```

### Verificación:
1. Agrega la variable en Render
2. Haz clic en **"Manual Deploy"** → **"Deploy latest commit"**
3. Revisa los logs, deberías ver:
   ```
   ✅ Usando SUPABASE_URL (URL REST): https://eixvqedpyuybfywmdulg.supabase.co
   ```

---

## 🔴 Error 2: "Faltan variables de entorno obligatorias"

### Síntomas:
```
ValueError: Faltan variables de entorno obligatorias: SUPABASE_SERVICE_KEY, DEEPSEEK_API_KEY
```

### Causa:
Faltan variables críticas.

### Solución:

Agrega estas variables en Render Dashboard → Environment:

```env
SUPABASE_SERVICE_KEY=tu_service_key_completa_aqui
DEEPSEEK_API_KEY=sk-113b676b0f8743438d47722440079739
CHAT_MODEL=deepseek/deepseek-chat
```

**⚠️ IMPORTANTE:**
- `SUPABASE_SERVICE_KEY` debe ser la **service_role key** completa (no la anon key)
- `DEEPSEEK_API_KEY` debe empezar con `sk-`
- NO uses comillas en los valores
- Los nombres son case-sensitive

### Verificación:
Después de agregar las variables, haz redeploy y revisa los logs. Deberías ver:
```
✓ API Key de Deepseek configurada
✓ Modelo por defecto: deepseek/deepseek-chat
```

---

## 🔴 Error 3: "Hostname no es válido para URL REST de Supabase"

### Síntomas:
```
ValueError: Hostname no es válido para URL REST de Supabase: xxx.supabase.com
```

### Causa:
La URL de Supabase termina en `.supabase.com` en lugar de `.supabase.co`

### Solución:

**❌ INCORRECTO:**
```
SUPABASE_URL=https://eixvqedpyuybfywmdulg.supabase.com
```

**✅ CORRECTO:**
```
SUPABASE_URL=https://eixvqedpyuybfywmdulg.supabase.co
```

**Nota:** Debe terminar en `.co` (NO `.com`)

---

## 🔴 Error 4: "ModuleNotFoundError" o "ImportError"

### Síntomas:
```
ModuleNotFoundError: No module named 'fastapi'
ImportError: cannot import name 'create_client' from 'supabase'
```

### Causa:
Faltan dependencias en `requirements.txt` o el build falló.

### Solución:

1. **Verifica que `requirements.txt` tenga todas las dependencias:**
   ```txt
   fastapi==0.115.0
   uvicorn[standard]==0.32.0
   python-dotenv==1.0.1
   supabase==2.10.0
   llama-index==0.12.0
   llama-index-embeddings-openai==0.3.0
   llama-index-vector-stores-supabase==0.3.0
   openai>=1.55.3
   litellm==1.55.0
   psycopg2-binary==2.9.10
   pydantic==2.9.2
   python-multipart==0.0.12
   stripe==10.8.0
   ```

2. **Verifica el Build Command en Render:**
   ```
   pip install -r requirements.txt
   ```

3. **Revisa los logs del build** para ver qué módulo falta

4. **Si falta un módulo**, agrégalo a `requirements.txt` y haz commit + push

---

## 🔴 Error 5: "Port already in use" o "Address already in use"

### Síntomas:
```
OSError: [Errno 98] Address already in use
```

### Causa:
El Start Command no está usando la variable `$PORT` que Render proporciona.

### Solución:

**❌ INCORRECTO:**
```
uvicorn main:app --host 0.0.0.0 --port 8000
```

**✅ CORRECTO:**
```
uvicorn main:app --host 0.0.0.0 --port $PORT
```

**⚠️ IMPORTANTE:** 
- Render proporciona automáticamente la variable `PORT`
- NO necesitas configurarla manualmente
- DEBES usar `$PORT` en el Start Command

---

## 🔴 Error 6: El servicio se detiene después de unos minutos

### Síntomas:
El servicio funciona pero se detiene después de 15 minutos de inactividad.

### Causa:
Render suspende servicios gratuitos después de 15 minutos de inactividad.

### Solución:

**Opción A: Actualizar a plan de pago (Recomendado para producción)**
- Los servicios de pago no se suspenden

**Opción B: Usar un servicio de ping**
- Configura un cron job o servicio que haga requests periódicos a tu API
- Ejemplo: Usar [UptimeRobot](https://uptimerobot.com) para hacer pings cada 5 minutos

**Opción C: Configurar Health Check en Render**
- Ve a Settings → Health Check Path
- Configura: `/health`
- Render hará pings automáticos

---

## 🔴 Error 7: "Network is unreachable" al conectar a Supabase

### Síntomas:
```
psycopg2.OperationalError: could not connect to server: Network is unreachable
```

### Causa:
Problemas de red entre Render y Supabase, o configuración incorrecta.

### Solución:

1. **Verifica que `SUPABASE_URL` esté correcta:**
   ```
   SUPABASE_URL=https://eixvqedpyuybfywmdulg.supabase.co
   ```

2. **Verifica que `SUPABASE_SERVICE_KEY` esté completa:**
   - Debe ser la service_role key (no la anon key)
   - Debe estar completa (no truncada)

3. **Verifica restricciones de IP en Supabase:**
   - Ve a Supabase Dashboard → Settings → Database
   - Verifica que no haya restricciones de IP activas
   - Si las hay, agrega la IP de Render o desactívalas temporalmente

4. **Prueba usar `SUPABASE_DB_URL` en lugar de `SUPABASE_URL`:**
   ```
   SUPABASE_DB_URL=postgresql://postgres:tu_password@db.eixvqedpyuybfywmdulg.supabase.co:5432/postgres
   ```

---

## 📋 Checklist de Verificación

Antes de reportar un error, verifica:

- [ ] `SUPABASE_URL` está configurada y termina en `.supabase.co`
- [ ] `SUPABASE_SERVICE_KEY` está configurada (service_role key completa)
- [ ] `DEEPSEEK_API_KEY` está configurada y empieza con `sk-`
- [ ] `CHAT_MODEL` está configurada como `deepseek/deepseek-chat`
- [ ] Build Command es: `pip install -r requirements.txt`
- [ ] Start Command es: `uvicorn main:app --host 0.0.0.0 --port $PORT`
- [ ] Todas las variables NO tienen comillas
- [ ] Los nombres de las variables son exactos (case-sensitive)
- [ ] Se hizo redeploy después de agregar/modificar variables

---

## 🆘 Si Ninguna Solución Funciona

1. **Revisa los logs completos en Render:**
   - Ve a Logs en Render Dashboard
   - Copia el error completo (desde el inicio del build hasta el error)

2. **Verifica la configuración:**
   - Compara tus variables con `VARIABLES_RENDER.txt`
   - Asegúrate de que todos los valores sean correctos

3. **Prueba un deploy limpio:**
   - Elimina el servicio en Render
   - Crea un nuevo servicio desde cero
   - Configura todas las variables de nuevo

---

**Última actualización:** 2025-01-27

