# ✅ Backend Desplegado en Railway

## 🌐 URL de Producción

```
https://web-production-3ab35.up.railway.app
```

## 📋 Endpoints Importantes

### Documentación de la API
```
https://web-production-3ab35.up.railway.app/docs
```

### Health Check
```
https://web-production-3ab35.up.railway.app/health
```

### Test Email (solo desarrollo)
```
POST https://web-production-3ab35.up.railway.app/debug/test-email
```

---

## ⚙️ Próximos Pasos

### 1. Verificar que Funciona

1. **Abre la documentación:**
   - Ve a: https://web-production-3ab35.up.railway.app/docs
   - Deberías ver Swagger UI con todos los endpoints

2. **Prueba el health check:**
   - Ve a: https://web-production-3ab35.up.railway.app/health
   - Debería responder: `{"status": "ok"}`

### 2. Configurar Variables de Entorno en Railway

Asegúrate de que todas las variables estén configuradas en Railway:

**Variables Obligatorias:**
- `SUPABASE_URL`
- `SUPABASE_SERVICE_KEY`
- `FRONTEND_URL` (puede ser temporal: `http://localhost:3000`)
- `SMTP_HOST`, `SMTP_PORT`, `SMTP_USER`, `SMTP_PASS`
- `EMAIL_FROM`, `ADMIN_EMAIL`
- `DEEPSEEK_API_KEY` (o `OPENAI_API_KEY`)
- `CHAT_MODEL`

Ver: `VARIABLES_RAILWAY.md` para la lista completa.

### 3. Actualizar FRONTEND_URL

Cuando despliegues el frontend en Vercel:

1. Obtén la URL de Vercel (ej: `https://codex-trader.vercel.app`)
2. Ve a Railway → Variables
3. Actualiza `FRONTEND_URL` con la URL de Vercel
4. Railway reiniciará automáticamente

### 4. Configurar Webhooks de Stripe (si usas pagos)

1. Ve a [Dashboard de Stripe](https://dashboard.stripe.com)
2. **Developers** → **Webhooks**
3. Crea un webhook apuntando a:
   ```
   https://web-production-3ab35.up.railway.app/stripe/webhook
   ```
4. Selecciona los eventos:
   - `checkout.session.completed`
   - `invoice.paid`
5. Copia el **Signing secret** y agrégalo a Railway como `STRIPE_WEBHOOK_SECRET`

### 5. Configurar Supabase

1. Ve a tu [Dashboard de Supabase](https://app.supabase.com)
2. **Settings** → **API**
3. Verifica que las URLs estén correctas
4. Cuando tengas el frontend, actualiza **Redirect URLs** con la URL de Vercel

---

## ✅ Checklist de Verificación

- [ ] Backend responde en la URL de Railway
- [ ] `/docs` muestra la documentación
- [ ] `/health` responde correctamente
- [ ] Variables de entorno configuradas en Railway
- [ ] Logs no muestran errores críticos
- [ ] Conexión a Supabase funciona
- [ ] Email SMTP configurado (prueba con `/debug/test-email`)

---

## 🔗 URLs para Configurar en Otros Servicios

### Frontend (Vercel)
Cuando despliegues el frontend, configura:
```
NEXT_PUBLIC_BACKEND_URL=https://web-production-3ab35.up.railway.app
```

### Supabase
En **Redirect URLs**, agrega:
```
https://web-production-3ab35.up.railway.app/auth/callback
```
(Después de desplegar el frontend, agrega también la URL de Vercel)

### Stripe Webhooks
```
https://web-production-3ab35.up.railway.app/stripe/webhook
```

---

## 🎉 ¡Backend Listo!

Tu backend está funcionando en Railway. Ahora puedes:

1. ✅ Desplegar el frontend en Vercel
2. ✅ Configurar las variables de entorno
3. ✅ Probar los endpoints
4. ✅ Conectar todo el sistema

---

**URL Guardada:** `https://web-production-3ab35.up.railway.app`

