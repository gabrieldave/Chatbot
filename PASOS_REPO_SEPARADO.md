# 🚀 Pasos para Crear Repositorio Separado del Frontend

## ✅ Solución: Repositorio Separado

Vercel detectará automáticamente el frontend si está en su propio repositorio.

---

## 📋 Pasos Rápidos

### Paso 1: Crear Repositorio en GitHub

1. Ve a: **https://github.com/new**
2. **Repository name:** `codex-trader-frontend`
3. **Description:** "Frontend de Codex Trader - Next.js"
4. **Visibility:** Public o Private (tu elección)
5. **⚠️ NO marques:** "Add README", "Add .gitignore", "Choose a license"
6. Haz clic en **"Create repository"**

### Paso 2: Subir Código del Frontend

Abre PowerShell y ejecuta estos comandos:

```powershell
# Ir a la carpeta frontend
cd "C:\Users\dakyo\Documents\Proyectos de apps\MI_SAAS_BOT\frontend"

# Agregar todos los archivos
git add .

# Hacer commit
git commit -m "Initial commit: Codex Trader Frontend"

# Cambiar el remote al nuevo repositorio
git remote set-url origin https://github.com/gabrieldave/codex-trader-frontend.git

# Cambiar branch a main
git branch -M main

# Subir código
git push -u origin main
```

### Paso 3: Conectar Vercel con el Nuevo Repositorio

1. Ve a [Vercel Dashboard](https://vercel.com/dashboard)
2. **Cancelar/eliminar** el proyecto actual (si existe)
3. Haz clic en **"Add New..."** → **"Project"**
4. Selecciona: **`codex-trader-frontend`**
5. Vercel detectará automáticamente:
   - ✅ Framework: **Next.js**
   - ✅ Root Directory: **/** (automático, no necesitas configurarlo)
   - ✅ Build Command: **npm run build**
   - ✅ Install Command: **npm install**

6. **Configura las variables de entorno:**
   ```
   NEXT_PUBLIC_SUPABASE_URL=https://eixvqedpyuybfywmdulg.supabase.co
   NEXT_PUBLIC_SUPABASE_ANON_KEY=tu_anon_key_completo
   NEXT_PUBLIC_BACKEND_URL=https://web-production-3ab35.up.railway.app
   ```

7. Haz clic en **"Deploy"**

---

## ✅ Ventajas

1. ✅ **Vercel detecta todo automáticamente** (no necesitas Root Directory)
2. ✅ **Build más rápido** (solo frontend)
3. ✅ **Más limpio** (separación clara)
4. ✅ **Sin problemas de submódulos**

---

## 🔄 Estructura Final

- **Frontend:** `codex-trader-frontend` (GitHub) → Vercel
- **Backend:** `Chatbot` (GitHub) → Railway
- **Conexión:** Frontend se conecta al backend vía `NEXT_PUBLIC_BACKEND_URL`

---

**¡Con esto Vercel detectará todo automáticamente!** 🎉

