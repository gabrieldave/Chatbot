# 🚀 INSTRUCCIONES PARA INICIAR EL SISTEMA

## ✅ Configuración Verificada

- ✅ **DEEPSEEK_API_KEY**: Configurada
- ✅ **CHAT_MODEL**: deepseek/deepseek-chat (se usará DeepSeek)
- ✅ **Backend**: FastAPI en `main.py`
- ✅ **Frontend**: Next.js en `../frontend/`

---

## 🚀 Opción 1: Iniciar Todo de Una Vez (Recomendado)

### Doble clic en:
```
iniciar_backend_y_frontend.bat
```

Esto iniciará:
- ✅ Backend en una ventana (http://localhost:8000)
- ✅ Frontend en otra ventana (http://localhost:3000)

---

## 🔧 Opción 2: Iniciar por Separado

### Backend (DeepSeek):
Doble clic en:
```
iniciar_backend_deepseek.bat
```

O desde terminal:
```bash
start cmd /k "cd /d %CD% && python main.py"
```

### Frontend (Next.js):
Doble clic en:
```
iniciar_frontend_nextjs.bat
```

O desde terminal:
```bash
start cmd /k "cd /d %CD%\..\frontend && npm run dev"
```

---

## 📊 URLs del Sistema

- **Backend API**: http://localhost:8000
- **Frontend**: http://localhost:3000 (o el puerto que Next.js asigne)
- **API Docs**: http://localhost:8000/docs (Swagger UI)

---

## 🔍 Verificar que Está Corriendo

### Ver puertos activos:
```bash
netstat -ano | findstr ":8000 :3000"
```

### Ver procesos:
```bash
tasklist | findstr "python node"
```

---

## ⚙️ Configuración de DeepSeek

El sistema está configurado para usar **DeepSeek** como modelo de chat.

**Configuración actual**:
- `CHAT_MODEL=deepseek/deepseek-chat` (o `deepseek-chat`)
- `DEEPSEEK_API_KEY` configurada

**Nota**: Se corrigió el código para que respete `CHAT_MODEL` y no cambie automáticamente a OpenAI.

---

## 🛑 Detener el Sistema

Presiona **Ctrl+C** en cada ventana de terminal para detener:
- Backend: Ctrl+C en la ventana del backend
- Frontend: Ctrl+C en la ventana del frontend

O usa:
```bash
python detener_todos_procesos.py
```

---

## 📝 Logs

Los logs aparecerán en las ventanas de terminal:
- **Backend**: Verás mensajes de FastAPI, consultas RAG, uso de DeepSeek
- **Frontend**: Verás mensajes de Next.js, compilación, etc.

---

**✅ Usa `iniciar_backend_y_frontend.bat` para iniciar todo fácilmente!**



