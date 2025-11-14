# 📁 Cómo Configurar Root Directory en Vercel

## ⚠️ Problema

Vercel no muestra "frontend" en la lista de directorios porque es un **submódulo de Git**.

---

## ✅ Solución: Escribir Manualmente

### Opción 1: En el Diálogo Actual

1. **NO selecciones "Chatbot"** (ese es el directorio raíz)
2. **Haz clic en el campo de texto** donde dice "Chatbot" o donde puedes escribir
3. **Escribe manualmente:** `frontend`
4. **Haz clic en "Continue"**

### Opción 2: Después del Deploy

Si ya hiciste deploy con "Chatbot":

1. Ve a tu proyecto en Vercel Dashboard
2. **Settings** → **General**
3. Busca **"Root Directory"**
4. Haz clic en **"Edit"**
5. Escribe: `frontend`
6. Haz clic en **"Save"**
7. Vercel reiniciará el despliegue automáticamente

---

## 🔍 Verificación

Después de configurar `frontend` como Root Directory:

1. Vercel solo construirá el código en `frontend/`
2. El build será mucho más rápido
3. No intentará instalar dependencias de Python
4. El tamaño será < 50 MB

---

## 📋 Configuración Completa

Después de configurar Root Directory, asegúrate de:

1. **Framework Preset:** Next.js
2. **Root Directory:** `frontend` (escrito manualmente)
3. **Build Command:** `npm run build` (activado)
4. **Install Command:** `npm install` (activado)
5. **Variables de entorno:** Configuradas correctamente

---

**⚠️ IMPORTANTE:** Escribe `frontend` manualmente en el campo, no selecciones de la lista.

