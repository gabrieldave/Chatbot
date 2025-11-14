# Guía de Despliegue en Vercel - CODEX TRADER

Esta guía te ayudará a desplegar el frontend de CODEX TRADER en Vercel y el backend en un servicio compatible.

## 📋 Requisitos Previos

1. Cuenta en [Vercel](https://vercel.com)
2. Cuenta en [Supabase](https://supabase.com) (ya configurada)
3. Backend desplegado en Railway, Render, o similar (ver sección de Backend)

---

## 🚀 Paso 1: Desplegar el Backend

El backend (FastAPI) necesita estar desplegado en un servicio que soporte Python. Recomendamos:

### Opción A: Railway (Recomendado)
1. Ve a [Railway](https://railway.app)
2. Crea un nuevo proyecto
3. Conecta tu repositorio o sube el código del backend
4. Railway detectará automáticamente que es Python
5. Configura las variables de entorno (ver sección de Variables de Entorno)
6. Railway te dará una URL como: `https://tu-proyecto.railway.app`

### Opción B: Render
1. Ve a [Render](https://render.com)
2. Crea un nuevo "Web Service"
3. Conecta tu repositorio
4. Configura:
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `uvicorn main:app --host 0.0.0.0 --port $PORT`
5. Configura las variables de entorno
6. Render te dará una URL como: `https://tu-proyecto.onrender.com`

### Variables de Entorno del Backend

Configura estas variables en tu servicio de backend:

```env
SUPABASE_URL=tu_supabase_url
SUPABASE_SERVICE_KEY=tu_service_key
SUPABASE_DB_PASSWORD=tu_db_password
OPENAI_API_KEY=tu_openai_key
DEEPSEEK_API_KEY=tu_deepseek_key (opcional)
CHAT_MODEL=deepseek/deepseek-chat (opcional)
```

---

## 🌐 Paso 2: Desplegar el Frontend en Vercel

### 2.1 Preparación Local

1. **Asegúrate de estar en el directorio del frontend:**
   ```bash
   cd frontend
   ```

2. **Verifica que el build funciona:**
   ```bash
   npm run build
   ```

3. **Verifica que todas las variables de entorno estén configuradas:**
   - Revisa `.env.local.example` para ver qué variables necesitas

### 2.2 Despliegue desde Vercel Dashboard

1. **Ve a [Vercel Dashboard](https://vercel.com/dashboard)**

2. **Haz clic en "Add New Project"**

3. **Importa tu repositorio:**
   - Conecta tu cuenta de GitHub/GitLab/Bitbucket
   - Selecciona el repositorio de CODEX TRADER
   - Selecciona el directorio `frontend` como raíz del proyecto

4. **Configura el proyecto:**
   - **Framework Preset**: Next.js (debería detectarse automáticamente)
   - **Root Directory**: `frontend`
   - **Build Command**: `npm run build` (por defecto)
   - **Output Directory**: `.next` (por defecto)

5. **Configura las Variables de Entorno:**
   
   Haz clic en "Environment Variables" y agrega:

   ```
   NEXT_PUBLIC_SUPABASE_URL=tu_supabase_url
   NEXT_PUBLIC_SUPABASE_ANON_KEY=tu_supabase_anon_key
   BACKEND_URL=https://tu-backend.railway.app (o tu URL de backend)
   NEXT_PUBLIC_BACKEND_URL=https://tu-backend.railway.app
   ```

   **Importante**: 
   - Las variables que empiezan con `NEXT_PUBLIC_` son accesibles desde el cliente
   - `BACKEND_URL` es solo para las API routes del servidor
   - `NEXT_PUBLIC_BACKEND_URL` es para llamadas directas desde el cliente (si las hay)

6. **Haz clic en "Deploy"**

### 2.3 Despliegue desde CLI (Alternativa)

1. **Instala Vercel CLI:**
   ```bash
   npm i -g vercel
   ```

2. **Inicia sesión:**
   ```bash
   vercel login
   ```

3. **Navega al directorio frontend:**
   ```bash
   cd frontend
   ```

4. **Despliega:**
   ```bash
   vercel
   ```

5. **Sigue las instrucciones:**
   - Selecciona el scope (tu cuenta)
   - Confirma el proyecto
   - Vercel detectará Next.js automáticamente

6. **Configura las variables de entorno:**
   ```bash
   vercel env add NEXT_PUBLIC_SUPABASE_URL
   vercel env add NEXT_PUBLIC_SUPABASE_ANON_KEY
   vercel env add BACKEND_URL
   vercel env add NEXT_PUBLIC_BACKEND_URL
   ```

7. **Despliega a producción:**
   ```bash
   vercel --prod
   ```

---

## ✅ Paso 3: Verificación Post-Despliegue

1. **Verifica que el frontend carga:**
   - Visita la URL que Vercel te proporcionó
   - Deberías ver la pantalla de login

2. **Verifica la conexión con el backend:**
   - Intenta iniciar sesión
   - Si hay errores, revisa la consola del navegador
   - Verifica que `BACKEND_URL` esté correctamente configurada

3. **Verifica las variables de entorno:**
   - En Vercel Dashboard → Tu Proyecto → Settings → Environment Variables
   - Asegúrate de que todas estén configuradas para "Production"

---

## 🔧 Solución de Problemas

### Error: "Cannot connect to backend"
- Verifica que `BACKEND_URL` esté configurada correctamente
- Verifica que el backend esté desplegado y accesible
- Verifica que el backend permita CORS desde tu dominio de Vercel

### Error: "Supabase authentication failed"
- Verifica `NEXT_PUBLIC_SUPABASE_URL` y `NEXT_PUBLIC_SUPABASE_ANON_KEY`
- Asegúrate de que las URLs de Supabase estén configuradas para permitir tu dominio de Vercel

### Error: "Build failed"
- Revisa los logs de build en Vercel
- Verifica que todas las dependencias estén en `package.json`
- Asegúrate de que `npm run build` funcione localmente

### CORS Issues
Si el backend rechaza peticiones desde Vercel:

1. En `backend/main.py`, verifica la configuración de CORS:
   ```python
   app.add_middleware(
       CORSMiddleware,
       allow_origins=["*"],  # En producción, especifica tu dominio de Vercel
       allow_credentials=True,
       allow_methods=["*"],
       allow_headers=["*"],
   )
   ```

2. Para producción, cambia a:
   ```python
   allow_origins=[
       "https://tu-proyecto.vercel.app",
       "https://www.tu-dominio.com"
   ]
   ```

---

## 📝 Checklist Final

- [ ] Backend desplegado y accesible
- [ ] Variables de entorno del backend configuradas
- [ ] Frontend desplegado en Vercel
- [ ] Variables de entorno de Vercel configuradas
- [ ] CORS configurado en el backend
- [ ] Login funciona correctamente
- [ ] Chat funciona correctamente
- [ ] Tokens se cargan correctamente

---

## 🔄 Actualizaciones Futuras

Para actualizar el proyecto después de cambios:

1. **Haz push a tu repositorio:**
   ```bash
   git add .
   git commit -m "Actualización"
   git push
   ```

2. **Vercel desplegará automáticamente** si tienes integración con Git
   - O ejecuta `vercel --prod` manualmente

---

## 📚 Recursos Adicionales

- [Documentación de Vercel](https://vercel.com/docs)
- [Documentación de Next.js](https://nextjs.org/docs)
- [Documentación de Railway](https://docs.railway.app)
- [Documentación de Render](https://render.com/docs)

---

¡Listo! Tu aplicación CODEX TRADER debería estar funcionando en producción. 🚀

