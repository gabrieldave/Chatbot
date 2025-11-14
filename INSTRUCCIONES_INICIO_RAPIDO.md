# 🚀 INICIO RÁPIDO - BACKEND Y FRONTEND

## ✅ Scripts Creados

He creado scripts `.bat` para iniciar fácilmente:

### 1. Iniciar Todo (Backend + Frontend)
**Doble clic en**: `iniciar_backend_y_frontend.bat`

### 2. Solo Backend
**Doble clic en**: `iniciar_backend_deepseek.bat`

### 3. Solo Frontend
**Doble clic en**: `iniciar_frontend_nextjs.bat`

---

## 🔧 Configuración DeepSeek

**Estado actual**:
- ✅ DEEPSEEK_API_KEY: Configurada
- ✅ CHAT_MODEL: `deepseek/deepseek-chat`

**Nota**: El código en `main.py` tiene lógica que puede priorizar OpenAI si está disponible. Para forzar DeepSeek, asegúrate de que `CHAT_MODEL=deepseek-chat` (sin "deepseek/" al inicio) en tu `.env`.

---

## 📡 URLs del Sistema

Una vez iniciado:
- **Backend**: http://localhost:8000
- **Frontend**: http://localhost:3000
- **API Docs**: http://localhost:8000/docs

---

## 🎯 Verificar que Está Corriendo

```bash
# Ver puertos
netstat -ano | findstr ":8000 :3000"

# Ver procesos
tasklist | findstr "python node"
```

---

## 💡 Si los Scripts .bat No Funcionan

Ejecuta manualmente en ventanas de terminal separadas:

**Terminal 1 (Backend)**:
```bash
cd C:\Users\dakyo\Documents\Proyectos de apps\MI_SAAS_BOT\backend
python main.py
```

**Terminal 2 (Frontend)**:
```bash
cd C:\Users\dakyo\Documents\Proyectos de apps\MI_SAAS_BOT\frontend
npm run dev
```

---

**✅ Los scripts .bat deberían abrir ventanas visibles automáticamente!**



