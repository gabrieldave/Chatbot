# 🔧 Solución: Error SUPABASE_SERVICE_KEY en Render

## ❌ Error

```
ValueError: Faltan variables de entorno obligatorias: SUPABASE_SERVICE_KEY. 
Asegúrate de tenerlas configuradas en Render.
```

## 🔍 Causa

La variable `SUPABASE_SERVICE_KEY` no está configurada en Render o está vacía.

## ✅ Solución

### Paso 1: Obtener la Service Key de Supabase

1. Ve a [Supabase Dashboard](https://app.supabase.com)
2. Selecciona tu proyecto
3. Ve a **Settings** → **API**
4. Busca la sección **"Project API keys"**
5. Copia el valor de **"service_role" key** (NO uses la "anon" key)

**⚠️ IMPORTANTE:** 
- Debe ser la **service_role** key (tiene permisos completos)
- NO uses la **anon** key (tiene permisos limitados)
- La key es muy larga, asegúrate de copiarla completa

### Paso 2: Configurar en Render

1. Ve a **Render Dashboard** → Tu Servicio → **Environment**
2. Haz clic en **"+ Add Environment Variable"**
3. Configura:
   - **Key:** `SUPABASE_SERVICE_KEY`
   - **Value:** Pega la service_role key completa que copiaste
4. Haz clic en **"Save Changes"**
5. Render reiniciará automáticamente el servicio

### Paso 3: Verificar

Después de agregar la variable, en los logs deberías ver:

```
✅ Usando SUPABASE_URL (URL REST): https://eixvqedpyuybfywmdulg.supabase.co
✅ Cliente de Supabase inicializado con URL REST: https://eixvqedpyuybfywmdulg.supabase.co
✅ SUPABASE_SERVICE_KEY configurado: Sí
✓ Iniciando servidor en puerto...
```

**NO deberías ver:**
- ❌ `Faltan variables de entorno obligatorias: SUPABASE_SERVICE_KEY`

## 📋 Variables Mínimas Necesarias en Render

Asegúrate de tener estas variables configuradas:

```env
SUPABASE_URL=https://eixvqedpyuybfywmdulg.supabase.co
SUPABASE_SERVICE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...[TU_SERVICE_KEY_COMPLETA]
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

## 🆘 Si Aún No Funciona

1. **Verifica que la key esté completa:**
   - La service_role key es muy larga (más de 200 caracteres)
   - Asegúrate de copiarla completa desde Supabase
   - No debe tener espacios al inicio o final

2. **Verifica que el nombre sea exacto:**
   - Debe ser exactamente: `SUPABASE_SERVICE_KEY`
   - Case-sensitive (mayúsculas/minúsculas importan)
   - No debe tener espacios

3. **Haz un redeploy manual:**
   - Ve a Render Dashboard → Tu Servicio
   - Haz clic en **"Manual Deploy"** → **"Deploy latest commit"**
   - Espera 2-3 minutos

---

**Última actualización:** 2025-01-27

