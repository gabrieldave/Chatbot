# 🚀 Script para Subir Código a GitHub

Sigue estos pasos para subir tu código a GitHub.

---

## 📋 Paso 1: Verificar Estado de Git

Abre PowerShell o CMD en la carpeta raíz del proyecto (`MI_SAAS_BOT`) y ejecuta:

```powershell
git status
```

Si ves "fatal: not a git repository", necesitas inicializar Git.

---

## 🔧 Paso 2: Inicializar Git (si es necesario)

Si Git no está inicializado, ejecuta:

```powershell
git init
```

---

## 📝 Paso 3: Agregar Archivos

Agrega todos los archivos al staging:

```powershell
git add .
```

Verifica qué se agregó:

```powershell
git status
```

---

## 💾 Paso 4: Hacer Commit Inicial

```powershell
git commit -m "Initial commit: Codex Trader - Frontend y Backend"
```

---

## 🌐 Paso 5: Crear Repositorio en GitHub

1. Ve a [https://github.com](https://github.com)
2. Haz clic en el botón **"+"** (arriba derecha) → **"New repository"**
3. Completa:
   - **Repository name:** `codex-trader` (o el nombre que prefieras)
   - **Description:** "Codex Trader - SaaS de Trading con IA"
   - **Visibility:** 
     - ✅ **Public** (gratis, visible para todos)
     - ⚠️ **Private** (requiere plan de pago o GitHub Pro)
   - ⚠️ **NO** marques "Add a README file"
   - ⚠️ **NO** marques "Add .gitignore"
   - ⚠️ **NO** marques "Choose a license"
4. Haz clic en **"Create repository"**

---

## 🔗 Paso 6: Conectar con GitHub

GitHub te mostrará comandos. Usa estos (reemplaza `TU_USUARIO` con tu usuario de GitHub):

```powershell
git remote add origin https://github.com/TU_USUARIO/codex-trader.git
git branch -M main
git push -u origin main
```

**Si GitHub te pide autenticación:**
- Si usas HTTPS, GitHub te pedirá usuario y contraseña
- Para contraseña, usa un **Personal Access Token** (no tu contraseña normal)
- Cómo crear un token: [GitHub Docs - Personal Access Tokens](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/creating-a-personal-access-token)

---

## ✅ Paso 7: Verificar

1. Ve a tu repositorio en GitHub: `https://github.com/TU_USUARIO/codex-trader`
2. Verifica que todos los archivos estén ahí
3. Verifica que `.env` **NO** esté en el repositorio (debe estar en `.gitignore`)

---

## 🔄 Paso 8: Futuros Cambios

Cada vez que hagas cambios, usa:

```powershell
git add .
git commit -m "Descripción de los cambios"
git push
```

---

## ⚠️ Notas Importantes

### Archivos que NO deben subirse:
- ✅ `.env` (ya está en `.gitignore`)
- ✅ `node_modules/` (ya está en `.gitignore`)
- ✅ `.next/` (ya está en `.gitignore`)
- ✅ `__pycache__/` (ya está en `.gitignore`)
- ✅ `*.log` (ya está en `.gitignore`)

### Si necesitas crear un Personal Access Token:

1. Ve a GitHub → **Settings** → **Developer settings** → **Personal access tokens** → **Tokens (classic)**
2. Haz clic en **"Generate new token (classic)"**
3. Selecciona los scopes:
   - ✅ `repo` (acceso completo a repositorios)
4. Genera el token y **cópialo inmediatamente** (no podrás verlo después)
5. Úsalo como contraseña cuando Git te la pida

---

## 🆘 Problemas Comunes

### "remote origin already exists"
```powershell
git remote remove origin
git remote add origin https://github.com/TU_USUARIO/codex-trader.git
```

### "Authentication failed"
- Verifica que estés usando un Personal Access Token, no tu contraseña
- Verifica que el token tenga permisos de `repo`

### "Permission denied"
- Verifica que el nombre del repositorio sea correcto
- Verifica que tengas permisos de escritura en el repositorio

---

**¡Listo para conectar con Vercel! 🎉**

