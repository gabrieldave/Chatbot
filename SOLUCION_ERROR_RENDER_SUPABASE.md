# 🔧 Solución: Error de Supabase en Render

## ❌ Error

```
ValueError: 'db.eixvqedpyuybfywmdulg.supabase.co' does not appear to be an IPv4 or IPv6 address
```

## 🔍 Causa

El problema es que `SUPABASE_DB_URL` está configurada incorrectamente o tiene un formato que Python 3.13 no puede parsear. El código intenta derivar la URL REST desde `SUPABASE_DB_URL`, pero falla al parsear la URL.

## ✅ Solución

### Opción 1: Usar SUPABASE_URL (Recomendado - Más Simple)

En Render Dashboard → Environment, configura:

```env
SUPABASE_URL=https://eixvqedpyuybfywmdulg.supabase.co
```

**⚠️ IMPORTANTE:**
- Debe empezar con `https://`
- Debe terminar en `.supabase.co` (NO `.com`)
- NO debe tener espacios
- NO uses comillas

**NO configures `SUPABASE_DB_URL`** si usas esta opción.

### Opción 2: Si necesitas usar SUPABASE_DB_URL

Si realmente necesitas usar `SUPABASE_DB_URL`, debe tener este formato exacto:

```env
SUPABASE_DB_URL=postgresql://postgres:TU_PASSWORD@db.eixvqedpyuybfywmdulg.supabase.co:5432/postgres
```

**⚠️ IMPORTANTE:**
- Debe empezar con `postgresql://` o `postgres://`
- Debe incluir el usuario: `postgres`
- Debe incluir la contraseña: `TU_PASSWORD`
- Debe incluir el host: `db.eixvqedpyuybfywmdulg.supabase.co`
- Debe incluir el puerto: `:5432`
- Debe incluir la base de datos: `/postgres`

## 📋 Pasos para Corregir en Render

1. **Ve a Render Dashboard** → Tu Servicio → **Environment**

2. **Elimina `SUPABASE_DB_URL`** si está configurada (o déjala vacía)

3. **Configura `SUPABASE_URL`** con el valor:
   ```
   SUPABASE_URL=https://eixvqedpyuybfywmdulg.supabase.co
   ```

4. **Verifica que `SUPABASE_SERVICE_KEY` esté configurada** (debe ser la service_role key completa)

5. **Haz clic en "Save Changes"**

6. **Render reiniciará automáticamente** el servicio

7. **Espera 2-3 minutos** y revisa los logs

## ✅ Verificación

Después de hacer los cambios, en los logs deberías ver:

```
✅ Usando SUPABASE_URL (URL REST): https://eixvqedpyuybfywmdulg.supabase.co
✅ Cliente de Supabase inicializado con URL REST: https://eixvqedpyuybfywmdulg.supabase.co
✓ Iniciando servidor en puerto...
```

**NO deberías ver:**
- ❌ `ValueError: 'db.eixvqedpyuybfywmdulg.supabase.co' does not appear to be an IPv4 or IPv6 address`
- ❌ `Error al parsear SUPABASE_DB_URL`

## 🔄 Si Aún No Funciona

1. **Verifica que no haya espacios** en los valores de las variables
2. **Verifica que `SUPABASE_URL` termine en `.supabase.co`** (no `.com`)
3. **Elimina `SUPABASE_DB_URL`** completamente si no la necesitas
4. **Haz un redeploy manual** en Render

---

**Última actualización:** 2025-01-27

