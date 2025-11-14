# 🚀 Guía Completa: Desplegar Frontend de Codex Trader en Vercel

Esta guía te llevará paso a paso para subir tu frontend de Next.js a Vercel.

---

## 📋 Requisitos Previos

1. ✅ Cuenta en [Vercel](https://vercel.com) (gratis)
2. ✅ Código del frontend en un repositorio Git (GitHub, GitLab o Bitbucket)
3. ✅ Backend desplegado (Railway, Render, etc.) con URL de producción
4. ✅ Proyecto Supabase configurado

---

## 🔧 Paso 1: Preparar el Proyecto

### 1.1 Verificar que el proyecto esté listo

Asegúrate de que tu proyecto tenga:

- ✅ `package.json` con scripts de build
- ✅ `next.config.ts` configurado
- ✅ Todas las dependencias instaladas localmente funcionan

### 1.2 Verificar que el build funciona localmente

```bash
cd frontend
npm install
npm run build
```

Si el build funciona sin errores, estás listo para continuar.

---

## 📦 Paso 2: Subir Código a Git (si no lo has hecho)

### 2.1 Inicializar repositorio (si es necesario)

```bash
cd frontend
git init
git add .
git commit -m "Preparar para despliegue en Vercel"
```

### 2.2 Crear repositorio en GitHub/GitLab/Bitbucket

1. Ve a [GitHub](https://github.com) (o tu plataforma preferida)
2. Crea un nuevo repositorio (ej: `codex-trader-frontend`)
3. **NO** inicialices con README, .gitignore, etc.

### 2.3 Conectar y subir código

```bash
git remote add origin https://github.com/TU_USUARIO/codex-trader-frontend.git
git branch -M main
git push -u origin main
```

---

## 🌐 Paso 3: Configurar Vercel

### 3.1 Crear cuenta en Vercel

1. Ve a [https://vercel.com](https://vercel.com)
2. Haz clic en **"Sign Up"**
3. Elige **"Continue with GitHub"** (o tu plataforma Git preferida)
4. Autoriza Vercel a acceder a tus repositorios

### 3.2 Importar Proyecto

1. En el dashboard de Vercel, haz clic en **"Add New..."** → **"Project"**
2. Selecciona tu repositorio `codex-trader-frontend`
3. Vercel detectará automáticamente que es un proyecto Next.js

### 3.3 Configurar el Proyecto

**Framework Preset:** Next.js (debería detectarse automáticamente)

**Root Directory:** `frontend` (si tu repo tiene la carpeta frontend, de lo contrario deja vacío)

**Build Command:** `npm run build` (por defecto)

**Output Directory:** `.next` (por defecto)

**Install Command:** `npm install` (por defecto)

---

## 🔐 Paso 4: Configurar Variables de Entorno

### 4.1 Variables Necesarias

En la sección **"Environment Variables"** de Vercel, agrega las siguientes:

#### Variables Públicas (NEXT_PUBLIC_*)

Estas son visibles en el navegador, así que solo incluyen valores que no sean secretos:

```
NEXT_PUBLIC_SUPABASE_URL=https://tu-proyecto.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=tu_anon_key_aqui
NEXT_PUBLIC_BACKEND_URL=https://tu-backend.railway.app
```

**⚠️ IMPORTANTE:** 
- `NEXT_PUBLIC_SUPABASE_URL`: URL de tu proyecto Supabase (Settings > API > Project URL)
- `NEXT_PUBLIC_SUPABASE_ANON_KEY`: Anon/Public Key de Supabase (Settings > API > anon public key)
- `NEXT_PUBLIC_BACKEND_URL`: URL de tu backend en producción (ej: `https://codex-trader-backend.railway.app`)

#### Variables Privadas (solo para API Routes del servidor)

Si usas API Routes que necesitan secretos, agrega:

```
BACKEND_URL=https://tu-backend.railway.app
```

**Nota:** Las variables `NEXT_PUBLIC_*` están disponibles en el cliente. Las otras solo en el servidor.

### 4.2 Cómo Agregar Variables en Vercel

1. En la página de configuración del proyecto, ve a **"Settings"** → **"Environment Variables"**
2. Haz clic en **"Add New"**
3. Ingresa el **Name** y **Value**
4. Selecciona los **Environments** donde aplicará:
   - ✅ Production
   - ✅ Preview
   - ✅ Development (opcional)
5. Haz clic en **"Save"**

---

## 🚀 Paso 5: Desplegar

### 5.1 Primer Despliegue

1. Después de configurar las variables, haz clic en **"Deploy"**
2. Vercel comenzará a:
   - Instalar dependencias (`npm install`)
   - Construir el proyecto (`npm run build`)
   - Desplegar a producción

### 5.2 Monitorear el Despliegue

- Verás el progreso en tiempo real
- Si hay errores, aparecerán en los logs
- El despliegue tarda 2-5 minutos normalmente

### 5.3 Verificar el Despliegue

Una vez completado, Vercel te dará una URL como:
```
https://codex-trader-frontend.vercel.app
```

Haz clic en la URL para ver tu aplicación en vivo.

---

## ⚙️ Paso 6: Configurar Supabase para Producción

### 6.1 Actualizar Redirect URLs en Supabase

1. Ve a tu [Dashboard de Supabase](https://app.supabase.com)
2. Selecciona tu proyecto
3. Ve a **Authentication** → **URL Configuration**
4. En **"Redirect URLs"**, agrega:
   ```
   https://tu-dominio.vercel.app/auth/callback
   https://tu-dominio.vercel.app
   ```
5. En **"Site URL"**, cambia a:
   ```
   https://tu-dominio.vercel.app
   ```
6. Haz clic en **"Save"**

### 6.2 Verificar Email Templates

1. Ve a **Authentication** → **Email Templates**
2. Verifica que los templates usen la URL correcta:
   - En los enlaces de confirmación, debe aparecer: `https://tu-dominio.vercel.app/auth/callback`
   - Si usas templates personalizados, actualiza las URLs

---

## 🔗 Paso 7: Configurar Dominio Personalizado (Opcional)

### 7.1 Agregar Dominio en Vercel

1. En el dashboard de Vercel, ve a **Settings** → **Domains**
2. Ingresa tu dominio (ej: `codextrader.com`)
3. Sigue las instrucciones para configurar DNS

### 7.2 Configurar DNS

Vercel te dará registros DNS para agregar en tu proveedor de dominio:

- **Tipo A:** Apunta a la IP de Vercel
- **Tipo CNAME:** Apunta a `cname.vercel-dns.com`

### 7.3 Actualizar Variables de Entorno

Después de configurar el dominio, actualiza:

```
FRONTEND_URL=https://tu-dominio.com
```

En tu backend (Railway/Render) y en Supabase.

---

## 🔄 Paso 8: Configurar Despliegues Automáticos

### 8.1 Conectar con Git

Vercel ya está conectado a tu repositorio Git. Cada vez que hagas `git push`:

- Se creará un **Preview Deployment** (para branches que no sean `main`)
- Se actualizará **Production** (cuando hagas push a `main`)

### 8.2 Configurar Branch de Producción

1. Ve a **Settings** → **Git**
2. Verifica que **Production Branch** sea `main` (o `master`)
3. Opcionalmente, configura **Ignored Build Step** si necesitas saltar builds

---

## ✅ Paso 9: Verificar que Todo Funciona

### 9.1 Checklist de Verificación

- [ ] ✅ La aplicación carga en la URL de Vercel
- [ ] ✅ El login/registro funciona
- [ ] ✅ La confirmación de email funciona
- [ ] ✅ Los emails de bienvenida se envían
- [ ] ✅ El chat se conecta al backend
- [ ] ✅ Los planes y pagos funcionan
- [ ] ✅ Los enlaces de referidos funcionan

### 9.2 Probar Flujo Completo

1. **Registro:**
   - Registra un usuario nuevo
   - Verifica que llegue el email de confirmación
   - Confirma el email
   - Verifica que llegue el email de bienvenida

2. **Login:**
   - Inicia sesión con el usuario creado
   - Verifica que la sesión se mantenga

3. **Chat:**
   - Envía un mensaje en el chat
   - Verifica que se conecte al backend

4. **Referidos:**
   - Verifica que el código de referido aparezca
   - Prueba el enlace de invitación

---

## 🐛 Solución de Problemas Comunes

### Error: "Module not found"

**Solución:**
- Verifica que todas las dependencias estén en `package.json`
- Ejecuta `npm install` localmente y verifica que no haya errores

### Error: "Environment variable not found"

**Solución:**
- Verifica que todas las variables `NEXT_PUBLIC_*` estén configuradas en Vercel
- Asegúrate de que los nombres sean exactos (case-sensitive)
- Reinicia el despliegue después de agregar variables

### Error: "Build failed"

**Solución:**
- Revisa los logs de build en Vercel
- Prueba el build localmente: `npm run build`
- Verifica que no haya errores de TypeScript: `npm run lint`

### Error: "Supabase redirect URL mismatch"

**Solución:**
- Verifica que la URL en Supabase sea exactamente la de Vercel
- Asegúrate de incluir `https://` y el path completo `/auth/callback`
- Espera unos minutos después de actualizar en Supabase

### Error: "Backend connection failed"

**Solución:**
- Verifica que `NEXT_PUBLIC_BACKEND_URL` esté configurada correctamente
- Asegúrate de que el backend esté desplegado y accesible
- Verifica que el backend permita CORS desde tu dominio de Vercel

---

## 📝 Resumen de Variables de Entorno

### Frontend (Vercel)

```env
# Supabase (públicas)
NEXT_PUBLIC_SUPABASE_URL=https://tu-proyecto.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=tu_anon_key

# Backend (pública)
NEXT_PUBLIC_BACKEND_URL=https://tu-backend.railway.app

# Backend (privada, solo para API routes)
BACKEND_URL=https://tu-backend.railway.app
```

### Backend (Railway/Render)

```env
# Supabase
SUPABASE_URL=https://tu-proyecto.supabase.co
SUPABASE_SERVICE_KEY=tu_service_key

# Frontend
FRONTEND_URL=https://tu-dominio.vercel.app

# Email
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=tu_email@gmail.com
SMTP_PASS=tu_app_password
EMAIL_FROM="Codex Trader <tu_email@gmail.com>"
ADMIN_EMAIL=tu_email@gmail.com

# Stripe (si usas pagos)
STRIPE_SECRET_KEY=sk_live_...
STRIPE_WEBHOOK_SECRET=whsec_...
# ... otros
```

---

## 🎉 ¡Listo!

Tu frontend debería estar funcionando en Vercel. Cada vez que hagas cambios y los subas a Git, Vercel los desplegará automáticamente.

### Próximos Pasos

1. **Configurar dominio personalizado** (opcional pero recomendado)
2. **Configurar monitoreo** (Vercel Analytics)
3. **Configurar backups** (si es necesario)
4. **Optimizar performance** (imágenes, bundle size, etc.)

---

## 📞 Soporte

Si tienes problemas:

1. Revisa los logs en Vercel: **Deployments** → Selecciona un deployment → **View Function Logs**
2. Revisa la documentación de Vercel: [https://vercel.com/docs](https://vercel.com/docs)
3. Revisa la documentación de Next.js: [https://nextjs.org/docs](https://nextjs.org/docs)

---

**¡Éxito con tu despliegue! 🚀**

