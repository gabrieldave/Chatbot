# ✅ Checklist de Despliegue en Railway

Usa esta checklist para asegurarte de que todo esté configurado correctamente antes y después del despliegue.

---

## 📋 Antes del Despliegue

### Preparación
- [ ] Cuenta creada en Railway
- [ ] Repositorio en GitHub (ya lo tienes: `gabrieldave/Chatbot`)
- [ ] Archivos verificados:
  - [ ] `Procfile` existe y está correcto
  - [ ] `requirements.txt` tiene todas las dependencias
  - [ ] `runtime.txt` tiene versión de Python válida
  - [ ] `main.py` usa `PORT` de Railway

### Variables de Entorno (Preparar)
- [ ] Tienes la URL de Supabase
- [ ] Tienes la Service Key de Supabase
- [ ] Tienes las credenciales de Gmail (App Password)
- [ ] Tienes las API keys de IA (OpenAI/Deepseek)
- [ ] Tienes las keys de Stripe (si usas pagos)

---

## 🚀 Durante el Despliegue

### Railway - Configuración Inicial
- [ ] Proyecto creado en Railway
- [ ] Repositorio conectado: `gabrieldave/Chatbot`
- [ ] Root Directory configurado: `backend`
- [ ] Branch configurado: `main`

### Variables de Entorno en Railway
- [ ] `SUPABASE_URL` configurada
- [ ] `SUPABASE_SERVICE_KEY` configurada
- [ ] `FRONTEND_URL` configurada (puede ser temporal: `http://localhost:3000` por ahora)
- [ ] `SMTP_HOST` configurada: `smtp.gmail.com`
- [ ] `SMTP_PORT` configurada: `587`
- [ ] `SMTP_USER` configurada
- [ ] `SMTP_PASS` configurada (App Password de Gmail)
- [ ] `EMAIL_FROM` configurada
- [ ] `ADMIN_EMAIL` configurada
- [ ] `OPENAI_API_KEY` o `DEEPSEEK_API_KEY` configurada
- [ ] `CHAT_MODEL` configurada (si aplica)
- [ ] Variables de Stripe configuradas (si usas pagos)

### Primer Despliegue
- [ ] Build completado sin errores
- [ ] Deployment exitoso
- [ ] URL de Railway funcionando

---

## ⚙️ Después del Despliegue

### Verificación Técnica
- [ ] URL de Railway accesible
- [ ] `/docs` muestra la documentación de FastAPI
- [ ] `/health` responde correctamente
- [ ] Logs no muestran errores críticos
- [ ] Conexión a Supabase funciona

### Pruebas Funcionales
- [ ] **API:**
  - [ ] Endpoint `/docs` carga
  - [ ] Endpoint `/health` responde
  - [ ] Endpoint `/chat` funciona (si aplica)

- [ ] **Email:**
  - [ ] Endpoint `/debug/test-email` funciona
  - [ ] Email de prueba llega correctamente

- [ ] **Supabase:**
  - [ ] Conexión a base de datos funciona
  - [ ] Queries a la base de datos funcionan

### Configuración Adicional
- [ ] Dominio personalizado configurado (opcional)
- [ ] Webhooks de Stripe configurados con URL de Railway (si aplica)
- [ ] `FRONTEND_URL` actualizada cuando despliegues el frontend

---

## 🔍 Verificación de Logs

### Revisar Logs en Railway
- [ ] No hay errores de importación
- [ ] No hay errores de conexión a Supabase
- [ ] No hay errores de variables de entorno faltantes
- [ ] El servidor inicia correctamente en el puerto asignado

---

## 📝 URLs Importantes

Anota estas URLs:

**Backend Railway:**
```
https://tu-proyecto.up.railway.app
```

**Documentación API:**
```
https://tu-proyecto.up.railway.app/docs
```

**Health Check:**
```
https://tu-proyecto.up.railway.app/health
```

---

## 🔄 Próximos Pasos

Después de desplegar el backend:

- [ ] Guardar URL de Railway
- [ ] Desplegar frontend en Vercel
- [ ] Actualizar `FRONTEND_URL` en Railway con URL de Vercel
- [ ] Configurar webhooks de Stripe con URL de Railway
- [ ] Actualizar `NEXT_PUBLIC_BACKEND_URL` en Vercel con URL de Railway

---

## ✅ Finalización

- [ ] Backend funcionando correctamente
- [ ] URL guardada para usar en frontend
- [ ] Variables de entorno configuradas
- [ ] Logs sin errores críticos
- [ ] Listo para conectar con frontend

---

**Fecha de Despliegue:** _______________

**URL de Producción:** _______________

**Notas:** _______________

---

¡Despliegue completado! 🚂

