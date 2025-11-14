# 🔴 Variables OBLIGATORIAS para Railway

El backend **NO iniciará** sin estas variables. Agrégalas **AHORA** en Railway.

---

## ⚠️ Variables CRÍTICAS (Sin estas, el backend NO funciona)

### 1. SUPABASE_URL
```
SUPABASE_URL=https://eixvqedpyuybfywmdulg.supabase.co
```

### 2. SUPABASE_SERVICE_KEY
```
SUPABASE_SERVICE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImVpeHZxZWRweXV5YmZ5d21kdWxnIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTczODA1NzYwMCwiZXhwIjoyMDUzNjMzNjAwfQ.tu_service_key_completo_aqui
```
**⚠️ IMPORTANTE:** Usa la **service_role** key, NO la anon key.

### 3. OPENAI_API_KEY O DEEPSEEK_API_KEY (Al menos UNA)

**Opción A: Deepseek (Recomendado)**
```
DEEPSEEK_API_KEY=sk-tu_api_key_de_deepseek
CHAT_MODEL=deepseek/deepseek-chat
```

**Opción B: OpenAI**
```
OPENAI_API_KEY=sk-proj-tu_api_key_de_openai
CHAT_MODEL=gpt-3.5-turbo
```

---

## 🟡 Variables IMPORTANTES (Para que todo funcione correctamente)

### 4. FRONTEND_URL
```
FRONTEND_URL=http://localhost:3000
```
(Actualiza después con la URL de Vercel)

### 5. Email SMTP
```
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=todossomostr4ders@gmail.com
SMTP_PASS=kjhf biie tgrk wncz
EMAIL_FROM=Codex Trader <todossomostr4ders@gmail.com>
ADMIN_EMAIL=todossomostr4ders@gmail.com
```

---

## 📋 Cómo Agregar en Railway

1. Ve a tu proyecto en Railway
2. Selecciona el servicio (backend)
3. Haz clic en la pestaña **"Variables"**
4. Haz clic en **"+ New Variable"**
5. Ingresa el **Name** y **Value**
6. Haz clic en **"Add"**
7. **Repite para cada variable**

---

## ✅ Verificación Rápida

Después de agregar las variables:

1. Railway reiniciará automáticamente
2. Ve a **Deployments** → **View Logs**
3. **NO debería** aparecer el error: "Faltan variables de entorno"
4. Debería mostrar: "✓ Iniciando servidor en puerto..."

---

## 🆘 Si Aún Aparece el Error

1. **Verifica que los nombres sean exactos** (case-sensitive):
   - ✅ `SUPABASE_URL` (correcto)
   - ❌ `supabase_url` (incorrecto)

2. **Verifica que hayas hecho clic en "Add"** después de ingresar cada variable

3. **Reinicia manualmente el servicio:**
   - Ve a **Deployments**
   - Haz clic en los tres puntos (⋯) → **Redeploy**

---

**⚠️ SIN ESTAS VARIABLES, EL BACKEND NO INICIARÁ**

