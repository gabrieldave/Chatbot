# ✅ Checklist de Despliegue en Vercel

Usa esta checklist para asegurarte de que todo esté configurado correctamente antes y después del despliegue.

---

## 📋 Antes del Despliegue

### Repositorio Git
- [ ] Código subido a GitHub/GitLab/Bitbucket
- [ ] `.env` está en `.gitignore` (no se sube al repo)
- [ ] `node_modules` está en `.gitignore`
- [ ] Build funciona localmente: `npm run build`

### Variables de Entorno (Preparar)
- [ ] Tienes la URL de Supabase: `https://tu-proyecto.supabase.co`
- [ ] Tienes la Anon Key de Supabase
- [ ] Tienes la URL del backend en producción
- [ ] Tienes el dominio de Vercel (o lo configurarás después)

---

## 🚀 Durante el Despliegue

### Vercel - Configuración Inicial
- [ ] Cuenta creada en Vercel
- [ ] Proyecto importado desde Git
- [ ] Framework detectado: Next.js
- [ ] Root Directory configurado (si aplica)

### Variables de Entorno en Vercel
- [ ] `NEXT_PUBLIC_SUPABASE_URL` configurada
- [ ] `NEXT_PUBLIC_SUPABASE_ANON_KEY` configurada
- [ ] `NEXT_PUBLIC_BACKEND_URL` configurada
- [ ] `BACKEND_URL` configurada (si usas API routes)
- [ ] Todas las variables marcadas para Production

### Primer Despliegue
- [ ] Build completado sin errores
- [ ] Deployment exitoso
- [ ] URL de Vercel funcionando

---

## ⚙️ Después del Despliegue

### Supabase
- [ ] Redirect URL actualizada: `https://tu-dominio.vercel.app/auth/callback`
- [ ] Site URL actualizada: `https://tu-dominio.vercel.app`
- [ ] Email templates actualizados (si aplica)

### Backend
- [ ] `FRONTEND_URL` actualizada en backend con URL de Vercel
- [ ] CORS configurado para permitir dominio de Vercel
- [ ] Backend accesible desde internet

### Pruebas Funcionales
- [ ] **Registro de usuario:**
  - [ ] Formulario de registro funciona
  - [ ] Email de confirmación llega
  - [ ] Confirmación de email funciona
  - [ ] Email de bienvenida llega
  - [ ] Código de referido aparece en email

- [ ] **Login:**
  - [ ] Login funciona correctamente
  - [ ] Sesión se mantiene al recargar
  - [ ] Logout funciona

- [ ] **Chat:**
  - [ ] Chat se conecta al backend
  - [ ] Mensajes se envían y reciben
  - [ ] Historial se carga

- [ ] **Planes y Pagos:**
  - [ ] Página de planes carga
  - [ ] Checkout de Stripe funciona
  - [ ] Webhooks de Stripe funcionan

- [ ] **Referidos:**
  - [ ] Código de referido se muestra
  - [ ] Enlace de invitación funciona
  - [ ] URL usa FRONTEND_URL correcto

- [ ] **Admin:**
  - [ ] Panel de admin accesible
  - [ ] Reportes de costos funcionan

---

## 🔍 Verificación Técnica

### Logs y Errores
- [ ] Revisar logs de Vercel (no hay errores críticos)
- [ ] Revisar logs del backend (no hay errores de conexión)
- [ ] Revisar consola del navegador (no hay errores de JS)

### Performance
- [ ] Página carga en menos de 3 segundos
- [ ] Imágenes se optimizan correctamente
- [ ] Bundle size razonable (< 1MB inicial)

### Seguridad
- [ ] Variables de entorno no expuestas en el cliente (excepto NEXT_PUBLIC_*)
- [ ] HTTPS habilitado en Vercel
- [ ] CORS configurado correctamente

---

## 🌐 Dominio Personalizado (Opcional)

Si configuraste un dominio personalizado:

- [ ] Dominio agregado en Vercel
- [ ] DNS configurado correctamente
- [ ] SSL/HTTPS activado automáticamente
- [ ] `FRONTEND_URL` actualizada en backend y Supabase
- [ ] Redirect URLs en Supabase actualizadas con nuevo dominio

---

## 📊 Monitoreo (Opcional)

- [ ] Vercel Analytics configurado (opcional)
- [ ] Error tracking configurado (opcional, ej: Sentry)
- [ ] Uptime monitoring configurado (opcional)

---

## ✅ Finalización

- [ ] Todo funciona correctamente
- [ ] Documentación actualizada
- [ ] Equipo notificado del despliegue
- [ ] Backup de configuración guardado

---

**Fecha de Despliegue:** _______________

**URL de Producción:** _______________

**Notas:** _______________

---

¡Despliegue completado! 🎉

